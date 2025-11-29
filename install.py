#!/usr/bin/env python3
"""
OpsPilot Installation Script

Sets up OpsPilot as an installable Python package.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return None


def main():
    """Main installation function."""
    print("🚀 OpsPilot Installation Script")
    print("=" * 40)

    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required")
        sys.exit(1)

    print(f"✅ Python {sys.version.split()[0]} detected")

    # Install in development mode
    current_dir = Path.cwd()

    print(f"\n📦 Installing OpsPilot in development mode...")
    run_command(f'pip install -e "{current_dir}"', "Development installation")

    # Verify installation
    print("\n🔍 Verifying installation...")
    try:
        result = subprocess.run(
            "opspilot --help", shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✅ OpsPilot successfully installed!")
        else:
            print("❌ Installation verification failed")
    except Exception as e:
        print(f"❌ Could not verify installation: {e}")

    print("\n📋 Next steps:")
    print("1. Run: opspilot start")
    print("2. Configure: opspilot config --show")
    print("3. Get help: opspilot --help")

    print("\n🎉 Installation complete!")


if __name__ == "__main__":
    main()
