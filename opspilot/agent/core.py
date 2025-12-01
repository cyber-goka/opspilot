"""
OpsPilot Agent Core

Implements the Think-Act loop with Plan/Build mode switching.
Manages AI interactions and tool orchestration.
"""

import json
from typing import List, Dict, Any, Optional, Literal, Callable
from dataclasses import dataclass
from enum import Enum

try:
    from litellm import acompletion, completion, completion_cost
except ImportError:
    # Fallback for development
    class MockMessage:
        def __init__(self) -> None:
            self.content = "Mock response - litellm not installed"
            self.tool_calls = None

    class MockChoice:
        @property
        def message(self) -> MockMessage:
            return MockMessage()

    class MockResponse:
        @property
        def choices(self) -> List[MockChoice]:
            return [MockChoice()]

    async def acompletion(*args: Any, **kwargs: Any) -> MockResponse:
        return MockResponse()

    def sync_completion(*args: Any, **kwargs: Any) -> MockResponse:
        return MockResponse()

    def completion(*args: Any, **kwargs: Any) -> Any:
        class MockResponse:
            def choice(self) -> Dict[str, Any]:
                return {"message": {"content": "Mock response - litellm not installed"}}

        return MockResponse()

    def completion_cost(*args: Any, **kwargs: Any) -> float:
        return 0.0


from ..config import config_manager


class AgentMode(Enum):
    """Agent operation modes."""

    PLAN = "plan"
    BUILD = "build"


@dataclass
class Tool:
    """Represents an available tool for the agent."""

    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    requires_build_mode: bool = False


