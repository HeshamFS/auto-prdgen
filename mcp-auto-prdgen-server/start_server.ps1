# PowerShell script to start MCP Auto-PRDGen Server
Write-Host "Starting MCP Auto-PRDGen Server..." -ForegroundColor Green
Write-Host ""

# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Check if conda is available
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "Error: conda is not found in PATH" -ForegroundColor Red
    Write-Host "Please ensure Anaconda/Miniconda is installed and available in PATH"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Activating conda environment 'mcp-server'..." -ForegroundColor Yellow
& conda activate mcp-server
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to activate conda environment 'mcp-server'" -ForegroundColor Red
    Write-Host "Please ensure the environment exists by running:" -ForegroundColor Yellow
    Write-Host "conda create -n mcp-server python=3.11 -y" -ForegroundColor Cyan
    Write-Host "pip install -e ." -ForegroundColor Cyan
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Starting MCP server..." -ForegroundColor Yellow
Write-Host "Server will be available for MCP clients to connect to." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Cyan
Write-Host ""

# Start the server
python -m mcp_auto_prdgen_server.server
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start MCP server" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
} 