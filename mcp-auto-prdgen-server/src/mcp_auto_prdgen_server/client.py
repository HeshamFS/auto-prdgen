#!/usr/bin/env python3
"""
MCP Client for Auto-PRDGen Server
Demonstrates how to connect to and use the Auto-PRDGen MCP server
"""

import asyncio
import json
import logging
from typing import Any, Dict, List

import mcp.client.stdio
import mcp.types as types
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-auto-prdgen-client")

class AutoPRDGenMCPClient:
    """Client for interacting with Auto-PRDGen MCP Server"""
    
    def __init__(self, server_command: List[str]):
        self.server_params = StdioServerParameters(
            command=server_command[0],
            args=server_command[1:] if len(server_command) > 1 else []
        )
        self.session = None
    
    async def connect(self):
        """Connect to the MCP server"""
        logger.info("Connecting to Auto-PRDGen MCP Server...")
        
        # Create the client connection
        self.read, self.write = await stdio_client(self.server_params)
        self.session = ClientSession(self.read, self.write)
        
        # Initialize the session
        await self.session.initialize()
        logger.info("Connected successfully!")
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.session:
            await self.session.close()
        logger.info("Disconnected from server")
    
    async def list_tools(self) -> List[types.Tool]:
        """List available tools from the server"""
        tools = await self.session.list_tools()
        return tools.tools
    
    async def list_resources(self) -> List[types.Resource]:
        """List available resources from the server"""
        resources = await self.session.list_resources()
        return resources.resources
    
    async def list_prompts(self) -> List[types.Prompt]:
        """List available prompts from the server"""
        prompts = await self.session.list_prompts()
        return prompts.prompts
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the server"""
        logger.info(f"Calling tool: {tool_name} with args: {arguments}")
        result = await self.session.call_tool(tool_name, arguments)
        return result
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource from the server"""
        logger.info(f"Reading resource: {uri}")
        result = await self.session.read_resource(uri)
        return result.content
    
    async def get_prompt(self, prompt_name: str, arguments: Dict[str, Any]) -> types.GetPromptResult:
        """Get a prompt from the server"""
        logger.info(f"Getting prompt: {prompt_name} with args: {arguments}")
        result = await self.session.get_prompt(prompt_name, arguments)
        return result
    
    async def execute_prd_workflow(self, project_idea: str):
        """Execute a complete PRD creation workflow"""
        logger.info(f"Starting PRD workflow for: {project_idea}")
        
        try:
            # 1. Get the creation prompt
            prompt_result = await self.get_prompt("create_new_project", {
                "project_idea": project_idea,
                "complexity": "medium"
            })
            
            print(f"\n📋 Workflow Guide:\n{prompt_result.messages[0].content.text}\n")
            
            # 2. Initialize PRD
            prd_result = await self.call_tool("auto_prdgen_prd_init", {})
            print(f"📄 PRD Initialization:\n{prd_result.content[0].text}\n")
            
            # 3. List current project structure
            structure_result = await self.call_tool("list_project_structure", {})
            print(f"📁 Project Structure:\n{structure_result.content[0].text}\n")
            
            # 4. Get project status
            status_result = await self.call_tool("get_project_status", {})
            print(f"📊 Project Status:\n{status_result.content[0].text}\n")
            
        except Exception as e:
            logger.error(f"Error in PRD workflow: {e}")
            raise
    
    async def analyze_project(self, project_name: str):
        """Analyze an existing project"""
        logger.info(f"Analyzing project: {project_name}")
        
        try:
            # 1. Get analysis prompt
            prompt_result = await self.get_prompt("analyze_existing_project", {
                "project_name": project_name
            })
            
            print(f"\n🔍 Analysis Guide:\n{prompt_result.messages[0].content.text}\n")
            
            # 2. Get project structure
            structure_result = await self.call_tool("list_project_structure", {
                "project_name": project_name
            })
            print(f"📁 Project Structure:\n{structure_result.content[0].text}\n")
            
            # 3. Get project status
            status_result = await self.call_tool("get_project_status", {
                "project_name": project_name
            })
            print(f"📊 Project Status:\n{status_result.content[0].text}\n")
            
            # 4. Validate PRD if available
            validate_result = await self.call_tool("auto_prdgen_prd_validate", {})
            print(f"✅ PRD Validation:\n{validate_result.content[0].text}\n")
            
        except Exception as e:
            logger.error(f"Error analyzing project: {e}")
            raise
    
    async def demo_capabilities(self):
        """Demonstrate all server capabilities"""
        print("\n🚀 Auto-PRDGen MCP Server Demo\n")
        
        # List tools
        tools = await self.list_tools()
        print(f"🔧 Available Tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        print()
        
        # List resources
        resources = await self.list_resources()
        print(f"📚 Available Resources ({len(resources)}):")
        for resource in resources:
            print(f"  - {resource.name}: {resource.description}")
        print()
        
        # List prompts
        prompts = await self.list_prompts()
        print(f"💡 Available Prompts ({len(prompts)}):")
        for prompt in prompts:
            print(f"  - {prompt.name}: {prompt.description}")
        print()
        
        # Demonstrate project structure listing
        print("📁 Demonstrating project structure listing:")
        structure_result = await self.call_tool("list_project_structure", {})
        print(structure_result.content[0].text)

async def main():
    """Main client demonstration"""
    # Server command (adjust path as needed)
    server_command = ["python", "-m", "mcp_auto_prdgen_server.server"]
    
    client = AutoPRDGenMCPClient(server_command)
    
    try:
        # Connect to server
        await client.connect()
        
        # Demonstrate capabilities
        await client.demo_capabilities()
        
        # Example workflow - create a new project
        print("\n" + "="*60)
        print("🎯 Example: Creating a new project")
        print("="*60)
        await client.execute_prd_workflow("AI-powered task management app")
        
        # Example workflow - analyze existing project
        print("\n" + "="*60)
        print("🔍 Example: Analyzing existing projects")
        print("="*60)
        await client.analyze_project("")  # Analyze all projects
        
    except Exception as e:
        logger.error(f"Client error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 