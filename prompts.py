#!/usr/bin/env python

# This file contains all the prompts used in the PRD Creator application
# Edit these prompts to customize the behavior of the application

# Initial prompt to get the user's idea
INITIAL_PROMPT = "What do you like to build today? Please provide a title or a brief idea."

# Prompt to get a more detailed description
DESCRIPTION_PROMPT = "Great! Now, could you please provide a more detailed description for '{user_title_idea}'?"

# Prompt to inform the user that the LLM is processing their request
PROCESSING_PROMPT = "Thanks! I'm processing your request to understand it better and will ask some clarifying questions."

# Prompt to generate clarifying questions
QUESTION_GENERATION_PROMPT = """
You are an expert product manager. I'm trying to create a Product Requirements Document (PRD).
Based on the provided title/idea and description, please generate {num_questions_descriptor} insightful questions to help flesh out the PRD.
The questions should cover key aspects like target users, core features, success metrics, and potential challenges.

IMPORTANT FORMATTING INSTRUCTIONS:
- Output *only* the questions.
- Each question MUST be on a new line.
- Do NOT include any introductory phrases, preamble, headings (like "Questions:"), or any text other than the questions themselves.
- Do NOT number the questions (e.g., "1. Question") unless the numbering is inherently part of the question itself (e.g., "What are the top 3 priorities?").

Title/Idea: {user_title_idea}
Description: {user_description}
"""

# Prompt to display before showing the clarifying questions
CLARIFYING_QUESTIONS_INTRO = "Here are some questions to help refine the PRD:"

# Prompt to ask the user to answer the clarifying questions
ANSWER_QUESTIONS_PROMPT = "Please answer the following questions:"

# Prompt to thank the user for their answers
THANK_YOU_PROMPT = "Thank you for your answers! I will now generate the Product Requirement Document."

# Prompt to generate the PRD
PRD_GENERATION_PROMPT = """
You are an expert product manager. Generate a comprehensive Product Requirements Document (PRD) based on the following information.
The PRD should be well-structured and include the following key sections, as per best practices:

## 1. Introduction/Overview
(Based on initial title and description. Explain what problem it solves, who it's for, and why it's valuable.)

## 2. Project Specifics
(Participants, Status, Target Release - if applicable)
Date: {current_date}

## 3. Team Goals and Business Objectives

## 4. Background and Strategic Fit

## 5. Assumptions

## 6. User Stories
(Derived from user's answers and initial description)

## 7. Core Features
(Detailed features based on user's answers and initial description. For each feature, include:
- What it does
- Why it's important
- How it works at a high level)

## 8. User Experience
(Describe the user journey and experience. Include:
- User personas
- Key user flows
- UI/UX considerations)

## 9. Technical Architecture
(Outline the technical implementation details:
- System components
- Data models
- APIs and integrations
- Infrastructure requirements)

## 10. Development Roadmap
(Break down the development process into phases:
- MVP requirements
- Future enhancements
- Focus on scope and detailed requirements for each phase, not timelines)

## 11. Logical Dependency Chain
(Define the logical order of development:
- Which features need to be built first (foundation)
- Path to quickly achieving a usable/visible front end
- How to properly pace and scope each feature to be atomic yet buildable)

## 12. Success Metrics

## 13. Risks and Mitigations
(Identify potential risks and how they'll be addressed:
- Technical challenges
- MVP definition challenges
- Resource constraints)

## 14. Appendix
(Include any additional information:
- Research findings
- Technical specifications)

Initial Title/Idea: {user_title_idea}
Initial Description: {user_description}

User's Answers to Clarifying Questions:
{user_answers}

Product Requirement Document:
"""

