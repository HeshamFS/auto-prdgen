# PRD Creator CLI

An AI-powered CLI tool for creating Product Requirement Documents (PRDs) and managing development tasks through a conversational interface with Google's Gemini LLM.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [PRD Management](#prd-management)
- [Task Management](#task-management)
- [Natural Language Commands](#natural-language-commands)
- [Advanced Analysis](#advanced-analysis)
- [Output and Project Structure](#output-and-project-structure)
- [Technical Details](#technical-details)

## Prerequisites

- Python 3.6 or higher
- Pip (Python package installer)
- Access to Google Generative AI API (with an API key)

## Setup

1. **Clone the repository (if applicable) or download the files**

2. **Navigate to the project directory:**
   ```bash
   cd path/to/your/project
   ```

3. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

4. **Install the package:**
   ```bash
   pip install .
   ```
   This will install all necessary dependencies listed in `setup.py` (including `google-generativeai`, `python-dotenv`, and `colorama`).

5. **Set up your Google API Key and Configuration:**
   Create a `.env` file in the project root and add your API key and optional config:
   ```
   # Required: Google API Key
   GOOGLE_API_KEY="YOUR_API_KEY"
   
   # Optional: Choose a specific model (defaults to gemini-2.5-flash-preview-05-20)
   # MODEL_NAME="gemini-2.5-pro-preview-06-05"
   ```

## PRD Management

### Generate a PRD
```bash
auto-prdgen prd-init
```
Guides you through creating a comprehensive PRD, which will be saved in the `output` directory.

You can also specify the number of clarifying questions the AI should ask:
```bash
auto-prdgen prd-init -nq 5
```
Or a range:
```bash
auto-prdgen prd-init --num-questions 3-5
```
This defaults to "3-5" questions if not specified.

### Modify Existing PRDs
```bash
auto-prdgen prd-update
```
Allows you to update and refine existing PRDs.

### Compare PRD Versions
```bash
auto-prdgen prd-compare
```
Compares different versions of your PRD to track changes.

### Validate PRD Quality
```bash
auto-prdgen prd-validate
```
Checks your PRD for completeness, consistency, and quality.

### Analyze PRD Complexity
```bash
auto-prdgen prd-complexity
```
Provides comprehensive analysis of your PRD including:
- Technical and functional complexity assessment
- Risk analysis and mitigation strategies
- Resource estimation and timeline guidance
- Quality improvement recommendations
- Detailed analysis report generation

## Task Management

### Generate Tasks from PRD
```bash
# Standard task generation from PRD
auto-prdgen task-init [--level simple|detailed]

# AI-Powered Research-Backed Task Generation (Recommended)
auto-prdgen task-research [--level simple|detailed] [--force]
```
Converts your PRD into actionable development tasks. 
- `task-init` provides a direct conversion.
- `task-research` (recommended) enhances tasks with AI-driven industry best practices, security considerations, testing strategies, and more.
  - `--level detailed` (default): Generates a comprehensive list of granular, research-backed tasks. All fields are populated with detailed information.
  - `--level simple`: Generates a smaller number of high-level, research-backed epics. All fields are still populated with relevant, summarized research-backed information.

Features:
- Task breakdown and prioritization
- Individual task files and JSON tracking
- Research justifications and best practices (with `task-research`)

### Find Next Available Task
```bash
auto-prdgen task-next
```
Uses AI to analyze all available (pending and unblocked) tasks and recommend the single most logical task to work on next, considering impact, urgency, and overall project flow. Provides a justification for its recommendation. If only one task is available, it's presented directly.

### Update Task Status
```bash
auto-prdgen task-update
```
Update the status, details, and other properties of tasks.

### View Tasks
```bash
auto-prdgen task-view
```
Display tasks with customizable filtering options.

### Break Down Complex Tasks
```bash
auto-prdgen task-expand --id <task_id> [--force]
```
Uses AI to break down complex tasks into manageable subtasks.

### Manage Task Dependencies
```bash
# Add dependency
auto-prdgen task-deps --id <task_id> --add --depends-on <dependency_id>

# Remove dependency
auto-prdgen task-deps --id <task_id> --remove --depends-on <dependency_id>

# Validate all dependencies
auto-prdgen task-deps --validate
```
Advanced dependency management with circular dependency detection.

### Analyze Task Complexity
```bash
# Analyze specific task
auto-prdgen task-complexity --id <task_id>

# Analyze all tasks
auto-prdgen task-complexity --all
```
AI-powered complexity analysis with recommendations for better planning.

### Export Tasks
```bash
auto-prdgen task-export
```
Export tasks to various project management tools and formats.

## Natural Language Commands

```bash
# Use natural language to interact with the tool
auto-prdgen nl-command "show me all pending tasks"
auto-prdgen nl-command "create a task for user authentication"
auto-prdgen nl-command "what's the next priority task?"
auto-prdgen nl-command "analyze the complexity of my PRD"

# Only suggest commands without executing them
auto-prdgen nl-command --suggest-only "show me all pending tasks"
```

Allows intuitive interaction using natural language:
- Intent recognition and command mapping
- Parameter extraction from natural language
- Confidence scoring for interpretations
- Automatic command execution (or suggestion with --suggest-only)

## Advanced Analysis

## Output and Project Structure

### Output Files
The generated PRD will be saved as a Markdown file in the `output/` directory. The filename will be unique, incorporating the project name and a timestamp to avoid overwrites. The script will print the full path to the saved file upon completion.

### Project Structure
- `.env`: Stores your Google API Key (ensure this file is in your `.gitignore` if using version control)
- `prd_creator.py`: The main Python script for the CLI application
- `prompts.py`: Contains AI prompts for various features
- `output/`: Created automatically to store generated files
  - Project directories with PRDs, tasks, and analysis reports
- `requirements.txt`: Lists the Python dependencies for the project

## Technical Details

### Model Configuration
By default, the application uses the `gemini-2.5-flash-preview-05-20` model, but you can specify a different model in your `.env` file:

```
MODEL_NAME="gemini-2.5-pro-preview-06-05"
```

Available models (as of June 2025):
- 'gemini-2.5-pro-preview-06-05'
- 'gemini-2.5-flash-preview-05-20'	
- 'gemini-2.0-flash'
- 'gemini-2.0-flash-lite'

### Available Commands

| Command | Description |
|---------|-------------|
| `prd-init` | Create a new PRD |
| `prd-update` | Modify existing PRDs |
| `prd-compare` | Compare PRD versions |
| `prd-validate` | Validate PRD quality |
| `prd-complexity` | Analyze PRD complexity |
| `task-init` | Generate tasks from PRD |
| `task-research` | Generate research-backed tasks |
| `task-update` | Update task status |
| `task-view` | Display tasks with filters |
| `task-next` | Find next available task |
| `task-expand` | Break down tasks into subtasks |
| `task-deps` | Manage task dependencies |
| `task-complexity` | Analyze task complexity |
| `task-export` | Export tasks to various formats |
| `nl-command` | Process natural language commands |