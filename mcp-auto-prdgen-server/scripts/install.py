#!/usr/bin/env python3
"""
Installation script for Auto-PRDGen MCP Server
Automatically sets up the MCP server configuration for various IDEs
"""

import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class MCPInstaller:
    """Installer for Auto-PRDGen MCP Server"""
    
    def __init__(self):
        self.system = platform.system()
        self.auto_prdgen_root = self._find_auto_prdgen_root()
        
    def _find_auto_prdgen_root(self) -> str:
        """Find the Auto-PRDGen root directory"""
        # Check current directory and parent directories
        current = Path.cwd()
        
        for path in [current] + list(current.parents):
            if (path / "prd_creator.py").exists():
                return str(path.absolute())
        
        # If not found, ask user
        print("Auto-PRDGen root directory not found automatically.")
        while True:
            root = input("Please enter the path to your Auto-PRDGen directory: ").strip()
            root_path = Path(root).expanduser().absolute()
            
            if root_path.exists() and (root_path / "prd_creator.py").exists():
                return str(root_path)
            else:
                print(f"Invalid path: {root_path}. Please ensure it contains prd_creator.py")
    
    def get_claude_config_path(self) -> Optional[Path]:
        """Get Claude Desktop configuration path"""
        if self.system == "Darwin":  # macOS
            return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
        elif self.system == "Windows":
            return Path(os.environ.get("APPDATA", "")) / "Claude/claude_desktop_config.json"
        else:  # Linux
            return Path.home() / ".config/Claude/claude_desktop_config.json"
    
    def get_cursor_config_path(self) -> Optional[Path]:
        """Get Cursor configuration path"""
        if self.system == "Darwin":  # macOS
            return Path.home() / "Library/Application Support/Cursor/User/settings.json"
        elif self.system == "Windows":
            return Path(os.environ.get("APPDATA", "")) / "Cursor/User/settings.json"
        else:  # Linux
            return Path.home() / ".config/Cursor/User/settings.json"
    
    def create_mcp_config(self) -> Dict[str, Any]:
        """Create MCP server configuration"""
        return {
            "command": "conda",
            "args": ["run", "-n", "mcp-server", "python", "-m", "mcp_auto_prdgen_server.server"],
            "env": {
                "AUTO_PRDGEN_ROOT": self.auto_prdgen_root,
                "LOG_LEVEL": "INFO"
            }
        }
    
    def install_claude_desktop(self) -> bool:
        """Install MCP server for Claude Desktop"""
        config_path = self.get_claude_config_path()
        if not config_path:
            print("❌ Claude Desktop configuration path not found")
            return False
        
        try:
            # Create directory if it doesn't exist
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing config or create new
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Add MCP server
            if "mcpServers" not in config:
                config["mcpServers"] = {}
            
            config["mcpServers"]["auto-prdgen"] = self.create_mcp_config()
            
            # Save config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Claude Desktop configuration updated: {config_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error installing for Claude Desktop: {e}")
            return False
    
    def install_cursor(self) -> bool:
        """Install MCP server for Cursor"""
        config_path = self.get_cursor_config_path()
        if not config_path:
            print("❌ Cursor configuration path not found")
            return False
        
        try:
            # Create directory if it doesn't exist
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing config or create new
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Add MCP server
            if "mcp" not in config:
                config["mcp"] = {}
            if "servers" not in config["mcp"]:
                config["mcp"]["servers"] = {}
            
            # Cursor uses array format for command
            mcp_config = self.create_mcp_config()
            mcp_config["command"] = [mcp_config["command"]] + mcp_config["args"]
            del mcp_config["args"]
            
            config["mcp"]["servers"]["auto-prdgen"] = mcp_config
            
            # Save config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Cursor configuration updated: {config_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error installing for Cursor: {e}")
            return False
    
    def install_windsurf(self) -> bool:
        """Install MCP server for Windsurf"""
        # Windsurf configuration is similar to Cursor
        # Implementation would depend on specific Windsurf config format
        print("ℹ️  Windsurf installation not yet implemented")
        print("Please refer to the README for manual configuration")
        return False
    
    def verify_installation(self) -> bool:
        """Verify the MCP server installation"""
        try:
            # Try to import the server module
            import mcp_auto_prdgen_server.server
            print("✅ MCP server module can be imported")
            
            # Check if Auto-PRDGen is accessible
            auto_prdgen_path = Path(self.auto_prdgen_root)
            if (auto_prdgen_path / "prd_creator.py").exists():
                print("✅ Auto-PRDGen found and accessible")
                return True
            else:
                print("❌ Auto-PRDGen not found at specified path")
                return False
                
        except ImportError as e:
            print(f"❌ Cannot import MCP server module: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install required dependencies"""
        try:
            import subprocess
            
            # First, create a clean conda environment
            print("🔧 Creating conda environment 'mcp-server'...")
            result = subprocess.run([
                "conda", "create", "-n", "mcp-server", "python=3.11", "-y"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Failed to create conda environment: {result.stderr}")
                return False
            
            print("✅ Conda environment 'mcp-server' created")
            
            # Install the MCP server package in the new environment
            print("📦 Installing MCP Auto-PRDGen Server...")
            result = subprocess.run([
                "conda", "run", "-n", "mcp-server", "pip", "install", "-e", "."
            ], cwd=Path(__file__).parent.parent, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully in mcp-server environment")
                return True
            else:
                print(f"❌ Error installing dependencies: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def run_interactive_install(self):
        """Run interactive installation"""
        print("🚀 Auto-PRDGen MCP Server Installer")
        print("=" * 50)
        print(f"Auto-PRDGen Root: {self.auto_prdgen_root}")
        print(f"System: {self.system}")
        print()
        
        # Install dependencies
        if not self.install_dependencies():
            print("Installation failed. Please install dependencies manually.")
            return
        
        # Choose installation targets
        print("Select installation targets:")
        print("1. Claude Desktop")
        print("2. Cursor IDE")
        print("3. Windsurf (manual setup required)")
        print("4. All supported")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        success = False
        
        if choice in ["1", "4"]:
            success |= self.install_claude_desktop()
        
        if choice in ["2", "4"]:
            success |= self.install_cursor()
        
        if choice in ["3", "4"]:
            success |= self.install_windsurf()
        
        print("\n" + "=" * 50)
        
        if success:
            print("🎉 Installation completed!")
            
            # Verify installation
            if self.verify_installation():
                print("\n✅ Installation verified successfully!")
                print("\nNext steps:")
                print("1. Restart your IDE/application")
                print("2. Look for Auto-PRDGen tools in your MCP-compatible client")
                print("3. Try commands like 'List project structure' or 'Create a new PRD'")
            else:
                print("\n⚠️  Installation verification failed. Please check the configuration manually.")
        else:
            print("❌ Installation failed. Please check the error messages above.")
    
    def create_config_files(self):
        """Create example configuration files"""
        configs = {
            "claude_desktop_config.json": {
                "mcpServers": {
                    "auto-prdgen": self.create_mcp_config()
                }
            },
            "cursor_config.json": {
                "mcp": {
                    "servers": {
                        "auto-prdgen": {
                            "command": ["conda", "run", "-n", "mcp-server", "python", "-m", "mcp_auto_prdgen_server.server"],
                            "env": {
                                "AUTO_PRDGEN_ROOT": self.auto_prdgen_root,
                                "LOG_LEVEL": "INFO"
                            }
                        }
                    }
                }
            }
        }
        
        for filename, config in configs.items():
            config_path = Path(__file__).parent.parent / filename
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"📄 Created example config: {config_path}")


def main():
    """Main installation function"""
    installer = MCPInstaller()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "verify":
            installer.verify_installation()
        elif command == "create-configs":
            installer.create_config_files()
        elif command == "claude":
            installer.install_claude_desktop()
        elif command == "cursor":
            installer.install_cursor()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: verify, create-configs, claude, cursor")
    else:
        installer.run_interactive_install()


if __name__ == "__main__":
    main() 