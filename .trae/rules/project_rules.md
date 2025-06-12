
# LLM Interaction Guide for Auto-PRDGen Project: 1D_Diffusion_Couple_Simulator

This document provides a detailed guide for an LLM or automated agent on how to interact with and manage the files for the '1D_Diffusion_Couple_Simulator' project using the `auto-prdgen` command-line tool.

## 1. Project File Structure & Key Paths

- **Project Name**: `1D_Diffusion_Couple_Simulator`
- **Project Root Directory**: `/mnt/d/auto-prdgen/output/1D_Diffusion_Couple_Simulator`
- **Main PRD File**: `/mnt/d/auto-prdgen/output/1D_Diffusion_Couple_Simulator/PRD.md`
- **Main Tasks JSON File**: `/mnt/d/auto-prdgen/output/1D_Diffusion_Couple_Simulator/tasks.json`

When executing commands, it's best to run them from the project's root directory or use absolute paths for file arguments.

## 2. Core `auto-prdgen` Commands & Usage

Below are the primary commands for interacting with this project's artifacts.

### Viewing Project Files

- **View PRD**: `auto-prdgen prd-view --file "/mnt/d/auto-prdgen/output/1D_Diffusion_Couple_Simulator/PRD.md"`
- **View a specific task**: `auto-prdgen task-view --id <TASK_ID>` (select project '1D_Diffusion_Couple_Simulator' when prompted)
- **View all tasks**: `auto-prdgen task-view --all` (select project '1D_Diffusion_Couple_Simulator' when prompted)

### Updating Project Files

- **Update a PRD Section**:
  `auto-prdgen prd-update --file "/mnt/d/auto-prdgen/output/1D_Diffusion_Couple_Simulator/PRD.md" --section "## Section Title To Update" --content "New content for the section..."`
  *Note: The `--section` argument must be an exact match of an H2 markdown header in the PRD.*

- **Update a Task**:
  `auto-prdgen task-update --id <TASK_ID> --status "in progress" --description "new updated description"` (select project '1D_Diffusion_Couple_Simulator' when prompted)
  *Updatable fields include: `title`, `description`, `status`, `priority`, `details`, `testStrategy`.*

### Creating New Tasks

- **Initialize new tasks from the PRD**:
  `auto-prdgen task-init` (select project '1D_Diffusion_Couple_Simulator' when prompted)
  *This command should only be run once initially. It will overwrite `tasks.json`.*

- **Expand a task into subtasks**:
  `auto-prdgen task-expand --id <PARENT_TASK_ID>` (select project '1D_Diffusion_Couple_Simulator' when prompted)

### Analysis Commands

- **Validate the PRD**:
  `auto-prdgen prd-validate --file "/mnt/d/auto-prdgen/output/1D_Diffusion_Couple_Simulator/PRD.md"`

- **Analyze PRD Complexity**:
  `auto-prdgen prd-complexity --file "/mnt/d/auto-prdgen/output/1D_Diffusion_Couple_Simulator/PRD.md"`

- **Analyze Task Complexity**:
  `auto-prdgen task-complexity --id <TASK_ID>` (or `--all`) (select project '1D_Diffusion_Couple_Simulator' when prompted)
  *This command updates `tasks.json` with complexity data.*

## 3. Data Structures

### `tasks.json`
- **Path**: `/mnt/d/auto-prdgen/output/1D_Diffusion_Couple_Simulator/tasks.json`
- **Root Key**: `tasks` (a list of task objects)
- **Task Object Schema**:
  ```json
  {
    "id": "number",
    "title": "string",
    "description": "string",
    "status": "string (pending|in progress|completed|blocked)",
    "dependencies": "list of numbers",
    "priority": "string (low|medium|high)",
    "details": "string",
    "testStrategy": "string",
    "complexity_score": "number (1-10)",
    "complexity_factors": "list of strings",
    "estimated_effort": "string"
  }
  ```

## 4. Natural Language Interaction

For more complex or ambiguous operations, you can use the `nl-command`. This command interprets a natural language request and maps it to the appropriate `auto-prdgen` command.

- **Syntax**: `auto-prdgen nl-command "your natural language request"`
- **Example**: `auto-prdgen nl-command "show me task 5 for the 1D_Diffusion_Couple_Simulator project"`
- **Example**: `auto-prdgen nl-command "change the status of task 3 in 1D_Diffusion_Couple_Simulator to completed"`

## 5. General Guidelines for Automation

- **Context is Key**: Always ensure you are operating within the context of the correct project, either by running commands from `/mnt/d/auto-prdgen/output/1D_Diffusion_Couple_Simulator` or by using the interactive project selection prompt.
- **Idempotency**: Be cautious with commands like `task-init` which can overwrite existing data. Commands like `task-update` are idempotent for the fields they modify.
- **Parsing Output**: Command outputs are typically human-readable text. For structured data, always read directly from the source files (`tasks.json`, `prd.md`). Reports are saved as separate `.md` files in the project directory.