@dataclass
class Message:
    """Represents a chat message."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class AgentCore:
    """Core agent logic implementing Think-Act loop."""

    def __init__(self, launch_config: Any = None) -> None:
        self.config = config_manager.load_config()
        self.launch_config = launch_config  # TUI launch config with API keys
        self.mode = AgentMode.PLAN
        self.tools: Dict[str, Tool] = {}
        self.messages: List[Message] = []
        self.usage_stats = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "requests_count": 0,
            "current_context_tokens": 0,
        }
        self._setup_default_tools()

    def _setup_default_tools(self) -> None:
        """Setup default tools based on available modules."""
        # These will be populated when tools are imported
        pass

    def _track_usage(self, response: Any) -> None:
        """Track usage statistics from litellm response."""
        try:
            # Extract usage information
            usage = getattr(response, "usage", None)
            if usage:
                # Get token counts
                prompt_tokens = getattr(usage, "prompt_tokens", 0)
                completion_tokens = getattr(usage, "completion_tokens", 0)
                total_tokens = getattr(usage, "total_tokens", 0)

                # Update statistics
                self.usage_stats["total_tokens"] += total_tokens
                self.usage_stats["requests_count"] += 1

                # Calculate cost using LiteLLM's built-in pricing
                cost = completion_cost(completion_response=response)
                self.usage_stats["total_cost"] += cost

                # Update current context tokens (approximate)
                self.usage_stats["current_context_tokens"] = prompt_tokens

        except Exception:
            # Don't fail if usage tracking fails
            pass

    def register_tool(self, tool: Any) -> None:
        """Register a new tool with the agent."""
        if isinstance(tool, dict):
            tool_obj = Tool(**tool)
        else:
            tool_obj = tool
        self.tools[tool_obj.name] = tool_obj

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools based on current mode."""
        available_tools = []

        for tool in self.tools.values():
            if tool.requires_build_mode and self.mode == AgentMode.PLAN:
                continue

            available_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
            )

        return available_tools

    def switch_mode(self, mode: AgentMode) -> None:
        """Switch between Plan and Build modes."""
        self.mode = mode

    def add_message(
        self,
        role: Literal["user", "assistant", "system", "tool"],
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
    ) -> None:
        """Add a message to the conversation history."""
        message = Message(
            role=role, content=content, tool_calls=tool_calls, tool_call_id=tool_call_id
        )
        self.messages.append(message)

    async def think(self, user_input: str, selected_model: Any = None) -> str:
        """Process user input and generate a response (Think phase)."""
        # Add user message to history
        self.add_message("user", user_input)

        # Get system prompt based on mode
        system_prompt = self._get_system_prompt()

        # Prepare messages for AI
        messages = [
            {"role": "system", "content": system_prompt},
            *[{"role": msg.role, "content": msg.content} for msg in self.messages],
        ]

        # Get available tools
        tools = self.get_available_tools()

        # Determine model to use
        if selected_model:
            model_name = selected_model.name
            provider = selected_model.provider
        else:
            model_name = config_manager.get_model_for_mode(self.mode.value)
            provider = None

        # Get API key for the provider if using TUI config
        litellm_kwargs = config_manager.get_litellm_config()
        if self.launch_config and provider:
            api_key = self.launch_config.get_api_key_for_provider(provider)
            if api_key:
                litellm_kwargs["api_key"] = api_key

        try:
            # Call AI model
            response = await acompletion(
                model=model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                **litellm_kwargs,
            )

            # Extract response content
            assistant_message = response.choices[0].message

            # Track usage statistics
            self._track_usage(response)

            # Add assistant response to history
            self.add_message(
                "assistant",
                assistant_message.content or "",
                assistant_message.tool_calls,
            )

            return assistant_message.content or ""

        except Exception as e:
            error_msg = f"AI Error: {str(e)}"
            self.add_message("assistant", error_msg)
            return error_msg

    async def act(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tool calls (Act phase)."""
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            tool_call_id = tool_call.get("id", "unknown")

            try:
                # Execute tool
                tool = self.tools[tool_name]
                result = await tool.function(**tool_args)

                # Add tool result message
                self.add_message("tool", str(result), tool_call_id=tool_call_id)

                results.append({"tool_call_id": tool_call_id, "result": str(result)})

            except Exception as e:
                error_result = f"Tool Error: {str(e)}"

                self.add_message("tool", error_result, tool_call_id=tool_call_id)

                results.append({"tool_call_id": tool_call_id, "result": error_result})

        return results

    async def process(self, user_input: str, selected_model: Any = None) -> str:
        """Main Think-Act loop processing."""
        # Think phase
        response = await self.think(user_input, selected_model=selected_model)

        # Check if there are tool calls to execute
        last_message = self.messages[-1] if self.messages else None
        if last_message and last_message.tool_calls:
            # Act phase
            await self.act(last_message.tool_calls)

            # Think again with tool results
            response = await self.think("", selected_model=selected_model)  # Empty input to continue conversation

        return response

    def _get_system_prompt(self) -> str:
        """Get system prompt based on current mode."""
        if self.mode == AgentMode.PLAN:
            return """You are OpsPilot, an expert DevOps/SRE engineer assistant in PLAN MODE.

IDENTITY & EXPERTISE:
You are a seasoned DevOps engineer with deep expertise in:
- Infrastructure automation (Terraform, Ansible, CloudFormation, Pulumi)
- Container orchestration (Kubernetes, Docker, ECS, Docker Swarm)
- CI/CD pipelines (Jenkins, GitLab CI, GitHub Actions, ArgoCD, Flux)
- Cloud platforms (AWS, Azure, GCP, DigitalOcean)
- Monitoring & observability (Prometheus, Grafana, ELK, Datadog, New Relic)
- Configuration management & GitOps practices
- Security best practices, compliance, and hardening
- High availability, disaster recovery, and incident response
- Performance optimization and cost management

PLAN MODE CAPABILITIES:
- Read and analyze configuration files, logs, and infrastructure code
- Review system architecture and deployment patterns
- Assess security vulnerabilities and compliance issues
- Analyze resource utilization and cost optimization opportunities
- Research best practices and industry standards

PLAN MODE RESTRICTIONS:
- You CANNOT execute commands or make changes to systems
- You CANNOT write files or modify configurations
- You CAN only read, analyze, and plan

YOUR PLANNING APPROACH:
When creating plans, always include:

1. SITUATION ANALYSIS
   - Current state assessment
   - Problem/requirement identification
   - Root cause analysis (for issues)
   - Resource inventory

2. SOLUTION DESIGN
   - Recommended approach with technical justification
   - Alternative solutions with pros/cons
   - Architecture diagrams (as ASCII art if needed)
   - Technology stack recommendations

3. IMPLEMENTATION PLAN
   - Step-by-step execution sequence
   - Commands/scripts to run (with explanations)
   - Configuration changes needed
   - Rollback procedures

4. RISK ASSESSMENT
   - Potential issues and failure points
   - Impact analysis (downtime, data loss, etc.)
   - Mitigation strategies
   - Compliance and security considerations

5. VALIDATION & TESTING
   - Success criteria
   - Testing procedures
   - Monitoring and alerting setup
   - Post-deployment verification

6. DOCUMENTATION & HANDOFF
   - Required prerequisites
   - Dependencies and assumptions
   - Estimated time and resource requirements
   - Operational runbook updates needed

COMMUNICATION STYLE:
- Be concise but thorough - use bullet points and structured formats
- Explain the "why" behind recommendations, not just the "what"
- Call out critical steps, security concerns, and potential gotchas
- Use industry-standard terminology but explain complex concepts
- Provide real-world examples and proven patterns

When your plan is ready, inform the user they can switch to BUILD MODE to execute it."""

        else:  # BUILD MODE
            return """You are OpsPilot, an expert DevOps/SRE engineer assistant in BUILD MODE.

IDENTITY & EXPERTISE:
You are a seasoned DevOps engineer with deep expertise in:
- Infrastructure automation (Terraform, Ansible, CloudFormation, Pulumi)
- Container orchestration (Kubernetes, Docker, ECS, Docker Swarm)
- CI/CD pipelines (Jenkins, GitLab CI, GitHub Actions, ArgoCD, Flux)
- Cloud platforms (AWS, Azure, GCP, DigitalOcean)
- Monitoring & observability (Prometheus, Grafana, ELK, Datadog, New Relic)
- Configuration management & GitOps practices
- Security best practices, compliance, and hardening
- High availability, disaster recovery, and incident response
- Performance optimization and cost management
- Scripting (Bash, Python, Go) and automation

BUILD MODE CAPABILITIES:
- Execute shell commands and scripts
- Create, modify, and delete files
- Configure services and applications
- Deploy infrastructure and applications
- Troubleshoot and resolve issues
- Implement monitoring and automation
- Full system access for DevOps operations

OPERATIONAL APPROACH:
Follow this workflow for every task:

1. BEFORE ACTION
   - Briefly state what you're about to do and why
   - Check prerequisites and dependencies
   - For risky operations: backup, dry-run, or seek confirmation
   - Verify you have necessary permissions/credentials

2. DURING EXECUTION
   - Run commands with appropriate error handling
   - Use idempotent operations where possible
   - Log outputs for troubleshooting
   - Handle errors gracefully and explain issues

3. AFTER ACTION
   - Verify the operation succeeded
   - Check service health and functionality
   - Report results clearly (success/failure/partial)
   - Document any changes made

SAFETY & BEST PRACTICES:
- ALWAYS backup before destructive operations
- Use --dry-run or -n flags when available
- Test in non-production first (mention this to user)
- Validate syntax before applying (terraform plan, kubectl diff, etc.)
- Check resource limits and quotas
- Follow principle of least privilege
- Never hardcode secrets - use environment variables or secret managers
- Implement proper logging and monitoring
- Use version control for infrastructure code
- Document everything you change

RISK AWARENESS:
HIGH RISK operations requiring extra caution:
- Database migrations and schema changes
- Production deployments during business hours
- Firewall/security group modifications
- DNS changes (propagation delays)
- Certificate renewals (potential service disruption)
- Scaling operations (cost implications)
- Data deletion or cleanup operations

TROUBLESHOOTING METHODOLOGY:
When debugging issues:
1. Gather information (logs, metrics, recent changes)
2. Form hypothesis based on symptoms
3. Test hypothesis systematically
4. Implement fix and verify
5. Document root cause and solution
6. Consider preventive measures

COMMUNICATION STYLE:
- Be direct and actionable
- Show command outputs when relevant
- Explain unexpected results or errors
- Provide context for decisions made
- Alert user to important warnings or considerations
- Use clear success/failure indicators

EFFICIENCY TIPS:
- Combine related commands when safe
- Use appropriate tools for the job
- Leverage existing configurations and patterns
- Automate repetitive tasks
- Think about long-term maintainability"""

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages = []

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation."""
        return {
            "mode": self.mode.value,
            "message_count": len(self.messages),
            "available_tools": len(self.get_available_tools()),
            "current_model": config_manager.get_model_for_mode(self.mode.value),
            "auth_mode": (
                "subscription" if config_manager.is_subscription_mode() else "byok"
            ),
            "usage_stats": self.usage_stats,
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return self.usage_stats.copy()

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self.usage_stats = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "requests_count": 0,
            "current_context_tokens": 0,
        }


# Global agent instance
agent_core = AgentCore()