# Prompt to generate tasks from a PRD
TASK_GENERATION_PROMPT = """
You are an AI assistant specialized in analyzing Product Requirements Documents (PRDs) and generating a structured, logically ordered, dependency-aware and sequenced list of development tasks in JSON format.

Analyze the provided PRD content and generate development tasks. Each task should represent a logical unit of work needed to implement the requirements and focus on the most direct and effective way to implement the requirements without unnecessary complexity or overengineering. Include pseudo-code, implementation details, and test strategy for each task.

{granularity_instructions}

Assign sequential IDs starting from 1. Infer title, description, details, and test strategy for each task based *only* on the PRD content.
Set status to 'pending', dependencies to an empty array [], and priority to 'medium' initially for all tasks.

Respond ONLY with a valid JSON object containing a single key "tasks", where the value is an array of task objects. Do not include any explanation or markdown formatting.

Each task should follow this JSON structure:
{{
    "id": number,
    "title": string,
    "description": string,
    "status": "pending",
    "dependencies": number[] (IDs of tasks this depends on),
    "priority": "high" | "medium" | "low",
    "details": string (implementation details),
    "testStrategy": string (validation approach)
}}

Guidelines:
1. Each task should be atomic and focused on a single responsibility following the most up to date best practices and standards
2. Order tasks logically - consider dependencies and implementation sequence
3. Early tasks should focus on setup, core functionality first, then advanced features
4. Include clear validation/testing approach for each task
5. Set appropriate dependency IDs (a task can only depend on tasks with lower IDs)
6. Assign priority (high/medium/low) based on criticality and dependency order
7. Include detailed implementation guidance in the "details" field
8. If the PRD contains specific requirements for libraries, database schemas, frameworks, tech stacks, or any other implementation details, STRICTLY ADHERE to these requirements in your task breakdown
9. Focus on filling in any gaps left by the PRD or areas that aren't fully specified, while preserving all explicit requirements
10. Always aim to provide the most direct path to implementation, avoiding over-engineering or roundabout approaches
12. Ensure the JSON is properly formatted and complete - do not truncate the output

PRD Content:
--- PRD START ---
{prd_content}
--- PRD END ---

Return your response in this exact format (ensure the JSON is complete and properly closed):
{{
    "tasks": [
        {{
            "id": 1,
            "title": "Setup Project Repository",
            "description": "...",
            "status": "pending",
            "dependencies": [],
            "priority": "high",
            "details": "...",
            "testStrategy": "..."
        }}
    ]
}}
"""

# Messages for task initialization
TASK_INIT_START = "Starting Task Initialization..."
NO_PRD_FILES = "No PRD files found in the '{output_dir}' directory."
GENERATE_PRD_FIRST = "Please generate a PRD first using the 'prd-init' command."
FOUND_PRD_FILES = "Found the following PRD files:"
SELECT_PRD = "Enter the number of the PRD to process: "
INVALID_SELECTION = "Invalid selection. Please enter a number from the list."
INVALID_INPUT = "Invalid input. Please enter a number."
PRD_SELECTED = "You selected: {prd_file_name}"
PRD_READ_SUCCESS = "Successfully read '{prd_file_name}'."
PROCESSING_PRD = "Processing the PRD to generate tasks..."
PARSED_TASKS_SUCCESS = "Successfully parsed generated tasks JSON."
TASKS_SAVED = "Tasks saved to {output_tasks_filename}"
CONVERTING_TASKS = "Converting tasks to individual Markdown files..."
ALL_TASKS_CONVERTED = "All tasks converted to Markdown files in '{tasks_dir}' directory."

# Task Management Extension Prompts
TASK_UPDATE_START = "Starting Task Update..."
TASK_VIEW_START = "Displaying Tasks..."
TASK_EXPORT_START = "Exporting Tasks..."
NO_TASKS_FOUND = "No tasks.json file found in the selected project directory."
TASK_UPDATED_SUCCESS = "Task #{task_id} updated successfully."
INVALID_TASK_ID = "Invalid task ID. Please enter a valid task number."
TASK_STATUS_OPTIONS = ["pending", "in-progress", "completed", "blocked"]
TASK_PRIORITY_OPTIONS = ["low", "medium", "high"]
EXPORT_SUCCESS = "Tasks exported successfully to {export_format}."
EXPORT_ERROR = "Error exporting tasks: {error}"

