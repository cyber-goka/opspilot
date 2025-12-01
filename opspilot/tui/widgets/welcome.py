"""Show a welcome box on the home page when the user has
no chat history.
"""

from rich.console import RenderableType
from textual.widgets import Static


class Welcome(Static):
    MESSAGE = """
To get started, type a message in the box at the top of the
screen and press [b u]Enter[/] to send it (or [b u]Shift+Enter[/] for multi-line).

Change the model by pressing [b u]ctrl+o[/].

Make sure you've set any required API keys first (e.g. [b]OPENAI_API_KEY[/])!

If you have any issues or feedback, please let me know [@click='open_issues'][b r]on GitHub[/][/]!

Finally, please consider starring the repo and sharing it with your friends and colleagues!

[@click='open_repo'][b r]https://github.com/cyber-goka/opspilot[/][/]
"""

    BORDER_TITLE = "Welcome to OpsPilot!"

    def render(self) -> RenderableType:
        return self.MESSAGE

    def _action_open_repo(self) -> None:
        import webbrowser

        webbrowser.open("https://github.com/cyber-goka/opspilot")

    def _action_open_issues(self) -> None:
        import webbrowser

        webbrowser.open("https://github.com/cyber-goka/opspilot/issues")
