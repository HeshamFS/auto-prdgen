# Auto-PRDGen MCP Server

An MCP (Model Context Protocol) server that allows any LLM to natively access and run commands from your auto-prdgen codebase. This enables seamless integration between AI assistants and your Product Requirements Document creation workflow.

## ⚠️ Important: Environment Setup

This MCP server **requires** a clean conda environment to avoid dependency conflicts. The installation automatically creates a `mcp-server` environment to ensure proper operation.

### Quick Start

1. **Run the installer** (automatically creates conda environment):
   ```bash
   cd mcp-auto-prdgen-server
   python scripts/install.py
   ```

2. **Or manually install**:
   ```bash
   # Create and activate environment
   conda create -n mcp-server python=3.11 -y
   conda activate mcp-server
   
   # Install the package
   pip install -e .
   ```

3. **Start the server**:
   ```bash
   # Use the provided startup scripts
   ./start_server.bat       # Windows Command Prompt
   ./start_server.ps1       # Windows PowerShell
   
   # Or manually
   conda activate mcp-server
   python -m mcp_auto_prdgen_server.server
   ```

## Features

### 🛠️ Tools (15+ available)
- **PRD Management**: Create, update, validate, and analyze PRDs
- **Task Management**: Initialize, research, update, and navigate tasks  
- **Project Management**: Check status, view structure, manage metadata
- **Natural Language**: Execute commands through conversational interface

### 📂 Resources
- Access PRD documents, task definitions, and project metadata
- Secure file system resource management
- Real-time project file access

### 📝 Prompts
- Guided project creation workflows
- Development plan generation templates
- Best practice recommendations

## Configuration

### Claude Desktop
Add to your Claude Desktop configuration file (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "auto-prdgen": {
      "command": "C:\\Users\\[YOUR_USERNAME]\\Miniconda3\\envs\\mcp-server\\python.exe",
      "args": ["-m", "mcp_auto_prdgen_server.server"],
      "env": {
        "AUTO_PRDGEN_ROOT": "D:/auto-prdgen",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Cursor IDE
Add to your Cursor MCP configuration file (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "auto-prdgen": {
      "command": "C:\\Users\\[YOUR_USERNAME]\\Miniconda3\\envs\\mcp-server\\python.exe",
      "args": ["-m", "mcp_auto_prdgen_server.server"],
      "env": {
        "AUTO_PRDGEN_ROOT": "D:/auto-prdgen",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Windsurf IDE
Add to your Windsurf MCP configuration:

```json
{
  "mcpServers": {
    "auto-prdgen": {
      "command": "C:\\Users\\[YOUR_USERNAME]\\Miniconda3\\envs\\mcp-server\\python.exe",
      "args": ["-m", "mcp_auto_prdgen_server.server"],
      "env": {
        "AUTO_PRDGEN_ROOT": "D:/auto-prdgen",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Important Configuration Notes:**
- Replace `[YOUR_USERNAME]` with your actual Windows username
- Update `AUTO_PRDGEN_ROOT` to point to your auto-prdgen installation directory
- Use forward slashes (`/`) or double backslashes (`\\`) in paths
- Ensure the Python executable path matches your conda environment location

## Usage Examples

Once configured, you can use natural language with your LLM client:

- "Create a new PRD for a mobile app"
- "Show me the current project structure"
- "What tasks are pending for this project?"
- "Update the PRD with new requirements"
- "Generate a development plan"

## Troubleshooting

### Common Issues

1. **"No module named 'pydantic'" error**:
   - Ensure you're using the `mcp-server` conda environment
   - Run: `conda activate mcp-server`
   - Use the provided startup scripts

2. **Server won't start**:
   - Check that the conda environment exists: `conda env list`
   - Recreate if needed: `conda create -n mcp-server python=3.11 -y`
   - Reinstall: `conda activate mcp-server && pip install -e .`

3. **Can't find auto-prdgen**:
   - Update `AUTO_PRDGEN_ROOT` in your MCP configuration
   - Ensure it points to the directory containing `prd_creator.py`

4. **Python executable path issues**:
   - Find your conda environment path: `conda info --envs`
   - Update the `command` path in your MCP configuration
   - Common paths:
     - Windows: `C:\Users\[USERNAME]\Miniconda3\envs\mcp-server\python.exe`
     - Windows (Anaconda): `C:\Users\[USERNAME]\Anaconda3\envs\mcp-server\python.exe`

### Environment Verification

Test your installation:
```bash
conda activate mcp-server
python -c "import mcp_auto_prdgen_server.server; print('✅ Server ready')"
```

Find your Python executable path:
```bash
conda activate mcp-server
python -c "import sys; print(sys.executable)"
```

## Architecture

```
AI Assistant ↔ MCP Server ↔ Auto-PRDGen CLI ↔ Project Files
```

The MCP server acts as a bridge between any MCP-compatible AI client and your auto-prdgen installation, providing seamless access to all PRD and project management functionality.

## Development

### Project Structure
```
mcp-auto-prdgen-server/
├── src/mcp_auto_prdgen_server/
│   ├── server.py          # Main MCP server
│   └── client.py          # Test client
├── scripts/
│   └── install.py         # Installation script
├── start_server.bat       # Windows batch launcher
├── start_server.ps1       # PowerShell launcher
└── README.md
```

### Testing
```bash
conda activate mcp-server
python -m mcp_auto_prdgen_server.client
```

## License

This project follows the same license as the auto-prdgen codebase.

## Related Projects

- [Auto-PRDGen](https://github.com/HeshamFS/auto-prdgen) - The original CLI tool
- [Model Context Protocol](https://github.com/modelcontextprotocol) - Official MCP specification and tools

## Support

For issues and support:
1. Check the [troubleshooting section](#troubleshooting)
2. Search existing issues
3. Create a new issue with detailed information
4. Join the community discussions