# Priority 1 Enhancement Prompts
TASK_NEXT_START = "Finding next available task..."
NO_AVAILABLE_TASKS = "No available tasks found. All tasks are either completed or blocked by dependencies."
NEXT_TASK_FOUND = "Next recommended task:"
TASK_EXPAND_START = "Expanding task into subtasks..."
TASK_EXPAND_SUCCESS = "Task #{task_id} expanded successfully with {count} subtasks."
TASK_COMPLEXITY_START = "Analyzing task complexity..."
COMPLEXITY_ANALYSIS_COMPLETE = "Complexity analysis complete."
DEPENDENCY_ADDED = "Dependency added: Task #{task_id} now depends on Task #{depends_on}."
DEPENDENCY_REMOVED = "Dependency removed: Task #{task_id} no longer depends on Task #{depends_on}."
CIRCULAR_DEPENDENCY_ERROR = "Error: Adding this dependency would create a circular dependency."
INVALID_DEPENDENCY_ERROR = "Error: Cannot add dependency - task #{depends_on} does not exist."
SELF_DEPENDENCY_ERROR = "Error: A task cannot depend on itself."
DEPENDENCY_VALIDATION_START = "Validating all task dependencies..."
DEPENDENCY_VALIDATION_COMPLETE = "Dependency validation complete. Found {issues} issues."

# AI Prompts for Priority 1 Features
TASK_EXPANSION_PROMPT = """
You are an AI assistant specialized in breaking down complex development tasks into smaller, manageable subtasks.

Analyze the provided task and break it down into 3-7 subtasks that are:
1. Atomic and focused on a single responsibility
2. Logically ordered with clear dependencies
3. Implementable within 1-4 hours each
4. Include specific implementation details
5. Have clear acceptance criteria

Original Task:
ID: {task_id}
Title: {task_title}
Description: {task_description}
Details: {task_details}

Respond ONLY with a valid JSON object containing subtasks. Use the format:
{{
    "subtasks": [
        {{
            "id": "{task_id}.1",
            "title": "Subtask title",
            "description": "Detailed description",
            "status": "pending",
            "dependencies": [],
            "priority": "medium",
            "details": "Implementation details and approach",
            "testStrategy": "How to validate this subtask",
            "estimatedHours": 2
        }}
    ]
}}
"""

TASK_COMPLEXITY_ANALYSIS_PROMPT = """
You are an AI assistant specialized in analyzing software development task complexity.

Analyze the provided task(s) and provide a complexity assessment including:
1. Complexity score (1-10, where 1 is trivial and 10 is extremely complex)
2. Factors contributing to complexity
3. Recommendation on whether the task should be broken down
4. Suggested number of subtasks if breakdown is recommended
5. Risk factors and mitigation strategies

Task(s) to analyze:
{tasks_content}

Respond with a detailed analysis in markdown format.
"""

# PRD Enhancement Tool Prompts
PRD_UPDATE_START = "Starting PRD Update..."
PRD_COMPARE_START = "Comparing PRD Versions..."
PRD_VALIDATE_START = "Validating PRD..."
PRD_UPDATE_SUCCESS = "PRD updated successfully."
PRD_VALIDATION_COMPLETE = "PRD validation complete."
NO_PRD_VERSIONS = "No previous PRD versions found for comparison."

# PRD Update Prompt
PRD_UPDATE_PROMPT = """
You are an expert product manager. Update the existing PRD based on the user's modification request.
Maintain the original structure and formatting while incorporating the requested changes.
Ensure all sections remain coherent and well-integrated.

Original PRD:
{original_prd}

Modification Request:
{modification_request}

Updated PRD:
"""

# PRD Validation Prompt
PRD_VALIDATION_PROMPT = """
You are an expert product manager. Analyze the provided PRD for completeness and quality.
Provide a detailed assessment covering:

1. **Completeness Score (0-100)**: Overall completeness percentage
2. **Missing Sections**: List any standard PRD sections that are missing
3. **Content Quality**: Assess clarity, specificity, and actionability
4. **Recommendations**: Specific suggestions for improvement
5. **Strengths**: What the PRD does well
6. **Critical Issues**: Any major problems that need immediate attention

PRD Content:
{prd_content}

Provide your assessment in a structured format with clear headings and actionable feedback.
"""

