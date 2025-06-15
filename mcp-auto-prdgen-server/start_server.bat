@echo off
echo Starting MCP Auto-PRDGen Server...
echo.
echo Activating conda environment...
call conda activate mcp-server
if %errorlevel% neq 0 (
    echo Failed to activate conda environment 'mcp-server'
    echo Please ensure the environment exists: conda create -n mcp-server python=3.11 -y
    pause
    exit /b 1
)

echo.
echo Starting MCP server...
cd /d "%~dp0"
python -m mcp_auto_prdgen_server.server
if %errorlevel% neq 0 (
    echo Failed to start MCP server
    pause
    exit /b 1
) 