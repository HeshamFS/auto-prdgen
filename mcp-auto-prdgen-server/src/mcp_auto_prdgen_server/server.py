#!/usr/bin/env python3
"""
MCP Server for Auto-PRDGen
Exposes auto-prdgen functionality as MCP tools for AI assistants
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-auto-prdgen-server")

# Server instance
server = Server("auto-prdgen-server")

# Auto-PRDGen commands mapping
COMMANDS = {
    "prd-init": "Generate a new PRD document",
    "prd-update": "Update an existing PRD document", 
    "prd-compare": "Compare different versions of PRD documents",
    "prd-validate": "Validate PRD quality and completeness",
    "prd-complexity": "Analyze PRD complexity and provide insights",
    "task-init": "Generate tasks from PRD with specified detail level",
    "task-research": "Generate research-backed tasks from PRD",
    "task-update": "Update task status and details",
    "task-view": "Display tasks with filtering options",
    "task-next": "Find the next available task to work on",
    "task-expand": "Break down complex tasks into subtasks",
    "task-deps": "Manage task dependencies",
    "task-complexity": "Analyze task complexity",
    "task-export": "Export tasks to various formats",
    "nl-command": "Execute natural language commands"
}

# Auto-PRDGen project root path
AUTO_PRDGEN_ROOT = Path(__file__).parent.parent.parent.parent.absolute()

@server.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """List available resources from auto-prdgen"""
    resources = []
    
    # Output directory resources
    output_dir = AUTO_PRDGEN_ROOT / "output"
    if output_dir.exists():
        for project_dir in output_dir.iterdir():
            if project_dir.is_dir():
                resources.append(
                    types.Resource(
                        uri=f"file://{project_dir.absolute()}",
                        name=f"Project: {project_dir.name}",
                        description=f"Auto-PRDGen project directory: {project_dir.name}",
                        mimeType="application/json"
                    )
                )
                
                # Add PRD files
                for prd_file in project_dir.glob("*.md"):
                    resources.append(
                        types.Resource(
                            uri=f"file://{prd_file.absolute()}",
                            name=f"PRD: {prd_file.stem}",
                            description=f"Product Requirements Document: {prd_file.name}",
                            mimeType="text/markdown"
                        )
                    )
                
                # Add task files
                for task_file in project_dir.glob("tasks/*.json"):
                    resources.append(
                        types.Resource(
                            uri=f"file://{task_file.absolute()}",
                            name=f"Task: {task_file.stem}",
                            description=f"Task definition: {task_file.name}",
                            mimeType="application/json"
                        )
                    )
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a resource from auto-prdgen"""
    try:
        if uri.startswith("file://"):
            file_path = Path(uri[7:])  # Remove file:// prefix
            if file_path.exists() and file_path.is_file():
                return file_path.read_text(encoding='utf-8')
            else:
                raise FileNotFoundError(f"File not found: {file_path}")
        else:
            raise ValueError(f"Unsupported URI scheme: {uri}")
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        raise

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available auto-prdgen tools"""
    tools = []
    
    # Add all auto-prdgen commands as tools
    for command, description in COMMANDS.items():
        tools.append(
            types.Tool(
                name=f"auto_prdgen_{command.replace('-', '_')}",
                description=description,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": f"Arguments for {command} command",
                            "default": []
                        }
                    }
                }
            )
        )
    
    # Add specialized PRD creation tool
    tools.append(
        types.Tool(
            name="create_prd",
            description="Create a new Product Requirements Document (PRD) with specified parameters",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Project name/title"
                    },
                    "project_description": {
                        "type": "string", 
                        "description": "Detailed project description"
                    },
                    "complexity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Project complexity level",
                        "default": "medium"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"], 
                        "description": "Project priority level",
                        "default": "medium"
                    },
                    "num_questions": {
                        "type": "string",
                        "description": "Number of clarifying questions (e.g., '3' or '3-5')",
                        "default": "3"
                    }
                },
                "required": ["project_name", "project_description"]
            }
        )
    )

    # Add general command execution tool
    tools.append(
        types.Tool(
            name="execute_auto_prdgen_command",
            description="Execute any auto-prdgen command with custom arguments",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The auto-prdgen command to execute",
                        "enum": list(COMMANDS.keys())
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional arguments for the command",
                        "default": []
                    },
                    "working_directory": {
                        "type": "string",
                        "description": "Working directory to execute the command in",
                        "default": str(AUTO_PRDGEN_ROOT)
                    }
                },
                "required": ["command"]
            }
        )
    )
    
    # Add file system tools
    tools.append(
        types.Tool(
            name="list_project_structure",
            description="List the structure of auto-prdgen projects and output files",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Specific project name to explore (optional)",
                        "default": ""
                    }
                }
            }
        )
    )
    
    tools.append(
        types.Tool(
            name="get_project_status",
            description="Get comprehensive status of auto-prdgen projects including PRDs, tasks, and progress",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Specific project name to check (optional)",
                        "default": ""
                    }
                }
            }
        )
    )
    
    # Add specialized task management tools
    tools.append(
        types.Tool(
            name="create_tasks_from_prd",
            description="Generate development tasks from a PRD",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "level": {
                        "type": "string",
                        "enum": ["simple", "detailed"],
                        "description": "Task detail level: simple for high-level epics, detailed for granular tasks",
                        "default": "detailed"
                    }
                },
                "required": ["project_name"]
            }
        )
    )
    
    tools.append(
        types.Tool(
            name="update_task",
            description="Update a specific task's status, priority, or details",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "task_id": {
                        "type": "integer",
                        "description": "Task ID to update"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in-progress", "completed"],
                        "description": "New task status"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "New task priority"
                    },
                    "description": {
                        "type": "string",
                        "description": "New task description"
                    },
                    "details": {
                        "type": "string",
                        "description": "New task details"
                    }
                },
                "required": ["project_name", "task_id"]
            }
        )
    )
    
    tools.append(
        types.Tool(
            name="view_tasks",
            description="View tasks with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "filter": {
                        "type": "string",
                        "enum": ["all", "status", "priority", "pending", "completed"],
                        "description": "Filter type",
                        "default": "all"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in-progress", "completed"],
                        "description": "Status to filter by (use with filter='status')"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Priority to filter by (use with filter='priority')"
                    }
                },
                "required": ["project_name"]
            }
        )
    )
    
    tools.append(
        types.Tool(
            name="update_prd",
            description="Update an existing PRD with specified modifications",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "modification_request": {
                        "type": "string",
                        "description": "Description of changes to make to the PRD"
                    }
                },
                "required": ["project_name", "modification_request"]
            }
        )
    )
    
    tools.append(
        types.Tool(
            name="validate_prd",
            description="Validate PRD completeness and quality",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Project name"
                    }
                },
                "required": ["project_name"]
            }
        )
    )
    
    return tools

async def execute_auto_prdgen_command(command: str, args: List[str], working_dir: str = None) -> Dict[str, Any]:
    """Execute an auto-prdgen command and return the result"""
    if working_dir is None:
        working_dir = str(AUTO_PRDGEN_ROOT)
    
    try:
        # Build the command
        cmd = ["python", "-m", "prd_creator", command] + args
        
        # Execute the command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE
        )
        
        # For interactive commands, we might need to provide input
        stdout, stderr = await process.communicate()
        
        return {
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "stdout": stdout.decode('utf-8') if stdout else "",
            "stderr": stderr.decode('utf-8') if stderr else "",
            "command": " ".join(cmd)
        }
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": " ".join(cmd)
        }

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Handle tool calls"""
    try:
        if name.startswith("auto_prdgen_"):
            # Extract command from tool name
            command = name.replace("auto_prdgen_", "").replace("_", "-")
            args = arguments.get("args", [])
            
            result = await execute_auto_prdgen_command(command, args)
            
            if result["success"]:
                content = f"✅ Command executed successfully:\n\n"
                content += f"Command: {result['command']}\n\n"
                if result["stdout"]:
                    content += f"Output:\n{result['stdout']}\n"
            else:
                content = f"❌ Command failed:\n\n"
                content += f"Command: {result['command']}\n"
                content += f"Return code: {result['returncode']}\n\n"
                if result["stderr"]:
                    content += f"Error:\n{result['stderr']}\n"
                if "error" in result:
                    content += f"Exception: {result['error']}\n"
            
            return [types.TextContent(type="text", text=content)]
            
        elif name == "create_prd":
            # Handle specialized PRD creation
            project_name = arguments["project_name"]
            project_description = arguments["project_description"]
            complexity = arguments.get("complexity", "medium")
            priority = arguments.get("priority", "medium")
            num_questions = arguments.get("num_questions", "3")
            
            args = [
                "--project-name", project_name,
                "--project-description", project_description,
                "--complexity", complexity,
                "--priority", priority,
                "--num-questions", num_questions
            ]
            
            result = await execute_auto_prdgen_command("prd-init", args)
            
            if result["success"]:
                content = f"✅ PRD created successfully for '{project_name}':\n\n"
                content += f"Full command: {result['command']}\n\n"
                if result["stdout"]:
                    content += f"Output:\n{result['stdout']}\n"
            else:
                content = f"❌ PRD creation failed for '{project_name}':\n\n"
                content += f"Full command: {result['command']}\n"
                content += f"Return code: {result['returncode']}\n\n"
                if result["stderr"]:
                    content += f"Error:\n{result['stderr']}\n"
                if "error" in result:
                    content += f"Exception: {result['error']}\n"
            
            return [types.TextContent(type="text", text=content)]
            
        elif name == "create_tasks_from_prd":
            # Handle task creation from PRD
            project_name = arguments["project_name"]
            level = arguments.get("level", "detailed")
            
            args = ["--project-name", project_name, "--level", level]
            result = await execute_auto_prdgen_command("task-init", args)
            
            if result["success"]:
                content = f"✅ Tasks created successfully for '{project_name}':\n\n"
                content += f"Full command: {result['command']}\n\n"
                if result["stdout"]:
                    content += f"Output:\n{result['stdout']}\n"
            else:
                content = f"❌ Task creation failed for '{project_name}':\n\n"
                content += f"Full command: {result['command']}\n"
                content += f"Return code: {result['returncode']}\n\n"
                if result["stderr"]:
                    content += f"Error:\n{result['stderr']}\n"
                if "error" in result:
                    content += f"Exception: {result['error']}\n"
            
            return [types.TextContent(type="text", text=content)]
            
        elif name == "update_task":
            # Handle task updates
            project_name = arguments["project_name"]
            task_id = arguments["task_id"]
            
            args = ["--project-name", project_name, "--task-id", str(task_id)]
            
            if "status" in arguments:
                args.extend(["--status", arguments["status"]])
            if "priority" in arguments:
                args.extend(["--priority", arguments["priority"]])
            if "description" in arguments:
                args.extend(["--description", arguments["description"]])
            if "details" in arguments:
                args.extend(["--details", arguments["details"]])
            
            result = await execute_auto_prdgen_command("task-update", args)
            
            if result["success"]:
                content = f"✅ Task {task_id} updated successfully in '{project_name}':\n\n"
                content += f"Full command: {result['command']}\n\n"
                if result["stdout"]:
                    content += f"Output:\n{result['stdout']}\n"
            else:
                content = f"❌ Task update failed for task {task_id} in '{project_name}':\n\n"
                content += f"Full command: {result['command']}\n"
                content += f"Return code: {result['returncode']}\n\n"
                if result["stderr"]:
                    content += f"Error:\n{result['stderr']}\n"
                if "error" in result:
                    content += f"Exception: {result['error']}\n"
            
            return [types.TextContent(type="text", text=content)]
            
        elif name == "view_tasks":
            # Handle task viewing
            project_name = arguments["project_name"]
            filter_type = arguments.get("filter", "all")
            
            args = ["--project-name", project_name, "--filter", filter_type]
            
            if filter_type == "status" and "status" in arguments:
                args.extend(["--status", arguments["status"]])
            elif filter_type == "priority" and "priority" in arguments:
                args.extend(["--priority", arguments["priority"]])
            
            result = await execute_auto_prdgen_command("task-view", args)
            
            if result["success"]:
                content = f"✅ Tasks viewed successfully for '{project_name}':\n\n"
                content += f"Full command: {result['command']}\n\n"
                if result["stdout"]:
                    content += f"Output:\n{result['stdout']}\n"
            else:
                content = f"❌ Task viewing failed for '{project_name}':\n\n"
                content += f"Full command: {result['command']}\n"
                content += f"Return code: {result['returncode']}\n\n"
                if result["stderr"]:
                    content += f"Error:\n{result['stderr']}\n"
                if "error" in result:
                    content += f"Exception: {result['error']}\n"
            
            return [types.TextContent(type="text", text=content)]
            
        elif name == "update_prd":
            # Handle PRD updates
            project_name = arguments["project_name"]
            modification_request = arguments["modification_request"]
            
            args = ["--project-name", project_name, "--modification-request", modification_request]
            result = await execute_auto_prdgen_command("prd-update", args)
            
            if result["success"]:
                content = f"✅ PRD updated successfully for '{project_name}':\n\n"
                content += f"Full command: {result['command']}\n\n"
                if result["stdout"]:
                    content += f"Output:\n{result['stdout']}\n"
            else:
                content = f"❌ PRD update failed for '{project_name}':\n\n"
                content += f"Full command: {result['command']}\n"
                content += f"Return code: {result['returncode']}\n\n"
                if result["stderr"]:
                    content += f"Error:\n{result['stderr']}\n"
                if "error" in result:
                    content += f"Exception: {result['error']}\n"
            
            return [types.TextContent(type="text", text=content)]
            
        elif name == "validate_prd":
            # Handle PRD validation
            project_name = arguments["project_name"]
            
            args = ["--project-name", project_name]
            result = await execute_auto_prdgen_command("prd-validate", args)
            
            if result["success"]:
                content = f"✅ PRD validated successfully for '{project_name}':\n\n"
                content += f"Full command: {result['command']}\n\n"
                if result["stdout"]:
                    content += f"Output:\n{result['stdout']}\n"
            else:
                content = f"❌ PRD validation failed for '{project_name}':\n\n"
                content += f"Full command: {result['command']}\n"
                content += f"Return code: {result['returncode']}\n\n"
                if result["stderr"]:
                    content += f"Error:\n{result['stderr']}\n"
                if "error" in result:
                    content += f"Exception: {result['error']}\n"
            
            return [types.TextContent(type="text", text=content)]
            
        elif name == "execute_auto_prdgen_command":
            command = arguments["command"]
            args = arguments.get("args", [])
            working_dir = arguments.get("working_directory", str(AUTO_PRDGEN_ROOT))
            
            result = await execute_auto_prdgen_command(command, args, working_dir)
            
            if result["success"]:
                content = f"✅ Command '{command}' executed successfully:\n\n"
                content += f"Full command: {result['command']}\n\n"
                if result["stdout"]:
                    content += f"Output:\n{result['stdout']}\n"
            else:
                content = f"❌ Command '{command}' failed:\n\n"
                content += f"Full command: {result['command']}\n"
                content += f"Return code: {result['returncode']}\n\n"
                if result["stderr"]:
                    content += f"Error:\n{result['stderr']}\n"
                if "error" in result:
                    content += f"Exception: {result['error']}\n"
            
            return [types.TextContent(type="text", text=content)]
            
        elif name == "list_project_structure":
            project_name = arguments.get("project_name", "")
            output_dir = AUTO_PRDGEN_ROOT / "output"
            
            structure = {"projects": [], "total_projects": 0}
            
            if output_dir.exists():
                for project_dir in output_dir.iterdir():
                    if project_dir.is_dir():
                        if project_name and project_name.lower() not in project_dir.name.lower():
                            continue
                            
                        project_info = {
                            "name": project_dir.name,
                            "path": str(project_dir),
                            "prd_files": [],
                            "task_files": [],
                            "other_files": []
                        }
                        
                        # List PRD files
                        for prd_file in project_dir.glob("*.md"):
                            project_info["prd_files"].append(prd_file.name)
                        
                        # List task files
                        tasks_dir = project_dir / "tasks"
                        if tasks_dir.exists():
                            for task_file in tasks_dir.glob("*.json"):
                                project_info["task_files"].append(task_file.name)
                        
                        # List other files
                        for other_file in project_dir.iterdir():
                            if other_file.is_file() and not other_file.name.endswith('.md'):
                                project_info["other_files"].append(other_file.name)
                        
                        structure["projects"].append(project_info)
                
                structure["total_projects"] = len(structure["projects"])
            
            content = f"📁 Auto-PRDGen Project Structure\n\n"
            content += f"Total projects: {structure['total_projects']}\n\n"
            
            for project in structure["projects"]:
                content += f"## Project: {project['name']}\n"
                content += f"Path: {project['path']}\n\n"
                
                if project["prd_files"]:
                    content += f"📄 PRD Files ({len(project['prd_files'])}):\n"
                    for prd in project["prd_files"]:
                        content += f"  - {prd}\n"
                    content += "\n"
                
                if project["task_files"]:
                    content += f"📋 Task Files ({len(project['task_files'])}):\n"
                    for task in project["task_files"]:
                        content += f"  - {task}\n"
                    content += "\n"
                
                if project["other_files"]:
                    content += f"📁 Other Files ({len(project['other_files'])}):\n"
                    for other in project["other_files"]:
                        content += f"  - {other}\n"
                    content += "\n"
                
                content += "---\n\n"
            
            return [types.TextContent(type="text", text=content)]
            
        elif name == "get_project_status":
            project_name = arguments.get("project_name", "")
            output_dir = AUTO_PRDGEN_ROOT / "output"
            
            status = {"projects": [], "summary": {}}
            total_prds = 0
            total_tasks = 0
            
            if output_dir.exists():
                for project_dir in output_dir.iterdir():
                    if project_dir.is_dir():
                        if project_name and project_name.lower() not in project_dir.name.lower():
                            continue
                        
                        project_status = {
                            "name": project_dir.name,
                            "path": str(project_dir),
                            "prd_count": 0,
                            "task_count": 0,
                            "latest_prd": None,
                            "task_summary": {"pending": 0, "in_progress": 0, "completed": 0}
                        }
                        
                        # Count PRD files and find latest
                        prd_files = list(project_dir.glob("*.md"))
                        project_status["prd_count"] = len(prd_files)
                        total_prds += len(prd_files)
                        
                        if prd_files:
                            latest_prd = max(prd_files, key=lambda f: f.stat().st_mtime)
                            project_status["latest_prd"] = latest_prd.name
                        
                        # Count and analyze tasks
                        tasks_dir = project_dir / "tasks"
                        if tasks_dir.exists():
                            task_files = list(tasks_dir.glob("*.json"))
                            project_status["task_count"] = len(task_files)
                            total_tasks += len(task_files)
                            
                            # Analyze task statuses (if possible)
                            for task_file in task_files:
                                try:
                                    with open(task_file, 'r', encoding='utf-8') as f:
                                        task_data = json.load(f)
                                        status_key = task_data.get("status", "pending").lower()
                                        if status_key in project_status["task_summary"]:
                                            project_status["task_summary"][status_key] += 1
                                        else:
                                            project_status["task_summary"]["pending"] += 1
                                except Exception:
                                    project_status["task_summary"]["pending"] += 1
                        
                        status["projects"].append(project_status)
            
            status["summary"] = {
                "total_projects": len(status["projects"]),
                "total_prds": total_prds,
                "total_tasks": total_tasks
            }
            
            content = f"📊 Auto-PRDGen Project Status\n\n"
            content += f"📈 Summary:\n"
            content += f"  - Total Projects: {status['summary']['total_projects']}\n"
            content += f"  - Total PRDs: {status['summary']['total_prds']}\n"
            content += f"  - Total Tasks: {status['summary']['total_tasks']}\n\n"
            
            for project in status["projects"]:
                content += f"## 📁 {project['name']}\n"
                content += f"  - PRDs: {project['prd_count']}\n"
                content += f"  - Tasks: {project['task_count']}\n"
                
                if project["latest_prd"]:
                    content += f"  - Latest PRD: {project['latest_prd']}\n"
                
                task_summary = project["task_summary"]
                if project["task_count"] > 0:
                    content += f"  - Task Status:\n"
                    content += f"    • Pending: {task_summary['pending']}\n"
                    content += f"    • In Progress: {task_summary['in_progress']}\n"
                    content += f"    • Completed: {task_summary['completed']}\n"
                
                content += "\n"
            
            return [types.TextContent(type="text", text=content)]
        
        else:
            return [types.TextContent(
                type="text", 
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [types.TextContent(
            type="text", 
            text=f"Error executing tool {name}: {str(e)}"
        )]

@server.list_prompts()
async def handle_list_prompts() -> List[types.Prompt]:
    """List available prompts for auto-prdgen workflows"""
    return [
        types.Prompt(
            name="create_new_project",
            description="Guide through creating a new PRD project from scratch",
            arguments=[
                types.PromptArgument(
                    name="project_idea",
                    description="Brief description of the project idea",
                    required=True
                ),
                types.PromptArgument(
                    name="complexity",
                    description="Project complexity level (simple, medium, complex)",
                    required=False
                )
            ]
        ),
        types.Prompt(
            name="analyze_existing_project",
            description="Analyze and provide insights on an existing project",
            arguments=[
                types.PromptArgument(
                    name="project_name",
                    description="Name of the existing project to analyze",
                    required=True
                )
            ]
        ),
        types.Prompt(
            name="generate_development_plan",
            description="Generate a comprehensive development plan from PRD and tasks",
            arguments=[
                types.PromptArgument(
                    name="project_name",
                    description="Project name to generate plan for",
                    required=True
                ),
                types.PromptArgument(
                    name="timeline",
                    description="Target timeline for development (e.g., '3 months', '6 weeks')",
                    required=False
                )
            ]
        )
    ]

@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
    """Handle prompt requests"""
    if name == "create_new_project":
        project_idea = arguments.get("project_idea", "")
        complexity = arguments.get("complexity", "medium")
        
        prompt_text = f"""You are an expert product manager helping to create a new project using Auto-PRDGen.

Project Idea: {project_idea}
Complexity Level: {complexity}

Please follow these steps to create a comprehensive PRD:

1. **Initialize the PRD**: Use the `auto_prdgen_prd_init` tool to start the PRD creation process
2. **Gather Requirements**: Ask clarifying questions about:
   - Target audience and users
   - Core features and functionality
   - Technical requirements and constraints
   - Business objectives and success metrics
   - Timeline and resource constraints

3. **Generate Tasks**: Once the PRD is complete, use `auto_prdgen_task_research` to create research-backed development tasks

4. **Validate**: Use `auto_prdgen_prd_validate` to ensure the PRD meets quality standards

5. **Analyze Complexity**: Run `auto_prdgen_prd_complexity` to understand the project's complexity and resource requirements

Start by initializing the PRD and gathering the necessary information about the project."""

        return types.GetPromptResult(
            description="Create a new PRD project workflow",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=prompt_text)
                )
            ]
        )
    
    elif name == "analyze_existing_project":
        project_name = arguments.get("project_name", "")
        
        prompt_text = f"""You are analyzing an existing Auto-PRDGen project: {project_name}

Please perform a comprehensive analysis by:

1. **Project Structure**: Use `list_project_structure` with project_name="{project_name}" to understand the project layout

2. **Project Status**: Use `get_project_status` with project_name="{project_name}" to get current status and metrics

3. **PRD Analysis**: 
   - Read the PRD documents using the resource reading capabilities
   - Use `auto_prdgen_prd_validate` to check PRD quality
   - Use `auto_prdgen_prd_complexity` to analyze complexity

4. **Task Analysis**:
   - Review existing tasks and their statuses
   - Use `auto_prdgen_task_complexity` to analyze task complexity
   - Identify any dependencies or blockers

5. **Recommendations**: Provide actionable recommendations for:
   - Improving the PRD if needed
   - Optimizing task breakdown
   - Addressing any gaps or issues
   - Next steps for development

Start by examining the project structure and status."""

        return types.GetPromptResult(
            description="Analyze existing project workflow",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=prompt_text)
                )
            ]
        )
    
    elif name == "generate_development_plan":
        project_name = arguments.get("project_name", "")
        timeline = arguments.get("timeline", "3 months")
        
        prompt_text = f"""Generate a comprehensive development plan for project: {project_name}
Target Timeline: {timeline}

Please create a detailed development plan by:

1. **Project Assessment**:
   - Use `get_project_status` to understand current state
   - Review PRD and tasks using resource reading capabilities
   - Analyze complexity using `auto_prdgen_prd_complexity` and `auto_prdgen_task_complexity`

2. **Task Planning**:
   - Use `auto_prdgen_task_view` to see all available tasks
   - Use `auto_prdgen_task_next` to identify the best starting points
   - Check task dependencies with `auto_prdgen_task_deps`

3. **Timeline Creation**:
   - Break down the {timeline} timeline into phases/sprints
   - Allocate tasks to phases based on dependencies and complexity
   - Identify critical path and potential risks

4. **Resource Planning**:
   - Estimate effort for each task/phase
   - Identify required skills and team composition
   - Plan for testing, deployment, and maintenance

5. **Risk Mitigation**:
   - Identify potential blockers and dependencies
   - Create contingency plans
   - Set up monitoring and progress tracking

6. **Deliverables Plan**:
   - Define milestones and deliverables for each phase
   - Create acceptance criteria
   - Plan for user feedback and iteration

Generate a detailed, actionable development plan with timelines, resource requirements, and risk mitigation strategies."""

        return types.GetPromptResult(
            description="Generate comprehensive development plan",
            messages=[
                types.PromptMessage(
                    role="user", 
                    content=types.TextContent(type="text", text=prompt_text)
                )
            ]
        )
    
    else:
        raise ValueError(f"Unknown prompt: {name}")

async def main():
    """Main server entry point"""
    logger.info("Starting Auto-PRDGen MCP Server...")
    logger.info(f"Auto-PRDGen root directory: {AUTO_PRDGEN_ROOT}")
    
    # Ensure the auto-prdgen directory exists
    if not AUTO_PRDGEN_ROOT.exists():
        logger.error(f"Auto-PRDGen root directory not found: {AUTO_PRDGEN_ROOT}")
        sys.exit(1)
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="auto-prdgen-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 