# Task Export Templates
JIRA_EXPORT_TEMPLATE = """
Summary: {title}
Description: {description}
Priority: {priority}
Status: {status}
Details: {details}
Test Strategy: {testStrategy}
Dependencies: {dependencies}
---
"""

TRELLO_EXPORT_TEMPLATE = """
Card: {title}
Description: {description}
Priority: {priority}
Status: {status}
Checklist:
- Implementation: {details}
- Testing: {testStrategy}
- Dependencies: {dependencies}
---
"""

GITHUB_ISSUE_TEMPLATE = """
## {title}

**Description:** {description}

**Priority:** {priority}
**Status:** {status}

**Implementation Details:**
{details}

**Test Strategy:**
{testStrategy}

**Dependencies:**
{dependencies}

---
"""

# Priority 2: Advanced Features Prompts

# PRD Complexity Analysis Prompt
PRD_COMPLEXITY_ANALYSIS_PROMPT = """
You are an AI assistant specialized in analyzing Product Requirements Document complexity.

Analyze the provided PRD and provide a comprehensive complexity assessment including:

1. **Overall Complexity Score (1-10)**: Where 1 is simple and 10 is extremely complex
2. **Technical Complexity**: Database design, API complexity, integrations, scalability requirements
3. **Business Complexity**: Market requirements, user personas, feature interdependencies
4. **Implementation Complexity**: Development effort, team coordination, timeline challenges
5. **Risk Assessment**: Technical risks, market risks, resource risks
6. **Recommendations**: 
   - Should the project be broken into phases?
   - What are the critical path items?
   - Resource allocation suggestions
   - Timeline estimates
7. **Complexity Breakdown by Section**: Rate each major PRD section (1-10)
8. **Mitigation Strategies**: How to reduce complexity and manage risks

PRD Content:
{prd_content}

Provide your analysis in a detailed markdown report with clear sections and actionable insights.
"""

# Natural Language Command Processing Prompt
NATURAL_LANGUAGE_COMMAND_PROMPT = """
You are an AI assistant that interprets natural language commands for a PRD and task management system.

Analyze the user's natural language input and determine:
1. **Intent**: What action does the user want to perform?
2. **Command**: Map to one of these available commands:
   - prd-init: Create a new PRD
   - prd-update: Modify an existing PRD
   - prd-validate: Validate PRD quality
   - prd-compare: Compare PRD versions
   - task-init: Generate tasks from PRD
   - task-next: Find next available task
   - task-expand: Break down a task into subtasks
   - task-deps: Manage task dependencies
   - task-complexity: Analyze task complexity
   - task-update: Update task status/details
   - task-view: Display tasks
   - task-export: Export tasks to different formats
3. **Parameters**: Extract any specific parameters (task IDs, file names, etc.)
4. **Confidence**: Rate your confidence in the interpretation (1-10)

User Input: "{user_input}"

Respond in JSON format:
{{
  "intent": "description of what user wants",
  "command": "mapped command name",
  "parameters": {{
    "param1": "value1",
    "param2": "value2"
  }},
  "confidence": 8,
  "explanation": "why you chose this mapping"
}}

If the input is unclear or doesn't match any command, set confidence to 3 or lower and ask for clarification.
"""

# Research-Backed Task Generation Prompt
RESEARCH_BACKED_TASK_GENERATION_PROMPT = """
You are an AI assistant specialized in generating development tasks based on industry best practices and research.

Analyze the provided PRD and generate tasks that incorporate:

1. **Industry Best Practices**: Follow established software development methodologies
2. **Security Standards**: Include security considerations (OWASP, data protection)
3. **Performance Optimization**: Consider scalability and performance from the start
4. **Testing Strategies**: Implement comprehensive testing approaches (unit, integration, e2e)
5. **DevOps Integration**: Include CI/CD, monitoring, and deployment considerations
6. **Accessibility**: Ensure compliance with accessibility standards (WCAG)
7. **Code Quality**: Include code review, documentation, and maintainability tasks
8. **Risk Mitigation**: Add tasks to address identified technical and business risks

For each task, include:
- **Research Justification**: Why this task is important based on industry standards
- **Best Practice References**: Mention relevant methodologies or standards
- **Quality Gates**: Define clear acceptance criteria
- **Risk Mitigation**: How this task reduces project risks

PRD Content:
--- PRD START ---
{prd_content}
--- PRD END ---

Generate tasks in the same JSON format as the standard task generation, but with enhanced details that reflect research-backed approaches.

Return your response in this exact format:
{{
    "tasks": [
        {{
            "id": 1,
            "title": "Task Title",
            "description": "Task description",
            "status": "pending",
            "dependencies": [],
            "priority": "high",
            "details": "Implementation details with best practices",
            "testStrategy": "Comprehensive testing approach",
            "researchJustification": "Why this task is important",
            "bestPracticeReferences": "Relevant standards/methodologies",
            "qualityGates": "Acceptance criteria",
            "riskMitigation": "How this reduces risks"
        }}
    ]
}}
"""

# Simple Research-Backed Task Generation Prompt (for high-level epics)
SIMPLE_RESEARCH_BACKED_TASK_GENERATION_PROMPT = """
You are an AI assistant specialized in generating a concise list of high-level, research-backed development epics or major features.

Analyze the provided PRD and generate a SMALLER NUMBER of high-level tasks (epics) that incorporate key industry best practices and research insights. While these are epics, they should still be comprehensive in their research backing.

For each epic, include ALL relevant details:
- **Title**: A clear, concise title for the epic.
- **Description**: A summary of what the epic covers and its strategic value.
- **Details**: Strategic overview and goals for this epic, incorporating best practices.
- **Test Strategy**: High-level testing approach (e.g., 'End-to-end testing of the core user flow, focusing on key acceptance criteria derived from best practices').
- **Research Justification**: Justification explaining why this epic and its approach are based on sound industry practices or research.
- **Best Practice References**: Mention relevant methodologies, standards, or research that inform this epic (summarized if necessary).
- **Quality Gates**: Define clear, high-level acceptance criteria or quality gates for the epic.
- **Risk Mitigation**: Identify potential high-level risks associated with this epic and suggest mitigation strategies, informed by research.

PRD Content:
--- PRD START ---
{prd_content}
--- PRD END ---

Generate the epics in the standard JSON task format. The key is FEWER, HIGHER-LEVEL TASKS, but with COMPLETE research information for each.

Return your response in this exact format:
{{
    "tasks": [
        {{
            "id": 1,
            "title": "Epic Title (e.g., Implement Core User Authentication System)",
            "description": "High-level description of the epic, its goals, and strategic value.",
            "status": "pending",
            "dependencies": [],
            "priority": "high",
            "details": "Strategic overview of implementing the user authentication system, including considerations for OAuth 2.0, secure password hashing (e.g., Argon2), and multi-factor authentication options.",
            "testStrategy": "End-to-end testing of login, registration, and password recovery flows. Security penetration testing focused on authentication vulnerabilities.",
            "researchJustification": "Adopting industry-standard authentication protocols enhances security and user trust, as supported by numerous security whitepapers and NIST guidelines.",
            "bestPracticeReferences": "NIST SP 800-63B (Digital Identity Guidelines), OWASP ASVS (Application Security Verification Standard) for authentication.",
            "qualityGates": "Successful completion of all authentication user stories, passing of security audit, and compliance with relevant data protection regulations (e.g., GDPR if applicable).",
            "riskMitigation": "Risk: Credential stuffing attacks. Mitigation: Implement rate limiting and account lockout policies. Risk: Weak password selection. Mitigation: Enforce strong password complexity rules and provide password strength meters."
        }}
    ]
}}
"""

# Messages for Priority 2 Features


# AI-Powered Task Prioritization Prompt
AI_TASK_PRIORITIZATION_PROMPT = """
You are an expert project manager and AI assistant. You are given a list of currently available (pending and unblocked) tasks for a software project.

Your goal is to recommend the single most logical task to work on next. Consider factors such as:
- Overall project impact and value delivered by the task.
- Foundational nature: Does this task unblock other significant features or work streams?
- Urgency or critical path: Is this task essential for near-term goals?
- Logical sequence: Does completing this task make the most sense in the current project phase?
- Cohesion: Does this task relate closely to recently completed work, minimizing context switching?

Available Tasks (summary):
{available_tasks_summary}

Based on your analysis, please recommend the single best task to tackle next.
Respond ONLY with a valid JSON object containing the following keys:
- "recommended_task_id": The ID of the task you recommend.
- "justification": A brief (1-2 sentence) explanation for your recommendation.

Example JSON Response:
{{
  "recommended_task_id": 10,
  "justification": "Completing task 10 (User Authentication) is critical as it's a foundational piece for most other user-facing features and has high project impact."
}}
"""
COMPLEXITY_ANALYSIS_START = "Starting complexity analysis..."
NATURAL_LANGUAGE_PROCESSING = "Processing natural language command..."
RESEARCH_BACKED_GENERATION = "Generating research-backed tasks..."
COMPLEXITY_REPORT_SAVED = "Complexity analysis report saved to {filename}"
COMMAND_INTERPRETED = "Command interpreted: {command}"
COMMAND_UNCLEAR = "Command unclear. Please provide more specific instructions."
RESEARCH_TASKS_GENERATED = "Research-backed tasks generated successfully."


# Template for the .mdc (Model Developer Context) file
MDC_FILE_TEMPLATE = """
# LLM Interaction Guide for Auto-PRDGen Project: {project_name}

This document provides a detailed guide for an LLM or automated agent on how to interact with and manage the files for the '{project_name}' project using the `auto-prdgen` command-line tool.

## 1. Project File Structure & Key Paths

- **Project Name**: `{project_name}`
- **Project Root Directory**: `{project_root_path}`
- **Main PRD File**: `{project_prd_path}`
- **Main Tasks JSON File**: `{project_tasks_path}`

When executing commands, it's best to run them from the project's root directory or use absolute paths for file arguments.

## 2. Core `auto-prdgen` Commands & Usage

Below are the primary commands for interacting with this project's artifacts.

### Viewing Project Files

- **View PRD**: `auto-prdgen prd-view --file "{project_prd_path}"`
- **View a specific task**: `auto-prdgen task-view --id <TASK_ID>` (select project '{project_name}' when prompted)
- **View all tasks**: `auto-prdgen task-view --all` (select project '{project_name}' when prompted)

### Updating Project Files

- **Update a PRD Section**:
  `auto-prdgen prd-update --file "{project_prd_path}" --section "## Section Title To Update" --content "New content for the section..."`
  *Note: The `--section` argument must be an exact match of an H2 markdown header in the PRD.*

- **Update a Task**:
  `auto-prdgen task-update --id <TASK_ID> --status "in progress" --description "new updated description"` (select project '{project_name}' when prompted)
  *Updatable fields include: `title`, `description`, `status`, `priority`, `details`, `testStrategy`.*

### Creating New Tasks

- **Initialize new tasks from the PRD**:
  `auto-prdgen task-init` (select project '{project_name}' when prompted)
  *This command should only be run once initially. It will overwrite `tasks.json`.*

- **Expand a task into subtasks**:
  `auto-prdgen task-expand --id <PARENT_TASK_ID>` (select project '{project_name}' when prompted)

### Analysis Commands

- **Validate the PRD**:
  `auto-prdgen prd-validate --file "{project_prd_path}"`

- **Analyze PRD Complexity**:
  `auto-prdgen prd-complexity --file "{project_prd_path}"`

- **Analyze Task Complexity**:
  `auto-prdgen task-complexity --id <TASK_ID>` (or `--all`) (select project '{project_name}' when prompted)
  *This command updates `tasks.json` with complexity data.*

## 3. Data Structures

### `tasks.json`
- **Path**: `{project_tasks_path}`
- **Root Key**: `tasks` (a list of task objects)
- **Task Object Schema**:
  ```json
  {{
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
  }}
  ```

## 4. Natural Language Interaction

For more complex or ambiguous operations, you can use the `nl-command`. This command interprets a natural language request and maps it to the appropriate `auto-prdgen` command.

- **Syntax**: `auto-prdgen nl-command "your natural language request"`
- **Example**: `auto-prdgen nl-command "show me task 5 for the {project_name} project"`
- **Example**: `auto-prdgen nl-command "change the status of task 3 in {project_name} to completed"`

## 5. General Guidelines for Automation

- **Context is Key**: Always ensure you are operating within the context of the correct project, either by running commands from `{project_root_path}` or by using the interactive project selection prompt.
- **Idempotency**: Be cautious with commands like `task-init` which can overwrite existing data. Commands like `task-update` are idempotent for the fields they modify.
- **Parsing Output**: Command outputs are typically human-readable text. For structured data, always read directly from the source files (`tasks.json`, `prd.md`). Reports are saved as separate `.md` files in the project directory.
"""


# Prompt for Single Task Complexity Analysis (to be used by task-complexity command)
SINGLE_TASK_COMPLEXITY_PROMPT = """
You are an expert AI project analyst. Analyze the following software development task and provide a detailed complexity assessment.

Task Details:
ID: {task_id}
Title: {task_title}
Description: {task_description}
Details: {task_details}
Priority: {task_priority}
Status: {task_status}
Dependencies: {task_dependencies}

Your analysis should include:
1.  **Overall Complexity Score**: An integer score from 1 (very low) to 10 (very high).
2.  **Key Complexity Factors**: A list of 2-5 primary factors contributing to the task's complexity (e.g., "Requires new technology stack", "High number of external dependencies", "Ambiguous requirements", "Significant UI/UX effort", "Critical security implications").
3.  **Estimated Effort**: A qualitative estimate (e.g., "Very Small", "Small", "Medium", "Large", "Very Large") or a rough quantitative estimate if possible (e.g., "1-2 days", "3-5 story points").
4.  **Narrative Report**: A detailed textual explanation of the complexity, elaborating on the factors, potential risks, and any recommendations for managing or mitigating the complexity.

Please return your response as a single, valid JSON object with two top-level keys: "structured_data" and "narrative_report".

Example JSON Response Format:
{{
  "structured_data": {{
    "complexity_score": 7,
    "complexity_factors": [
      "Integration with legacy system",
      "Requires learning a new API",
      "Unclear performance requirements"
    ],
    "estimated_effort": "Medium (3-5 days)"
  }},
  "narrative_report": "The task of integrating the new user module with the legacy payment system presents a complexity score of 7. Key factors include the outdated architecture of the legacy system, which will require careful interface design and potentially custom adapters. Additionally, the development team will need to allocate time to learn the new third-party API for currency conversion. Performance requirements are currently underspecified, adding a risk of rework. It is recommended to allocate dedicated time for API learning and to conduct performance testing early in the development cycle."
}}

CRITICAL: Pay special attention to escaping characters within string values. For example, any double quotes inside the 'narrative_report' string must be escaped with a backslash (e.g., \"some quoted text\").

Ensure the JSON is well-formed.
"""

# Research-Backed Task Enhancement Prompt (for existing tasks)
RESEARCH_BACKED_TASK_ENHANCEMENT_PROMPT = """
You are an AI assistant specialized in enhancing existing development tasks with industry best practices and research-backed information.

You are provided with:
1. A PRD (Product Requirements Document)
2. Existing tasks that were previously generated

Your goal is to ENHANCE the existing tasks by adding research-backed information while preserving their core structure, IDs, titles, descriptions, status, dependencies, and priority.

For each existing task, ADD or ENHANCE the following fields:
- **researchJustification**: Why this task is important based on industry standards
- **bestPracticeReferences**: Mention relevant methodologies or standards  
- **qualityGates**: Define clear acceptance criteria based on best practices
- **riskMitigation**: How this task reduces project risks
- **details**: Enhance existing details with best practices (don't replace, enhance)
- **testStrategy**: Enhance existing test strategy with comprehensive approaches

DO NOT:
- Change task IDs, titles, basic descriptions, status, dependencies, or priority
- Remove or replace existing content - only enhance it
- Create new tasks - only work with the provided existing tasks

PRD Content:
--- PRD START ---
{prd_content}
--- PRD END ---

Existing Tasks:
--- EXISTING TASKS START ---
{existing_tasks_json}
--- EXISTING TASKS END ---

Return the enhanced tasks in the same JSON format, preserving all original fields and adding the research-backed enhancements.

Return your response in this exact format:
{{
    "tasks": [
        {{
            "id": <original_id>,
            "title": "<original_title>",
            "description": "<original_description>", 
            "status": "<original_status>",
            "dependencies": <original_dependencies>,
            "priority": "<original_priority>",
            "details": "<enhanced_details_with_best_practices>",
            "testStrategy": "<enhanced_test_strategy>",
            "researchJustification": "Why this task is important based on industry standards",
            "bestPracticeReferences": "Relevant standards/methodologies",
            "qualityGates": "Clear acceptance criteria based on best practices",
            "riskMitigation": "How this task reduces project risks"
        }}
    ]
}}
"""

# Simple Research-Backed Task Enhancement Prompt (for existing high-level tasks)
SIMPLE_RESEARCH_BACKED_TASK_ENHANCEMENT_PROMPT = """
You are an AI assistant specialized in enhancing existing high-level development tasks/epics with industry best practices and research-backed information.

You are provided with:
1. A PRD (Product Requirements Document)  
2. Existing high-level tasks/epics that were previously generated

Your goal is to ENHANCE the existing tasks by adding comprehensive research-backed information while preserving their core structure, IDs, titles, descriptions, status, dependencies, and priority.

For each existing task, ADD or ENHANCE the following fields with comprehensive information:
- **researchJustification**: Detailed justification based on industry practices and research
- **bestPracticeReferences**: Comprehensive references to relevant methodologies, standards, or research
- **qualityGates**: Define clear, high-level acceptance criteria based on best practices
- **riskMitigation**: Detailed risk analysis and mitigation strategies
- **details**: Enhance existing details with strategic best practices (don't replace, enhance)
- **testStrategy**: Enhance with comprehensive high-level testing approaches

DO NOT:
- Change task IDs, titles, basic descriptions, status, dependencies, or priority
- Remove or replace existing content - only enhance it
- Create new tasks - only work with the provided existing tasks

PRD Content:
--- PRD START ---
{prd_content}
--- PRD END ---

Existing Tasks:
--- EXISTING TASKS START ---
{existing_tasks_json}
--- EXISTING TASKS END ---

Return the enhanced tasks in the same JSON format, preserving all original fields and adding comprehensive research-backed enhancements.

Return your response in this exact format:
{{
    "tasks": [
        {{
            "id": <original_id>,
            "title": "<original_title>",
            "description": "<original_description>",
            "status": "<original_status>", 
            "dependencies": <original_dependencies>,
            "priority": "<original_priority>",
            "details": "<enhanced_strategic_details_with_best_practices>",
            "testStrategy": "<enhanced_comprehensive_test_strategy>",
            "researchJustification": "Detailed justification based on industry practices and research",
            "bestPracticeReferences": "Comprehensive references to methodologies, standards, research",
            "qualityGates": "Clear high-level acceptance criteria based on best practices", 
            "riskMitigation": "Detailed risk analysis and mitigation strategies"
        }}
    ]
}}
"""