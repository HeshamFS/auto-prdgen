#!/usr/bin/env python
import os
import google.generativeai as genai
from dotenv import load_dotenv
import uuid
from pathlib import Path
import time # Added for thinking animation
from datetime import datetime # Added for current date
from colorama import Fore, Style, init # Added for colored output
import argparse # Added for CLI argument parsing
import json # Added for JSON processing
from prompts import * # Import all prompts from prompts.py
from config import config # Import configuration manager
from ui_utils import (
    ProgressBar, EnhancedSpinner, colored_print, quiet_print,
    get_user_input, confirm_action, select_from_list, display_header, stream_print
)

# Initialize Colorama
init(autoreset=True)

# --- Environment Variable Loading ---
# Explicitly specify the path to the .env file in the current working directory.
# This ensures that the .env file is loaded from where the user runs the command.
current_cwd = Path(os.getcwd())
dotenv_path_in_cwd = current_cwd / '.env'

quiet_print(f"Attempting to load .env from: {dotenv_path_in_cwd}", force=True)

# load_dotenv() returns True if a .env file was loaded.
loaded_from_dotenv = load_dotenv(dotenv_path=dotenv_path_in_cwd, verbose=False, override=True)

if loaded_from_dotenv:
    quiet_print(f"Successfully loaded .env file from {dotenv_path_in_cwd}", force=True)
else:
    quiet_print(f".env file not loaded from {dotenv_path_in_cwd}. Will check for manual loading.", force=True)

API_KEY = os.getenv("GOOGLE_API_KEY")

# Manual fallback if python-dotenv didn't set the key via os.getenv()
if not API_KEY and dotenv_path_in_cwd.exists():
    quiet_print(f"GOOGLE_API_KEY not found via os.getenv(). Attempting manual parse of {dotenv_path_in_cwd}")
    try:
        with open(dotenv_path_in_cwd, 'r') as f_manual_env:
            for line in f_manual_env:
                line = line.strip()
                if line.startswith('GOOGLE_API_KEY='):
                    key_value = line.split('=', 1)
                    if len(key_value) == 2:
                        manual_key = key_value[1].strip().strip('"').strip("'") # Remove potential quotes
                        if manual_key:
                            os.environ['GOOGLE_API_KEY'] = manual_key
                            API_KEY = os.getenv("GOOGLE_API_KEY") # Re-fetch
                            quiet_print(f"Successfully parsed and set GOOGLE_API_KEY from {dotenv_path_in_cwd}")
                            break
                        else:
                            colored_print(f"Found GOOGLE_API_KEY= but the value is empty in {dotenv_path_in_cwd}.", Fore.YELLOW)
                    else:
                        colored_print(f"Malformed GOOGLE_API_KEY line in {dotenv_path_in_cwd}: {line}", Fore.YELLOW)
        if not API_KEY:
             colored_print(f"Manual parsing of {dotenv_path_in_cwd} did not result in GOOGLE_API_KEY being set.", Fore.RED)
    except Exception as e_manual:
        colored_print(f"Error during manual parsing of {dotenv_path_in_cwd}: {e_manual}", Fore.RED)

if not API_KEY:
    colored_print("Error: GOOGLE_API_KEY environment variable is not set.", Fore.RED)
    colored_print("Please create a .env file in the current directory with your Google API Key:", Fore.YELLOW)
    colored_print("GOOGLE_API_KEY=your_api_key_here", Fore.CYAN)
    exit(1)

quiet_print("GOOGLE_API_KEY loaded successfully.")

# Configure the generative AI client
genai.configure(api_key=API_KEY)

# --- Agent Configuration ---
# Get model name from environment variable or use default
DEFAULT_MODEL = "gemini-2.5-flash-preview-05-20"
MODEL_NAME = os.getenv("MODEL_NAME", DEFAULT_MODEL)

# Log the model being used
quiet_print(f"Using model: {MODEL_NAME}")

llm = genai.GenerativeModel(MODEL_NAME)

OUTPUT_DIR = Path("output")

def create_llm_spinner(desc: str = "LLM is thinking") -> EnhancedSpinner:
    """Create a spinner for LLM operations"""
    return EnhancedSpinner(desc, style="dots")

def llm_call_with_progress(model, prompt: str, desc: str = "Processing") -> str:
    """Make LLM call with progress indication"""
    spinner = create_llm_spinner(desc)
    
    try:
        # Start spinner in a separate thread-like manner
        import threading
        import queue
        
        result_queue = queue.Queue()
        
        def make_call():
            try:
                response = model.generate_content(prompt)
                result_queue.put(("success", response.text))
            except Exception as e:
                result_queue.put(("error", str(e)))
        
        thread = threading.Thread(target=make_call)
        thread.start()
        
        # Show spinner while waiting
        while thread.is_alive():
            next(spinner)
        
        spinner.stop()
        thread.join()
        
        # Get result
        status, result = result_queue.get()
        if status == "error":
            raise Exception(result)
        
        return result
        
    except Exception as e:
        spinner.stop()
        raise e

def generate_prd(num_questions_str=None, project_name=None, project_description=None, complexity=None, priority=None, interactive=True):
    display_header("Auto-PRDGen", "Product Requirements Document Generator")

    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Non-interactive mode: use provided parameters
    if not interactive and project_name and project_description:
        user_title_idea = project_name
        user_description = project_description
        colored_print(f"Creating PRD for: {user_title_idea}", Fore.GREEN)
        colored_print(f"Description: {user_description}", Fore.CYAN)
    else:
        # Interactive mode: prompt user for input
        # 1. Initial prompt: What do you like to build today?
        colored_print(f"LLM: {INITIAL_PROMPT}", Fore.GREEN)
        user_title_idea = get_user_input("You: ", "project_titles")

        if not user_title_idea.strip():
            colored_print("No input received. Exiting.", Fore.RED)
            return

        # 2. Get user's description
        formatted_description_prompt = DESCRIPTION_PROMPT.format(user_title_idea=user_title_idea)
        colored_print(f"LLM: {formatted_description_prompt}", Fore.GREEN)
        user_description = get_user_input("You: ", "project_descriptions")

        if not user_description.strip():
            colored_print("No description provided. Exiting.", Fore.RED)
            return

    colored_print(f"LLM: {PROCESSING_PROMPT}", Fore.GREEN)

    # 3. LLM processes title and description, then asks 3-5 questions
    model = genai.GenerativeModel(MODEL_NAME)

    # Determine num_questions_descriptor
    if num_questions_str:
        if '-' in num_questions_str:
            try:
                low, high = map(int, num_questions_str.split('-'))
                if low > 0 and high > 0 and low <= high:
                    num_questions_descriptor = f"{low} to {high}"
                else:
                    print_info(f"Invalid range for --num-questions: '{num_questions_str}'. Using default '3 to 5'.")
                    num_questions_descriptor = "3 to 5"
            except ValueError:
                print_info(f"Invalid format for --num-questions: '{num_questions_str}'. Using default '3 to 5'.")
                num_questions_descriptor = "3 to 5"
        elif num_questions_str.isdigit() and int(num_questions_str) > 0:
            num_questions_descriptor = f"exactly {num_questions_str}"
        else:
            print_info(f"Invalid value for --num-questions: '{num_questions_str}'. Using default '3 to 5'.")
            num_questions_descriptor = "3 to 5"
    else:
        num_questions_descriptor = "3 to 5" # Default

    question_generation_prompt = QUESTION_GENERATION_PROMPT.format(
        num_questions_descriptor=num_questions_descriptor,
        user_title_idea=user_title_idea,
        user_description=user_description
    )

    try:
        clarifying_questions_text = llm_call_with_progress(
            model,
            question_generation_prompt,
            "Generating clarifying questions"
        )
    except Exception as e:
        colored_print(f"Error generating clarifying questions: {e}", Fore.RED)
        return

    clarifying_questions = [q.strip() for q in clarifying_questions_text.split('\n') if q.strip() and not q.strip().startswith("Questions:")]

    # 4. User replies to questions (or skip in non-interactive mode)
    user_answers = []
    if interactive:
        colored_print(f"\n{ANSWER_QUESTIONS_PROMPT}", Fore.CYAN)
        for i, question in enumerate(clarifying_questions):
            if not question: continue
            colored_print(f"LLM Q{i+1}: {question}", Fore.GREEN)
            answer = get_user_input("You: ", "question_answers")
            user_answers.append({"question": question, "answer": answer})
    else:
        # In non-interactive mode, provide default answers based on project parameters
        colored_print("Using default answers for clarifying questions...", Fore.CYAN)
        for i, question in enumerate(clarifying_questions):
            if not question: continue
            default_answer = f"Please infer appropriate details based on the project description. Complexity: {complexity or 'medium'}, Priority: {priority or 'medium'}"
            user_answers.append({"question": question, "answer": default_answer})

    colored_print(f"\nLLM: {THANK_YOU_PROMPT}\n", Fore.GREEN)

    # 5. LLM generates the full PRD
    # Format user answers for the prompt
    formatted_user_answers = ""
    for qa in user_answers:
        formatted_user_answers += f"- Question: {qa['question']}\n  Answer: {qa['answer']}\n"
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    prd_generation_prompt = PRD_GENERATION_PROMPT.format(
        user_title_idea=user_title_idea,
        user_description=user_description,
        user_answers=formatted_user_answers,
        current_date=current_date
    )

    try:
        final_prd = llm_call_with_progress(
            model,
            prd_generation_prompt,
            "Generating Product Requirements Document"
        )
    except Exception as e:
        colored_print(f"Error generating PRD: {e}", Fore.RED)
        return

    # Generate a unique filename
    safe_title = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in user_title_idea[:50]).rstrip()
    safe_title = safe_title.replace(' ', '_')
    unique_id = str(uuid.uuid4()).split('-')[0]
    
    # Create project directory inside output directory
    project_dir = OUTPUT_DIR / safe_title
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the PRD to the project directory
    prd_filepath = project_dir / "PRD.md"
    try:
        with open(prd_filepath, "w", encoding="utf-8") as f:
            f.write(final_prd)
        display_header("Success!", "Product Requirements Document Generated")
        colored_print(f"Successfully saved PRD to: {prd_filepath.resolve()}", Fore.GREEN)

        # Generate and save the .mdc file for LLM context
        try:
            mdc_file_path = project_dir / "llm_context.mdc"
            tasks_json_path = project_dir / "tasks.json"
            mdc_content = MDC_FILE_TEMPLATE.format(
                project_name=safe_title,
                project_root_path=project_dir.resolve(),
                project_prd_path=prd_filepath.resolve(),
                project_tasks_path=tasks_json_path.resolve()
            )
            with open(mdc_file_path, 'w', encoding='utf-8') as f_mdc:
                f_mdc.write(mdc_content)
            colored_print(f"LLM context guide saved to: {mdc_file_path.resolve()}", Fore.GREEN)
        except Exception as e_mdc:
            colored_print(f"Warning: Could not create .mdc file: {e_mdc}", Fore.YELLOW)
        colored_print("---------------------------------------------", Fore.GREEN)
    except IOError as e:
        colored_print(f"Error saving PRD to file: {e}", Fore.RED)
        display_header("Generated PRD", "Displaying in terminal due to save error", Fore.YELLOW)
        stream_print(final_prd)
        colored_print("---------------------------------------------", Fore.YELLOW)

def handle_prd_init(args):
    # Check if non-interactive parameters are provided
    project_name = getattr(args, 'project_name', None)
    project_description = getattr(args, 'project_description', None) 
    complexity = getattr(args, 'complexity', None)
    priority = getattr(args, 'priority', None)
    
    # Determine if we should run in interactive mode
    interactive = not (project_name and project_description)
    
    generate_prd(
        num_questions_str=args.num_questions if hasattr(args, 'num_questions') else None,
        project_name=project_name,
        project_description=project_description,
        complexity=complexity,
        priority=priority,
        interactive=interactive
    )

def handle_task_update(args):
    display_header("Task Update", "Update task status and details")
    colored_print(TASK_UPDATE_START, Fore.CYAN)
    
    # Get non-interactive parameters
    project_name = getattr(args, 'project_name', None)
    task_id_arg = getattr(args, 'task_id', None)
    new_status = getattr(args, 'status', None)
    new_priority = getattr(args, 'priority', None)
    new_description = getattr(args, 'description', None)
    new_details = getattr(args, 'details', None)
    
    # Select project and load tasks
    project_dir, tasks_data = select_project_and_load_tasks(project_name)
    if not project_dir or not tasks_data:
        return
    
    tasks = tasks_data.get('tasks', [])
    if not tasks:
        colored_print("No tasks found in the selected project.", Fore.RED)
        return
    
    # Display current tasks
    colored_print("\nCurrent Tasks:", Fore.GREEN)
    for task in tasks:
        status_color = Fore.GREEN if task['status'] == 'completed' else Fore.YELLOW if task['status'] == 'in-progress' else Fore.WHITE
        colored_print(f"  {task['id']}. {task['title']} [{task['status']}] - Priority: {task['priority']}", status_color)
    
    # Get task ID to update
    if task_id_arg is not None:
        # Non-interactive mode
        task_id = task_id_arg
        task_to_update = next((task for task in tasks if task['id'] == task_id), None)
        
        if not task_to_update:
            colored_print(f"Task ID {task_id} not found.", Fore.RED)
            return
    else:
        # Interactive mode
        try:
            task_id = int(get_user_input("\nEnter task ID to update: ", "task_ids"))
            task_to_update = next((task for task in tasks if task['id'] == task_id), None)
            
            if not task_to_update:
                colored_print(INVALID_TASK_ID, Fore.RED)
                return
        except ValueError:
            colored_print(INVALID_TASK_ID, Fore.RED)
            return
    
    # Update task fields
    colored_print(f"\nUpdating Task: {task_to_update['title']}", Fore.CYAN)
    
    if task_id_arg is not None:
        # Non-interactive mode: use provided parameters
        if new_status:
            task_to_update['status'] = new_status
            colored_print(f"Status updated to: {new_status}", Fore.GREEN)
        
        if new_priority:
            task_to_update['priority'] = new_priority
            colored_print(f"Priority updated to: {new_priority}", Fore.GREEN)
        
        if new_description:
            task_to_update['description'] = new_description
            colored_print(f"Description updated", Fore.GREEN)
        
        if new_details:
            task_to_update['details'] = new_details
            colored_print(f"Details updated", Fore.GREEN)
    else:
        # Interactive mode: prompt user for updates
        # Update status
        colored_print(f"Current status: {task_to_update['status']}", Fore.WHITE)
        new_status_index, _ = select_from_list(TASK_STATUS_OPTIONS, "Select new status (or press Enter to keep current)")
        if new_status_index is not None:
            task_to_update['status'] = TASK_STATUS_OPTIONS[new_status_index]
        
        # Update priority
        colored_print(f"Current priority: {task_to_update['priority']}", Fore.WHITE)
        new_priority_index, _ = select_from_list(TASK_PRIORITY_OPTIONS, "Select new priority (or press Enter to keep current)")
        if new_priority_index is not None:
            task_to_update['priority'] = TASK_PRIORITY_OPTIONS[new_priority_index]
        
        # Update description
        colored_print(f"Current description: {task_to_update['description']}", Fore.WHITE)
        new_description = get_user_input("Enter new description (or press Enter to keep current): ", "task_descriptions")
        if new_description.strip():
            task_to_update['description'] = new_description
        
        # Update details
        colored_print(f"Current details: {task_to_update['details']}", Fore.WHITE)
        new_details = get_user_input("Enter new details (or press Enter to keep current): ", "task_details")
        if new_details.strip():
            task_to_update['details'] = new_details
    
    # Save updated tasks
    tasks_file = project_dir / "tasks.json"
    try:
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, indent=2, ensure_ascii=False)
        colored_print(TASK_UPDATED_SUCCESS.format(task_id=task_id), Fore.GREEN)
    except Exception as e:
        colored_print(f"Error saving updated tasks: {e}", Fore.RED)

def handle_task_view(args):
    display_header("Task Viewer", "Display tasks with filtering options")
    colored_print(TASK_VIEW_START, Fore.CYAN)
    
    # Get non-interactive parameters
    project_name = getattr(args, 'project_name', None)
    filter_by = getattr(args, 'filter', None)  # 'all', 'status', 'priority', 'pending', 'completed'
    status_filter = getattr(args, 'status', None)
    priority_filter = getattr(args, 'priority', None)
    
    # Select project and load tasks
    project_dir, tasks_data = select_project_and_load_tasks(project_name)
    if not project_dir or not tasks_data:
        return
    
    tasks = tasks_data.get('tasks', [])
    if not tasks:
        colored_print("No tasks found in the selected project.", Fore.RED)
        return
    
    # Apply filters
    filtered_tasks = tasks
    
    if filter_by:
        # Non-interactive mode
        if filter_by == 'status' and status_filter:
            filtered_tasks = [task for task in tasks if task['status'] == status_filter]
            colored_print(f"Filtering by status: {status_filter}", Fore.CYAN)
        elif filter_by == 'priority' and priority_filter:
            filtered_tasks = [task for task in tasks if task['priority'] == priority_filter]
            colored_print(f"Filtering by priority: {priority_filter}", Fore.CYAN)
        elif filter_by == 'pending':
            filtered_tasks = [task for task in tasks if task['status'] == 'pending']
            colored_print("Showing pending tasks only", Fore.CYAN)
        elif filter_by == 'completed':
            filtered_tasks = [task for task in tasks if task['status'] == 'completed']
            colored_print("Showing completed tasks only", Fore.CYAN)
        elif filter_by == 'all':
            filtered_tasks = tasks
            colored_print("Showing all tasks", Fore.CYAN)
    else:
        # Interactive mode
        # Filter options
        filter_options = ["All tasks", "By status", "By priority", "Pending only", "Completed only"]
        filter_index, _ = select_from_list(filter_options, "Select filter option")
        
        if filter_index == 1:  # By status
            status_index, _ = select_from_list(TASK_STATUS_OPTIONS, "Select status to filter by")
            if status_index is not None:
                filtered_tasks = [task for task in tasks if task['status'] == TASK_STATUS_OPTIONS[status_index]]
        elif filter_index == 2:  # By priority
            priority_index, _ = select_from_list(TASK_PRIORITY_OPTIONS, "Select priority to filter by")
            if priority_index is not None:
                filtered_tasks = [task for task in tasks if task['priority'] == TASK_PRIORITY_OPTIONS[priority_index]]
        elif filter_index == 3:  # Pending only
            filtered_tasks = [task for task in tasks if task['status'] == 'pending']
        elif filter_index == 4:  # Completed only
            filtered_tasks = [task for task in tasks if task['status'] == 'completed']
    
    # Display filtered tasks
    if not filtered_tasks:
        colored_print("No tasks match the selected filter.", Fore.YELLOW)
        return
    
    colored_print(f"\nDisplaying {len(filtered_tasks)} task(s):", Fore.GREEN)
    for task in filtered_tasks:
        status_color = Fore.GREEN if task['status'] == 'completed' else Fore.YELLOW if task['status'] == 'in-progress' else Fore.WHITE
        colored_print(f"\n--- Task {task['id']} ---", Fore.CYAN)
        colored_print(f"Title: {task['title']}", Fore.WHITE)
        colored_print(f"Status: {task['status']}", status_color)
        colored_print(f"Priority: {task['priority']}", Fore.WHITE)
        colored_print(f"Description: {task['description']}", Fore.WHITE)
        if task.get('dependencies'):
            colored_print(f"Dependencies: {', '.join(map(str, task['dependencies']))}", Fore.WHITE)
        colored_print(f"Details: {task['details']}", Fore.WHITE)
        colored_print(f"Test Strategy: {task['testStrategy']}", Fore.WHITE)

def handle_task_export(args):
    display_header("Task Export", "Export tasks to project management tools")
    colored_print(TASK_EXPORT_START, Fore.CYAN)
    
    # Get non-interactive parameters
    project_name = getattr(args, 'project_name', None)
    export_format_arg = getattr(args, 'format', None)
    
    # Select project and load tasks
    project_dir, tasks_data = select_project_and_load_tasks(project_name)
    if not project_dir or not tasks_data:
        return
    
    tasks = tasks_data.get('tasks', [])
    if not tasks:
        colored_print("No tasks found in the selected project.", Fore.RED)
        return
    
    # Determine export format
    export_format = None
    export_options = ["Jira", "Trello", "GitHub Issues"]
    
    if export_format_arg:
        # Non-interactive mode
        # Handle case-insensitive matching
        for option in export_options:
            if option.lower() == export_format_arg.lower() or option.lower().replace(' ', '') == export_format_arg.lower():
                export_format = option
                break
        
        if not export_format:
            colored_print(f"Invalid export format: {export_format_arg}", Fore.RED)
            colored_print(f"Available formats: {', '.join(export_options)}", Fore.YELLOW)
            return
        
        colored_print(f"Exporting to format: {export_format}", Fore.CYAN)
    else:
        # Interactive mode
        export_index, _ = select_from_list(export_options, "Select export format")
        
        if export_index is None:
            colored_print("No export format selected.", Fore.YELLOW)
            return
        
        export_format = export_options[export_index]
    
    try:
        # Generate export content
        export_content = ""
        
        for task in tasks:
            deps_str = ", ".join(map(str, task.get('dependencies', [])))
            
            if export_format == "Jira":
                export_content += JIRA_EXPORT_TEMPLATE.format(
                    title=task['title'],
                    description=task['description'],
                    priority=task['priority'],
                    status=task['status'],
                    details=task['details'],
                    testStrategy=task['testStrategy'],
                    dependencies=deps_str
                )
            elif export_format == "Trello":
                export_content += TRELLO_EXPORT_TEMPLATE.format(
                    title=task['title'],
                    description=task['description'],
                    priority=task['priority'],
                    status=task['status'],
                    details=task['details'],
                    testStrategy=task['testStrategy'],
                    dependencies=deps_str
                )
            elif export_format == "GitHub Issues":
                export_content += GITHUB_ISSUE_TEMPLATE.format(
                    title=task['title'],
                    description=task['description'],
                    priority=task['priority'],
                    status=task['status'],
                    details=task['details'],
                    testStrategy=task['testStrategy'],
                    dependencies=deps_str
                )
        
        # Save export file
        export_filename = f"tasks_export_{export_format.lower().replace(' ', '_')}.txt"
        export_file = project_dir / export_filename
        
        with open(export_file, 'w', encoding='utf-8') as f:
            f.write(export_content)
        
        colored_print(EXPORT_SUCCESS.format(export_format=export_format), Fore.GREEN)
        colored_print(f"Export saved to: {export_file.resolve()}", Fore.GREEN)
        
    except Exception as e:
        colored_print(EXPORT_ERROR.format(error=str(e)), Fore.RED)

def handle_prd_update(args):
    display_header("PRD Update", "Modify existing PRDs")
    colored_print(PRD_UPDATE_START, Fore.CYAN)
    
    # Get non-interactive parameters
    project_name = getattr(args, 'project_name', None)
    modification_request = getattr(args, 'modification_request', None)
    
    # Select project and load PRD
    project_dir, prd_content = select_project_and_load_prd(project_name)
    if not project_dir or not prd_content:
        return
    
    # Get modification request
    if modification_request:
        # Non-interactive mode
        colored_print(f"Updating PRD for project: {project_dir.name}", Fore.GREEN)
        colored_print(f"Modification request: {modification_request}", Fore.CYAN)
    else:
        # Interactive mode
        colored_print("\nCurrent PRD loaded successfully.", Fore.GREEN)
        modification_request = get_user_input("\nDescribe the changes you want to make to the PRD: ", "prd_modifications")
        
        if not modification_request.strip():
            colored_print("No modification request provided. Exiting.", Fore.YELLOW)
            return
    
    # Generate updated PRD using LLM
    model = genai.GenerativeModel(MODEL_NAME)
    update_prompt = PRD_UPDATE_PROMPT.format(
        original_prd=prd_content,
        modification_request=modification_request
    )
    
    try:
        updated_prd = llm_call_with_progress(
            model,
            update_prompt,
            "Updating PRD based on your request"
        )
        
        # Create backup of original PRD
        prd_file = project_dir / "PRD.md"
        backup_file = project_dir / f"PRD_backup_{int(time.time())}.md"
        
        with open(str(backup_file), 'w', encoding='utf-8') as f:
            f.write(prd_content)
        
        # Save updated PRD
        with open(prd_file, "w", encoding="utf-8") as f:
            f.write(updated_prd)
        
        colored_print(f"PRD saved to: {prd_file.resolve()}", Fore.GREEN)
        colored_print(f"Original PRD backed up to: {backup_file.name}", Fore.CYAN)
        colored_print(f"Updated PRD saved to: {str(prd_file.resolve())}", Fore.GREEN)
        
    except Exception as e:
        colored_print(f"Error updating PRD: {e}", Fore.RED)

def handle_prd_compare(args):
    display_header("PRD Compare", "Show differences between PRD versions")
    colored_print(PRD_COMPARE_START, Fore.CYAN)
    
    # Get non-interactive parameters
    project_name = getattr(args, 'project_name', None)
    first_version = getattr(args, 'first_version', None)
    second_version = getattr(args, 'second_version', None)
    
    # Select project
    project_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]
    if not project_dirs:
        colored_print(f"No project directories found in {OUTPUT_DIR}.", Fore.RED)
        return
    
    if project_name:
        # Non-interactive mode: find project by name
        project_dir = None
        for d in project_dirs:
            if d.name == project_name:
                project_dir = d
                break
        
        if not project_dir:
            colored_print(f"Project '{project_name}' not found.", Fore.RED)
            colored_print(f"Available projects: {', '.join([d.name for d in project_dirs])}", Fore.YELLOW)
            return
    else:
        # Interactive mode: let user select
        project_options = [d.name for d in project_dirs]
        project_index, _ = select_from_list(project_options, "Select project to compare PRD versions")
        
        if project_index is None:
            colored_print("No project selected.", Fore.YELLOW)
            return
        
        project_dir = project_dirs[project_index]
    
    # Find PRD files (current and backups)
    prd_files = []
    current_prd = project_dir / "PRD.md"
    if current_prd.exists():
        prd_files.append(("Current PRD", current_prd))
    
    # Find backup files
    backup_files = list(project_dir.glob("PRD_backup_*.md"))
    for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
        timestamp = backup_file.stem.split('_')[-1]
        prd_files.append((f"Backup {timestamp}", backup_file))
    
    if len(prd_files) < 2:
        colored_print(NO_PRD_VERSIONS, Fore.YELLOW)
        return
    
    # If in non-interactive mode but no versions specified, default to current vs latest backup
    if project_name and not (first_version and second_version):
        if len(prd_files) >= 2:
            first_version = "current"
            second_version = "1"  # First backup
            colored_print(f"No versions specified. Comparing current PRD vs latest backup.", Fore.CYAN)
    
    # Select two versions to compare
    if first_version and second_version:
        # Non-interactive mode: find versions by name/type
        file_options = [name for name, _ in prd_files]
        first_index = None
        second_index = None
        
        # Find first version
        if first_version.lower() == 'current':
            first_index = 0 if len(prd_files) > 0 and 'Current' in prd_files[0][0] else None
        else:
            for i, (name, _) in enumerate(prd_files):
                if first_version in name or str(i) == first_version:
                    first_index = i
                    break
        
        # Find second version 
        if second_version.lower() == 'current':
            second_index = 0 if len(prd_files) > 0 and 'Current' in prd_files[0][0] else None
        else:
            for i, (name, _) in enumerate(prd_files):
                if second_version in name or str(i) == second_version:
                    second_index = i
                    break
        
        if first_index is None:
            colored_print(f"First version '{first_version}' not found.", Fore.RED)
            colored_print(f"Available versions: {', '.join(file_options)}", Fore.YELLOW)
            return
            
        if second_index is None:
            colored_print(f"Second version '{second_version}' not found.", Fore.RED)
            colored_print(f"Available versions: {', '.join(file_options)}", Fore.YELLOW)
            return
    else:
        # Interactive mode: let user select versions
        colored_print("\nSelect first PRD version:", Fore.CYAN)
        file_options = [name for name, _ in prd_files]
        first_index, _ = select_from_list(file_options, "Select first version")
        
        if first_index is None:
            return
        
        colored_print("\nSelect second PRD version:", Fore.CYAN)
        second_index, _ = select_from_list(file_options, "Select second version")
        
        if second_index is None:
            return
    
    # Read and compare files
    try:
        with open(prd_files[first_index][1], 'r', encoding='utf-8') as f:
            first_content = f.read()
        
        with open(prd_files[second_index][1], 'r', encoding='utf-8') as f:
            second_content = f.read()
        
        # Simple line-by-line comparison
        first_lines = first_content.splitlines()
        second_lines = second_content.splitlines()
        
        colored_print(f"\nComparing {prd_files[first_index][0]} vs {prd_files[second_index][0]}:", Fore.CYAN)
        
        # Basic diff display
        max_lines = max(len(first_lines), len(second_lines))
        differences_found = False
        
        for i in range(max_lines):
            first_line = first_lines[i] if i < len(first_lines) else ""
            second_line = second_lines[i] if i < len(second_lines) else ""
            
            if first_line != second_line:
                if not differences_found:
                    colored_print("\nDifferences found:", Fore.YELLOW)
                    differences_found = True
                
                colored_print(f"Line {i+1}:", Fore.WHITE)
                colored_print(f"  - {first_line}", Fore.RED)
                colored_print(f"  + {second_line}", Fore.GREEN)
        
        if not differences_found:
            colored_print("\nNo differences found between the selected versions.", Fore.GREEN)
        
    except Exception as e:
        colored_print(f"Error comparing PRD versions: {e}", Fore.RED)

def handle_prd_validate(args):
    display_header("PRD Validation", "Check PRD completeness and quality")
    colored_print(PRD_VALIDATE_START, Fore.CYAN)
    
    # Get non-interactive parameters
    project_name = getattr(args, 'project_name', None)
    
    # Select project and load PRD
    project_dir, prd_content = select_project_and_load_prd(project_name)
    if not project_dir or not prd_content:
        return
    
    # Generate validation report using LLM
    model = genai.GenerativeModel(MODEL_NAME)
    validation_prompt = PRD_VALIDATION_PROMPT.format(prd_content=prd_content)
    
    try:
        validation_report = llm_call_with_progress(
            model,
            validation_prompt,
            "Analyzing PRD for completeness and quality"
        )
        

        
        # Save validation report
        report_file = project_dir / f"prd_validation_report_{int(time.time())}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# PRD Validation Report\n\n{validation_report}")
        
        colored_print(PRD_VALIDATION_COMPLETE, Fore.GREEN)
        colored_print(f"Validation report saved to: {report_file.resolve()}", Fore.GREEN)
        
    except Exception as e:
        colored_print(f"Error validating PRD: {e}", Fore.RED)

def select_project_and_load_tasks(project_name=None):
    """Helper function to select a project and load its tasks.json file"""
    project_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]
    if not project_dirs:
        colored_print(f"No project directories found in {OUTPUT_DIR}.", Fore.RED)
        return None, None
    
    if project_name:
        # Non-interactive mode: find project by name
        project_dir = None
        for d in project_dirs:
            if d.name == project_name:
                project_dir = d
                break
        
        if not project_dir:
            colored_print(f"Project '{project_name}' not found.", Fore.RED)
            colored_print(f"Available projects: {', '.join([d.name for d in project_dirs])}", Fore.YELLOW)
            return None, None
    else:
        # Interactive mode: let user select
        project_options = [d.name for d in project_dirs]
        project_index, _ = select_from_list(project_options, "Select project")
        
        if project_index is None:
            colored_print("No project selected.", Fore.YELLOW)
            return None, None
        
        project_dir = project_dirs[project_index]
    
    tasks_file = project_dir / "tasks.json"
    
    if not tasks_file.exists():
        colored_print(NO_TASKS_FOUND, Fore.RED)
        return None, None
    
    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
        return project_dir, tasks_data
    except Exception as e:
        colored_print(f"Error loading tasks: {e}", Fore.RED)
        return None, None

def select_project_and_load_prd(project_name=None):
    """Helper function to select a project and load its PRD.md file"""
    project_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]
    if not project_dirs:
        colored_print(f"No project directories found in {OUTPUT_DIR}.", Fore.RED)
        return None, None
    
    # Filter projects that have PRD files
    projects_with_prd = []
    for project_dir in project_dirs:
        prd_file = project_dir / "PRD.md"
        if prd_file.exists():
            projects_with_prd.append(project_dir)
    
    if not projects_with_prd:
        colored_print("No projects with PRD files found.", Fore.RED)
        return None, None
    
    if project_name:
        # Non-interactive mode: find project by name
        project_dir = None
        for d in projects_with_prd:
            if d.name == project_name:
                project_dir = d
                break
        
        if not project_dir:
            colored_print(f"Project '{project_name}' not found or has no PRD.", Fore.RED)
            colored_print(f"Available projects with PRDs: {', '.join([d.name for d in projects_with_prd])}", Fore.YELLOW)
            return None, None
    else:
        # Interactive mode: let user select
        project_options = [d.name for d in projects_with_prd]
        project_index, _ = select_from_list(project_options, "Select project")
        
        if project_index is None:
            colored_print("No project selected.", Fore.YELLOW)
            return None, None
        
        project_dir = projects_with_prd[project_index]
    
    prd_file = project_dir / "PRD.md"
    
    try:
        with open(str(prd_file), 'r', encoding='utf-8') as f:
            prd_content = f.read()
        return project_dir, prd_content
    except Exception as e:
        colored_print(f"Error loading PRD: {e}", Fore.RED)
        return None, None

def handle_task_init(args):
    display_header("Task Generator", "Generate development tasks from PRD")
    colored_print(TASK_INIT_START, Fore.CYAN)

    # Get non-interactive parameters 
    project_name = getattr(args, 'project_name', None)

    # 1. List project directories in the output directory
    project_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]

    if not project_dirs:
        colored_print(f"No project directories found in {OUTPUT_DIR}. Please generate a PRD first.", Fore.RED)
        return

    # Find PRD files in project directories
    prd_files = []
    project_dirs_map = {}
    
    for project_dir in project_dirs:
        prd_file = project_dir / "PRD.md"
        if prd_file.exists():
            prd_files.append(prd_file)
            project_dirs_map[prd_file] = project_dir

    if not prd_files:
        colored_print(NO_PRD_FILES.format(output_dir=OUTPUT_DIR), Fore.RED)
        colored_print(GENERATE_PRD_FIRST, Fore.YELLOW)
        return

    if project_name:
        # Non-interactive mode: find project by name
        selected_prd_file = None
        selected_project_dir = None
        
        for prd_file in prd_files:
            project_dir = project_dirs_map[prd_file]
            if project_dir.name == project_name:
                selected_prd_file = prd_file
                selected_project_dir = project_dir
                break
        
        if not selected_prd_file:
            colored_print(f"Project '{project_name}' not found or has no PRD.", Fore.RED)
            available_projects = [project_dirs_map[prd_file].name for prd_file in prd_files]
            colored_print(f"Available projects with PRDs: {', '.join(available_projects)}", Fore.YELLOW)
            return
        
        colored_print(f"Using PRD from project: {selected_project_dir.name}", Fore.GREEN)
    else:
        # Interactive mode: let user select
        colored_print(FOUND_PRD_FILES, Fore.GREEN)
        
        # Create options for selection
        prd_options = [f"{project_dirs_map[prd_file].name} / {prd_file.name}" for prd_file in prd_files]
        
        # 2. User selects a PRD
        selected_index, selected_option = select_from_list(prd_options, "Select a PRD file")
        if selected_index is None:
            colored_print("No PRD selected. Exiting.", Fore.YELLOW)
            return
            
        selected_prd_file = prd_files[selected_index]
        selected_project_dir = project_dirs_map[selected_prd_file]
        colored_print(PRD_SELECTED.format(prd_file_name=selected_prd_file.name), Fore.GREEN)

    # 3. Read the selected PRD file
    try:
        prd_content = selected_prd_file.read_text(encoding='utf-8')
        colored_print(PRD_READ_SUCCESS.format(prd_file_name=selected_prd_file.name), Fore.GREEN)
    except Exception as e:
        colored_print(f"Error reading PRD file '{selected_prd_file.name}': {e}", Fore.RED)
        return

    colored_print(f"\nLLM: {PROCESSING_PRD}", Fore.GREEN)

    # 4. LLM processes PRD and generates tasks
    model = genai.GenerativeModel(MODEL_NAME)
    if args.level == 'simple':
        granularity_instructions = "Generate 5-7 high-level tasks or epics suitable for a project roadmap."
    else:
        granularity_instructions = "Generate a comprehensive, granular list of all necessary development tasks (typically 15-30)."

    task_generation_prompt = TASK_GENERATION_PROMPT.format(
        prd_content=prd_content,
        granularity_instructions=granularity_instructions
    )

    try:
        generated_tasks_json_str = llm_call_with_progress(
            model,
            task_generation_prompt,
            "Generating development tasks"
        )
        
        # Attempt to parse the generated JSON
        try:
            # Clean up the JSON string by removing markdown code block markers if present
            cleaned_json_str = generated_tasks_json_str
            # Remove ```json or ``` at the beginning
            if cleaned_json_str.strip().startswith('```'):
                cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[1:])
            # Remove ``` at the end
            if cleaned_json_str.strip().endswith('```'):
                cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[:-1])
            # Strip any leading/trailing whitespace
            cleaned_json_str = cleaned_json_str.strip()
            
            tasks_data = json.loads(cleaned_json_str)
            colored_print(PARSED_TASKS_SUCCESS, Fore.GREEN)

            # 5. Save the generated tasks to a JSON file in the project directory
            output_tasks_filename = selected_project_dir / "tasks.json"
            with open(output_tasks_filename, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
            colored_print(TASKS_SAVED.format(output_tasks_filename=output_tasks_filename), Fore.GREEN)

            # 6. Convert tasks to individual .md files
            colored_print(f"\n{CONVERTING_TASKS}", Fore.CYAN)
            tasks_dir = selected_project_dir / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            
            # Create progress bar for task conversion
            total_tasks = len(tasks_data.get("tasks", []))
            progress = ProgressBar(total=total_tasks, desc="Converting tasks to markdown files")

            for i, task in enumerate(tasks_data.get("tasks", [])):
                task_id = task.get("id", "unknown")
                task_title = task.get("title", "Untitled Task").replace(" ", "_").replace("/", "_") # Sanitize for filename
                task_filename = tasks_dir / f"task_{task_id}_{task_title}.md"

                dependencies = ", ".join(map(str, task.get("dependencies", [])))

                task_md_content = f"""
# Task ID: {task.get("id", "unknown")}
# Title: {task.get("title", "Untitled Task")}
# Status: {task.get("status", "pending")}
# Dependencies: {dependencies}
# Priority: {task.get("priority", "medium")}
# Description: {task.get("description", "No description provided.")}
# Details:
{task.get("details", "No detailed implementation notes.")}

# Test Strategy:
{task.get("testStrategy", "No test strategy provided.")}
"""
                with open(task_filename, 'w', encoding='utf-8') as f:
                    f.write(task_md_content)
                
                # Update progress bar
                progress.set_progress(i + 1)
                
            progress.finish()
            colored_print(ALL_TASKS_CONVERTED.format(tasks_dir=tasks_dir), Fore.GREEN)

        except json.JSONDecodeError as e:
            colored_print(f"Error: LLM did not return valid JSON. Please try again. Details: {e}", Fore.RED)
            display_header("Raw LLM Output", "Problematic JSON")
            stream_print(generated_tasks_json_str) # Print raw JSON for debugging if parsing fails
            colored_print("--------------------------------------", Fore.YELLOW)
        except Exception as e:
            colored_print(f"An unexpected error occurred during task processing: {e}", Fore.RED)
            display_header("Raw LLM Output", "During Unexpected Error")
            stream_print(generated_tasks_json_str) # Print raw JSON for debugging if other error occurs
            colored_print("---------------------------------------------", Fore.YELLOW)

    except Exception as e:
        colored_print(f"Error generating tasks from LLM: {e}", Fore.RED)
        return

# Priority 1 Enhancement Functions

def handle_task_next(args):
    """Find and recommend the next available task to work on based on dependencies"""
    display_header("Task Next", "Find next available task")
    colored_print(TASK_NEXT_START, Fore.CYAN)
    
    # Get non-interactive parameters
    project_name = getattr(args, 'project_name', None)
    
    # Select project and load tasks
    project_dir, tasks_data = select_project_and_load_tasks(project_name)
    if not project_dir or not tasks_data:
        return
    
    tasks = tasks_data.get("tasks", [])
    if not tasks:
        colored_print("No tasks found in the project.", Fore.YELLOW)
        return
    
    # Find all available tasks
    available_tasks = find_next_available_task(tasks)

    if not available_tasks:
        colored_print(NO_AVAILABLE_TASKS, Fore.YELLOW)
        return

    if len(available_tasks) == 1:
        next_task = available_tasks[0]
        colored_print(NEXT_TASK_FOUND, Fore.GREEN)
        display_task_details(next_task)
    else:
        colored_print(f"Found {len(available_tasks)} available tasks. Asking AI for prioritization...", Fore.CYAN)
        
        # Prepare summary for AI
        tasks_summary_for_ai = ""
        for task in available_tasks:
            tasks_summary_for_ai += f"- ID: {task.get('id')}, Title: {task.get('title')}, Priority: {task.get('priority', 'medium')}, Description: {task.get('description', '')[:100]}...\n"
        
        model = genai.GenerativeModel(MODEL_NAME)
        ai_prompt = AI_TASK_PRIORITIZATION_PROMPT.format(available_tasks_summary=tasks_summary_for_ai)
        
        try:
            response_json_str = llm_call_with_progress(
                model,
                ai_prompt,
                "AI is prioritizing tasks"
            )
            # Clean up the JSON string
            cleaned_json_str = response_json_str
            if cleaned_json_str.strip().startswith('```json'):
                cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[1:])
            if cleaned_json_str.strip().startswith('```'): # Handle if only ``` is present
                cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[1:])
            if cleaned_json_str.strip().endswith('```'):
                cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[:-1])
            cleaned_json_str = cleaned_json_str.strip()

            ai_recommendation = json.loads(cleaned_json_str)
            recommended_task_id = ai_recommendation.get("recommended_task_id")
            justification = ai_recommendation.get("justification")

            recommended_task = next((task for task in available_tasks if task.get('id') == recommended_task_id), None)

            if recommended_task:
                colored_print("\nAI Recommendation for the next task:", Fore.GREEN)
                display_task_details(recommended_task)
                colored_print(f"\nAI Justification: {justification}", Fore.CYAN)
            else:
                colored_print(f"AI recommended task ID {recommended_task_id}, but it was not found in the available tasks. Defaulting to the highest priority task.", Fore.YELLOW)
                display_task_details(available_tasks[0]) # Default to first in sorted list

        except json.JSONDecodeError as e:
            colored_print(f"Error parsing AI response: {e}. Raw response: {response_json_str}", Fore.RED)
            colored_print("Defaulting to the highest priority task.", Fore.YELLOW)
            display_task_details(available_tasks[0]) # Default to first in sorted list
        except Exception as e:
            colored_print(f"Error during AI task prioritization: {e}", Fore.RED)
            colored_print("Defaulting to the highest priority task.", Fore.YELLOW)
            display_task_details(available_tasks[0]) # Default to first in sorted list

def find_next_available_task(tasks):
    """Find the next task that can be worked on (no pending dependencies)"""
    # Create a map of task IDs to tasks for quick lookup
    task_map = {task['id']: task for task in tasks}
    
    # Find tasks that are pending and have no pending dependencies
    available_tasks = []
    
    for task in tasks:
        if task.get('status') == 'pending':
            # Check if all dependencies are completed
            dependencies = task.get('dependencies', [])
            all_deps_completed = True
            
            for dep_id in dependencies:
                dep_task = task_map.get(dep_id)
                if not dep_task or dep_task.get('status') != 'completed':
                    all_deps_completed = False
                    break
            
            if all_deps_completed:
                available_tasks.append(task)
    
    # Sort by priority (high > medium > low) and then by ID
    priority_order = {'high': 3, 'medium': 2, 'low': 1}
    available_tasks.sort(key=lambda t: (priority_order.get(t.get('priority', 'medium'), 2), t.get('id', 0)), reverse=True)
    
    return available_tasks

def display_task_details(task):
    """Display detailed information about a task"""
    colored_print(f"\nTask #{task.get('id')}: {task.get('title', 'Untitled')}", Fore.WHITE, style=Style.BRIGHT)
    colored_print(f"Status: {task.get('status', 'unknown')}", Fore.CYAN)
    colored_print(f"Priority: {task.get('priority', 'medium')}", Fore.CYAN)
    
    dependencies = task.get('dependencies', [])
    if dependencies:
        colored_print(f"Dependencies: {', '.join(map(str, dependencies))}", Fore.CYAN)
    else:
        colored_print("Dependencies: None", Fore.CYAN)
    
    colored_print(f"\nDescription:", Fore.YELLOW)
    colored_print(task.get('description', 'No description'), Fore.WHITE)
    
    if task.get('details'):
        colored_print(f"\nDetails:", Fore.YELLOW)
        colored_print(task.get('details'), Fore.WHITE)
    
    if task.get('testStrategy'):
        colored_print(f"\nTest Strategy:", Fore.YELLOW)
        colored_print(task.get('testStrategy'), Fore.WHITE)

def handle_task_expand(args):
    """Break down a task into subtasks using AI"""
    # Get parameters from args object
    task_id = getattr(args, 'id', None)
    force = getattr(args, 'force', False)
    project_name = getattr(args, 'project_name', None)
    
    if task_id is None:
        colored_print("Error: Task ID is required. Use --id parameter.", Fore.RED)
        return
    
    display_header("Task Expand", f"Break down Task #{task_id}")
    colored_print(TASK_EXPAND_START, Fore.CYAN)
    
    # Select project and load tasks
    project_dir, tasks_data = select_project_and_load_tasks(project_name)
    if not project_dir or not tasks_data:
        return
    
    tasks = tasks_data.get("tasks", [])
    
    # Find the target task
    target_task = None
    for task in tasks:
        if task.get('id') == task_id:
            target_task = task
            break
    
    if not target_task:
        colored_print(f"Task #{task_id} not found.", Fore.RED)
        return
    
    # Check if task already has subtasks
    if target_task.get('subtasks') and not force:
        colored_print(f"Task #{task_id} already has subtasks. Use --force to regenerate.", Fore.YELLOW)
        return
    
    # Generate subtasks using AI
    model = genai.GenerativeModel(MODEL_NAME)
    expansion_prompt = TASK_EXPANSION_PROMPT.format(
        task_id=task_id,
        task_title=target_task.get('title', ''),
        task_description=target_task.get('description', ''),
        task_details=target_task.get('details', '')
    )
    
    try:
        subtasks_json_str = llm_call_with_progress(
            model,
            expansion_prompt,
            f"Generating subtasks for Task #{task_id}"
        )
        
        # Parse the generated JSON
        try:
            # Clean up JSON string
            cleaned_json_str = subtasks_json_str.strip()
            if cleaned_json_str.startswith('```'):
                cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[1:])
            if cleaned_json_str.endswith('```'):
                cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[:-1])
            cleaned_json_str = cleaned_json_str.strip()
            
            subtasks_data = json.loads(cleaned_json_str)
            subtasks = subtasks_data.get('subtasks', [])
            
            # Add subtasks to the target task
            target_task['subtasks'] = subtasks
            
            # Save updated tasks
            tasks_file = project_dir / "tasks.json"
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
            
            colored_print(TASK_EXPAND_SUCCESS.format(task_id=task_id, count=len(subtasks)), Fore.GREEN)
            
            # Display generated subtasks
            colored_print(f"\nGenerated Subtasks:", Fore.CYAN)
            subtask_md_lines = ["\n## Subtasks"] # Start with a newline to ensure separation
            for subtask in subtasks:
                colored_print(f"  {subtask.get('id')}: {subtask.get('title')}", Fore.WHITE)
                subtask_md_lines.append(f"- {subtask.get('id')}: {subtask.get('title')}")

            # Update the parent task's individual Markdown file
            parent_task_title_safe = target_task.get('title', 'Untitled Task').replace(" ", "_").replace("/", "_")
            parent_task_md_filename = project_dir / "tasks" / f"task_{target_task.get('id')}_{parent_task_title_safe}.md"

            if parent_task_md_filename.exists():
                try:
                    with open(parent_task_md_filename, 'r+', encoding='utf-8') as f_parent_md:
                        content = f_parent_md.read()
                        # Ensure there's a blank line before appending if not already present
                        if content and not content.endswith('\n\n'):
                            if not content.endswith('\n'):
                                f_parent_md.write('\n')
                            f_parent_md.write('\n') # Add an extra newline for separation
                        
                        f_parent_md.write("\n".join(subtask_md_lines) + "\n")
                    colored_print(f"Updated parent task Markdown file: {parent_task_md_filename}", Fore.GREEN)
                except Exception as e_md:
                    colored_print(f"Error updating parent task Markdown file {parent_task_md_filename}: {e_md}", Fore.YELLOW)
            else:
                colored_print(f"Parent task Markdown file {parent_task_md_filename} not found. Subtasks not added to individual file.", Fore.YELLOW)
            
        except json.JSONDecodeError as e:
            colored_print(f"Error: AI did not return valid JSON. {e}", Fore.RED)
            
    except Exception as e:
        colored_print(f"Error expanding task: {e}", Fore.RED)

def handle_task_dependencies(args):
    """Manage task dependencies"""
    # Get parameters from args object
    add_dep = getattr(args, 'add', False)
    remove_dep = getattr(args, 'remove', False)  
    task_id = getattr(args, 'id', None)
    depends_on = getattr(args, 'depends_on', None)
    validate = getattr(args, 'validate', False)
    project_name = getattr(args, 'project_name', None)
    
    display_header("Task Dependencies", "Manage task relationships")
    
    # Select project and load tasks
    project_dir, tasks_data = select_project_and_load_tasks(project_name)
    if not project_dir or not tasks_data:
        return
    
    tasks = tasks_data.get("tasks", [])
    task_map = {task['id']: task for task in tasks}
    
    if validate:
        validate_all_dependencies(tasks)
        return
    
    if task_id is None:
        colored_print("Error: Task ID is required. Use --id parameter.", Fore.RED)
        return
    
    # Find target task
    target_task = task_map.get(task_id)
    if not target_task:
        colored_print(f"Task #{task_id} not found.", Fore.RED)
        return
    
    if add_dep and depends_on:
        add_task_dependency(target_task, depends_on, task_map, project_dir, tasks_data)
    elif remove_dep and depends_on:
        remove_task_dependency(target_task, depends_on, project_dir, tasks_data)
    else:
        colored_print("Please specify --add or --remove with --depends-on, or use --validate.", Fore.YELLOW)

def add_task_dependency(task, depends_on_id, task_map, project_dir, tasks_data):
    """Add a dependency to a task"""
    task_id = task['id']
    
    # Validation checks
    if task_id == depends_on_id:
        colored_print(SELF_DEPENDENCY_ERROR, Fore.RED)
        return
    
    if depends_on_id not in task_map:
        colored_print(INVALID_DEPENDENCY_ERROR.format(depends_on=depends_on_id), Fore.RED)
        return
    
    # Check for circular dependencies
    if would_create_circular_dependency(task_id, depends_on_id, task_map):
        colored_print(CIRCULAR_DEPENDENCY_ERROR, Fore.RED)
        return
    
    # Add dependency
    dependencies = task.get('dependencies', [])
    if depends_on_id not in dependencies:
        dependencies.append(depends_on_id)
        task['dependencies'] = dependencies
        
        # Save updated tasks
        tasks_file = project_dir / "tasks.json"
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, indent=2, ensure_ascii=False)
        
        colored_print(DEPENDENCY_ADDED.format(task_id=task_id, depends_on=depends_on_id), Fore.GREEN)
    else:
        colored_print(f"Task #{task_id} already depends on Task #{depends_on_id}.", Fore.YELLOW)

def remove_task_dependency(task, depends_on_id, project_dir, tasks_data):
    """Remove a dependency from a task"""
    task_id = task['id']
    dependencies = task.get('dependencies', [])
    
    if depends_on_id in dependencies:
        dependencies.remove(depends_on_id)
        task['dependencies'] = dependencies
        
        # Save updated tasks
        tasks_file = project_dir / "tasks.json"
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, indent=2, ensure_ascii=False)
        
        colored_print(DEPENDENCY_REMOVED.format(task_id=task_id, depends_on=depends_on_id), Fore.GREEN)
    else:
        colored_print(f"Task #{task_id} does not depend on Task #{depends_on_id}.", Fore.YELLOW)

def would_create_circular_dependency(task_id, depends_on_id, task_map):
    """Check if adding a dependency would create a circular dependency"""
    visited = set()
    
    def has_path(from_id, to_id):
        if from_id == to_id:
            return True
        if from_id in visited:
            return False
        
        visited.add(from_id)
        task = task_map.get(from_id)
        if task:
            for dep_id in task.get('dependencies', []):
                if has_path(dep_id, to_id):
                    return True
        return False
    
    # Check if depends_on_id has a path back to task_id
    return has_path(depends_on_id, task_id)

def validate_all_dependencies(tasks):
    """Validate all task dependencies for issues"""
    colored_print(DEPENDENCY_VALIDATION_START, Fore.CYAN)
    
    task_map = {task['id']: task for task in tasks}
    issues = []
    
    for task in tasks:
        task_id = task['id']
        dependencies = task.get('dependencies', [])
        
        for dep_id in dependencies:
            # Check if dependency exists
            if dep_id not in task_map:
                issues.append(f"Task #{task_id} depends on non-existent Task #{dep_id}")
            
            # Check for self-dependency
            if dep_id == task_id:
                issues.append(f"Task #{task_id} depends on itself")
    
    # Check for circular dependencies
    for task in tasks:
        task_id = task['id']
        if would_create_circular_dependency(task_id, task_id, task_map):
            issues.append(f"Circular dependency detected involving Task #{task_id}")
    
    colored_print(DEPENDENCY_VALIDATION_COMPLETE.format(issues=len(issues)), Fore.GREEN)
    
    if issues:
        colored_print("\nIssues found:", Fore.YELLOW)
        for issue in issues:
            colored_print(f"  - {issue}", Fore.RED)
    else:
        colored_print("No dependency issues found.", Fore.GREEN)

def handle_task_complexity(args):
    """Analyze task complexity and provide recommendations"""
    # Get non-interactive parameters
    project_name = getattr(args, 'project_name', None)
    
    display_header("Task Complexity Analysis", "AI-powered complexity assessment")
    colored_print(TASK_COMPLEXITY_START, Fore.CYAN)
    
    # Select project and load tasks
    project_dir, tasks_data = select_project_and_load_tasks(project_name)
    if not project_dir or not tasks_data:
        return
    
    tasks = tasks_data.get("tasks", [])
    
    # Determine which tasks to analyze
    if args.id:
        target_tasks = [task for task in tasks if task.get('id') == args.id]
        if not target_tasks:
            colored_print(f"Task #{args.id} not found.", Fore.RED)
            return
    elif args.all:
        target_tasks = tasks
    else:
        colored_print("Please specify --id <task_id> or --all", Fore.YELLOW)
        return
    
    model = genai.GenerativeModel(MODEL_NAME)
    all_narrative_reports = []
    tasks_updated_count = 0

    for i, task_to_analyze in enumerate(target_tasks):
        task_id = task_to_analyze.get('id')
        colored_print(f"\nProcessing Task #{task_id}: {task_to_analyze.get('title')}", Fore.CYAN)
        colored_print(f"({i+1}/{len(target_tasks)})", Fore.MAGENTA)

        analysis_prompt = SINGLE_TASK_COMPLEXITY_PROMPT.format(
            task_id=task_id,
            task_title=task_to_analyze.get('title', ''),
            task_description=task_to_analyze.get('description', ''),
            task_details=task_to_analyze.get('details', ''),
            task_priority=task_to_analyze.get('priority', 'N/A'),
            task_status=task_to_analyze.get('status', 'N/A'),
            task_dependencies=task_to_analyze.get('dependencies', [])
        )

        try:
            response_json_str = llm_call_with_progress(
                model,
                analysis_prompt,
                f"Analyzing complexity for Task #{task_id}"
            )
            
            # Clean and parse JSON response
            cleaned_json_str = response_json_str.strip()
            if cleaned_json_str.startswith('```json'):
                cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[1:])
            if cleaned_json_str.endswith('```'):
                cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[:-1])
            cleaned_json_str = cleaned_json_str.strip()

            llm_response = json.loads(cleaned_json_str)
            structured_data = llm_response.get('structured_data')
            narrative_report = llm_response.get('narrative_report')

            if structured_data and narrative_report:
                # Update the task in the tasks_data list
                for task_in_memory in tasks_data.get("tasks", []):
                    if task_in_memory.get('id') == task_id:
                        task_in_memory['complexity_score'] = structured_data.get('complexity_score')
                        task_in_memory['complexity_factors'] = structured_data.get('complexity_factors')
                        task_in_memory['estimated_effort'] = structured_data.get('estimated_effort')
                        tasks_updated_count += 1
                        break
                
                all_narrative_reports.append(f"## Task #{task_id}: {task_to_analyze.get('title')}\n\n{narrative_report}\n\n---\n")
                colored_print(f"Successfully analyzed Task #{task_id}.", Fore.GREEN)
            else:
                colored_print(f"Error: LLM response for Task #{task_id} was missing structured_data or narrative_report.", Fore.YELLOW)
                all_narrative_reports.append(f"## Task #{task_id}: {task_to_analyze.get('title')}\n\nAnalysis failed or produced incomplete data.\n\n---\n")

        except json.JSONDecodeError as e_json:
            colored_print(f"Error decoding LLM JSON response for Task #{task_id}: {e_json}", Fore.RED)
            colored_print(f"LLM Raw Output for Task #{task_id}:\n{response_json_str[:500]}...", Fore.YELLOW) # Print first 500 chars of raw output
            all_narrative_reports.append(f"## Task #{task_id}: {task_to_analyze.get('title')}\n\nJSON parsing failed. Raw LLM output might be malformed.\nLLM Raw Output Preview: {response_json_str[:200]}...\n\n---\n")
        except Exception as e_task:
            colored_print(f"Error analyzing Task #{task_id}: {e_task}", Fore.RED)
            all_narrative_reports.append(f"## Task #{task_id}: {task_to_analyze.get('title')}\n\nAn unexpected error occurred during analysis: {e_task}\n\n---\n")

    if not all_narrative_reports:
        colored_print("No tasks were analyzed or no reports generated.", Fore.YELLOW)
        return

    # Save the updated tasks.json
    try:
        tasks_file_path = project_dir / "tasks.json"
        with open(tasks_file_path, 'w', encoding='utf-8') as f_tasks:
            json.dump(tasks_data, f_tasks, indent=2, ensure_ascii=False)
        colored_print(f"\nSuccessfully updated {tasks_updated_count} task(s) in {tasks_file_path.resolve()}", Fore.GREEN)
    except Exception as e_save_json:
        colored_print(f"\nError saving updated tasks.json: {e_save_json}", Fore.RED)

    # Save the consolidated narrative report
    report_filename_suffix = f"task_{args.id}" if args.id else "all_tasks"
    report_file = project_dir / f"task_complexity_report_{report_filename_suffix}_{int(time.time())}.md"
    try:
        with open(report_file, 'w', encoding='utf-8') as f_report:
            f_report.write("# Task Complexity Analysis Report\n\n")
            f_report.write("\n".join(all_narrative_reports))
        colored_print(COMPLEXITY_ANALYSIS_COMPLETE, Fore.GREEN)
        colored_print(f"Consolidated analysis report saved to: {report_file.resolve()}", Fore.GREEN)
    except Exception as e_save_report:
        colored_print(f"Error saving complexity analysis report: {e_save_report}", Fore.RED)

# Priority 2: Advanced Features Implementation

def handle_prd_complexity(args):
    """Analyze PRD complexity and provide recommendations"""
    display_header("PRD Complexity Analysis", "AI-powered PRD complexity assessment")
    colored_print(COMPLEXITY_ANALYSIS_START, Fore.CYAN)
    
    # Get non-interactive parameters
    project_name = getattr(args, 'project_name', None)
    
    # Select project and load PRD content
    project_dir, prd_content = select_project_and_load_prd(project_name)
    if not project_dir or not prd_content:
        return
    
    # Generate complexity analysis using AI
    model = genai.GenerativeModel(MODEL_NAME)
    analysis_prompt = PRD_COMPLEXITY_ANALYSIS_PROMPT.format(prd_content=prd_content)
    
    try:
        complexity_analysis = llm_call_with_progress(
            model,
            analysis_prompt,
            "Analyzing PRD complexity"
        )
        

        
        # Save analysis report
        report_file = project_dir / f"prd_complexity_analysis_{int(time.time())}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# PRD Complexity Analysis\n\n{complexity_analysis}")
        
        colored_print(COMPLEXITY_REPORT_SAVED.format(filename=report_file.resolve()), Fore.GREEN)
        
    except Exception as e:
        colored_print(f"Error analyzing PRD complexity: {e}", Fore.RED)

def handle_natural_language_command(args):
    """Process natural language commands and map them to system commands"""
    import json
    
    # Get parameters from args object
    suggest_only = getattr(args, 'suggest_only', False)
    
    # Handle query argument properly - args.query should be a list due to nargs='+'
    if hasattr(args, 'query') and args.query:
        user_input = ' '.join(args.query)
    else:
        user_input = ""
    
    if not user_input.strip():
        colored_print("No query provided. Please specify a natural language command.", Fore.RED)
        return
    
    display_header("Natural Language Command Processing", "AI-powered command interpretation")
    colored_print(NATURAL_LANGUAGE_PROCESSING, Fore.CYAN)
    
    colored_print(f"Processing: '{user_input}'", Fore.YELLOW)
    
    # Generate command interpretation using AI
    model = genai.GenerativeModel(MODEL_NAME)
    interpretation_prompt = NATURAL_LANGUAGE_COMMAND_PROMPT.format(user_input=user_input)
    
    try:
        interpretation_result = llm_call_with_progress(
            model,
            interpretation_prompt,
            "Interpreting natural language command"
        )
        
        # Parse the JSON response
        try:
            # Clean up the JSON string
            cleaned_json = interpretation_result.strip()
            if cleaned_json.startswith('```json'):
                cleaned_json = '\n'.join(cleaned_json.split('\n')[1:])
            if cleaned_json.endswith('```'):
                cleaned_json = '\n'.join(cleaned_json.split('\n')[:-1])
            cleaned_json = cleaned_json.strip()
            
            result = json.loads(cleaned_json)
            
            colored_print(f"\nIntent: {result.get('intent', 'Unknown')}", Fore.GREEN)
            colored_print(f"Mapped Command: {result.get('command', 'Unknown')}", Fore.GREEN)
            colored_print(f"Confidence: {result.get('confidence', 0)}/10", Fore.GREEN)
            colored_print(f"Explanation: {result.get('explanation', 'No explanation')}", Fore.CYAN)
            
            command = result.get('command')
            parameters = result.get('parameters', {})
            
            if parameters:
                colored_print("Parameters:", Fore.YELLOW)
                for key, value in parameters.items():
                    colored_print(f"  {key}: {value}", Fore.WHITE)
            
            confidence = result.get('confidence', 0)
            if confidence >= 7:
                # Build the command string for display
                cmd_str = command
                if parameters:
                    for key, value in parameters.items():
                        if isinstance(value, bool) and value:
                            cmd_str += f" --{key}"
                        elif not isinstance(value, bool):
                            cmd_str += f" --{key} {value}"
                
                colored_print(COMMAND_INTERPRETED.format(command=cmd_str), Fore.GREEN)
                
                if suggest_only:
                    colored_print(f"\nSuggested command: auto-prdgen {cmd_str}", Fore.CYAN)
                else:
                    colored_print(f"\nCommand interpretation complete: {cmd_str}", Fore.CYAN)
                    colored_print("Note: Use the suggested command directly for execution to avoid recursive calls.", Fore.YELLOW)
                
            else:
                colored_print(COMMAND_UNCLEAR, Fore.YELLOW)
                colored_print("Please try a more specific command or use 'auto-prdgen --help' for available options.", Fore.WHITE)
                
        except json.JSONDecodeError as e:
            colored_print(f"Error parsing AI response: {e}", Fore.RED)
            colored_print("Raw response (first 500 chars):", Fore.YELLOW)
            colored_print(interpretation_result[:500] + "..." if len(interpretation_result) > 500 else interpretation_result, Fore.WHITE)
            
    except Exception as e:
        colored_print(f"Error processing natural language command: {e}", Fore.RED)

def handle_research_backed_tasks(args):
    """Generate research-backed tasks with industry best practices"""
    display_header("Research-Backed Task Generation", "Industry best practices integration")
    colored_print(RESEARCH_BACKED_GENERATION, Fore.CYAN)
    
    # Get non-interactive parameters
    project_name = getattr(args, 'project_name', None)
    
    # Select project and load PRD
    project_dir, prd_content = select_project_and_load_prd(project_name)
    if not project_dir or not prd_content:
        return
    
    # Check if tasks already exist
    tasks_file = project_dir / "tasks.json"
    existing_tasks_data = None
    
    if tasks_file.exists():
        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                existing_tasks_data = json.load(f)
            colored_print(f"Found existing tasks in {tasks_file}. Will enhance them with research-backed information.", Fore.CYAN)
        except Exception as e:
            colored_print(f"Error loading existing tasks: {e}. Will create new tasks.", Fore.YELLOW)
            existing_tasks_data = None
    
    # If --force is used, ignore existing tasks and create from scratch
    if args.force:
        colored_print("--force flag used. Creating new research-backed tasks from scratch.", Fore.YELLOW)
        existing_tasks_data = None
    
    # Generate or enhance tasks using AI
    model = genai.GenerativeModel(MODEL_NAME)
    
    if existing_tasks_data and existing_tasks_data.get('tasks'):
        # Enhance existing tasks with research-backed information
        colored_print(f"Enhancing {len(existing_tasks_data['tasks'])} existing tasks with research-backed information...", Fore.CYAN)
        
        # Convert existing tasks to JSON string for the prompt
        existing_tasks_json = json.dumps(existing_tasks_data, indent=2, ensure_ascii=False)
        
        # Select the enhancement prompt based on the level
        if args.level == 'simple':
            from prompts import SIMPLE_RESEARCH_BACKED_TASK_ENHANCEMENT_PROMPT
            task_enhancement_prompt = SIMPLE_RESEARCH_BACKED_TASK_ENHANCEMENT_PROMPT.format(
                prd_content=prd_content,
                existing_tasks_json=existing_tasks_json
            )
            progress_desc = "Enhancing existing high-level tasks with research-backed information"
        else: # 'detailed'
            from prompts import RESEARCH_BACKED_TASK_ENHANCEMENT_PROMPT
            task_enhancement_prompt = RESEARCH_BACKED_TASK_ENHANCEMENT_PROMPT.format(
                prd_content=prd_content,
                existing_tasks_json=existing_tasks_json
            )
            progress_desc = "Enhancing existing tasks with research-backed information"
        
        try:
            enhanced_tasks_json_str = llm_call_with_progress(
                model,
                task_enhancement_prompt,
                progress_desc
            )
            
            # Parse the enhanced JSON
            try:
                # Clean up the JSON string
                cleaned_json_str = enhanced_tasks_json_str.strip()
                if cleaned_json_str.startswith('```json'):
                    cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[1:])
                if cleaned_json_str.endswith('```'):
                    cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[:-1])
                cleaned_json_str = cleaned_json_str.strip()
                
                enhanced_tasks_data = json.loads(cleaned_json_str)
                colored_print("Successfully enhanced existing tasks with research-backed information.", Fore.GREEN)
                
                # Save the enhanced tasks to the JSON file
                with open(tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(enhanced_tasks_data, f, indent=2, ensure_ascii=False)
                colored_print(f"Enhanced research-backed tasks saved to {tasks_file}", Fore.GREEN)
                
                tasks_data = enhanced_tasks_data
                
            except json.JSONDecodeError as e:
                colored_print(f"Error: AI did not return valid JSON during enhancement. Details: {e}", Fore.RED)
                display_header("Raw AI Output", "Problematic JSON")
                stream_print(enhanced_tasks_json_str)
                return
                
        except Exception as e:
            colored_print(f"Error enhancing existing tasks: {e}", Fore.RED)
            return
    else:
        # No existing tasks found, create new research-backed tasks from scratch
        colored_print("No existing tasks found. Creating new research-backed tasks from scratch...", Fore.CYAN)
        
        # Select the prompt based on the level
        if args.level == 'simple':
            from prompts import SIMPLE_RESEARCH_BACKED_TASK_GENERATION_PROMPT
            task_generation_prompt = SIMPLE_RESEARCH_BACKED_TASK_GENERATION_PROMPT.format(prd_content=prd_content)
            progress_desc = "Generating high-level research-backed epics"
        else: # 'detailed'
            from prompts import RESEARCH_BACKED_TASK_GENERATION_PROMPT
            task_generation_prompt = RESEARCH_BACKED_TASK_GENERATION_PROMPT.format(prd_content=prd_content)
            progress_desc = "Generating detailed research-backed tasks"

        try:
            generated_tasks_json_str = llm_call_with_progress(
                model,
                task_generation_prompt,
                progress_desc
            )
            
            # Parse the generated JSON
            try:
                # Clean up the JSON string
                cleaned_json_str = generated_tasks_json_str.strip()
                if cleaned_json_str.startswith('```json'):
                    cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[1:])
                if cleaned_json_str.endswith('```'):
                    cleaned_json_str = '\n'.join(cleaned_json_str.split('\n')[:-1])
                cleaned_json_str = cleaned_json_str.strip()
                
                tasks_data = json.loads(cleaned_json_str)
                colored_print("Successfully parsed generated research-backed tasks.", Fore.GREEN)
                
                # Save the generated tasks to a JSON file
                with open(tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(tasks_data, f, indent=2, ensure_ascii=False)
                colored_print(f"Research-backed tasks saved to {tasks_file}", Fore.GREEN)
                
            except json.JSONDecodeError as e:
                colored_print(f"Error: AI did not return valid JSON. Details: {e}", Fore.RED)
                display_header("Raw AI Output", "Problematic JSON")
                stream_print(generated_tasks_json_str)
                return
                
        except Exception as e:
            colored_print(f"Error generating research-backed tasks: {e}", Fore.RED)
            return
    
    # Convert tasks to individual .md files (both for enhanced and new tasks)
    colored_print("\nConverting tasks to individual Markdown files...", Fore.CYAN)
    tasks_dir = project_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    
    total_tasks = len(tasks_data.get("tasks", []))
    progress = ProgressBar(total=total_tasks, desc="Converting research-backed tasks")
    
    for i, task in enumerate(tasks_data.get("tasks", [])):
        task_id = task.get("id", "unknown")
        task_title = task.get("title", "Untitled Task").replace(" ", "_").replace("/", "_")
        task_filename = tasks_dir / f"task_{task_id}_{task_title}.md"
        
        dependencies = ", ".join(map(str, task.get("dependencies", [])))
        
        task_md_content = f"""# Task ID: {task.get("id", "unknown")}
# Title: {task.get("title", "Untitled Task")}
# Status: {task.get("status", "pending")}
# Dependencies: {dependencies}
# Priority: {task.get("priority", "medium")}
# Description: {task.get("description", "No description provided.")}

# Details:
{task.get("details", "No detailed implementation notes.")}

# Test Strategy:
{task.get("testStrategy", "No test strategy provided.")}

# Research Justification:
{task.get("researchJustification", "No research justification provided.")}

# Best Practice References:
{task.get("bestPracticeReferences", "No best practice references provided.")}

# Quality Gates:
{task.get("qualityGates", "No quality gates defined.")}

# Risk Mitigation:
{task.get("riskMitigation", "No risk mitigation strategies defined.")}
"""
        
        with open(task_filename, 'w', encoding='utf-8') as f:
            f.write(task_md_content)
        
        progress.set_progress(i + 1)
    
    progress.finish()
    colored_print(RESEARCH_TASKS_GENERATED, Fore.GREEN)
    colored_print(f"All research-backed tasks converted to Markdown files in '{tasks_dir}' directory.", Fore.GREEN)

def main():
    # Configuration is automatically loaded when imported
    
    parser = argparse.ArgumentParser(
        description="Auto-PRDGen: Automate Product Requirement Document generation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:

  PRD Management:
    auto-prdgen prd-init                      # Interactively generate a new PRD
    auto-prdgen prd-init --num-questions 5    # Generate PRD, AI asks up to 5 follow-up questions
    auto-prdgen prd-update                    # Modify an existing PRD
    auto-prdgen prd-compare                   # Show differences between PRD versions
    auto-prdgen prd-validate                  # Check PRD completeness and quality
    auto-prdgen prd-complexity                # Analyze PRD complexity, risks, and resources

  Task Management:
    auto-prdgen task-init                     # Convert PRD to a detailed list of tasks
    auto-prdgen task-init --level simple      # Convert PRD to a high-level list of tasks (epics)
    auto-prdgen task-research                 # Generate detailed research-backed tasks (default)
    auto-prdgen task-research --level detailed  # Explicitly generate detailed research-backed tasks
    auto-prdgen task-research --level simple    # Generate fewer, high-level research-backed epics (all fields populated)
    auto-prdgen task-next                     # Get AI recommendation for the next logical task
    auto-prdgen task-update                   # Update task status, details, etc.
    auto-prdgen task-view                     # Display tasks with filtering options
    auto-prdgen task-expand --id <task_id>    # Use AI to break down a complex task into subtasks
    auto-prdgen task-deps --id <X> --add --depends-on <Y> # Task X depends on Task Y
    auto-prdgen task-complexity --id <task_id>  # Analyze complexity of a specific task
    auto-prdgen task-complexity --all           # Analyze complexity of all tasks
    auto-prdgen task-export                   # Export tasks (Jira, Trello, GitHub Issues)

  Natural Language Interface:
    auto-prdgen nl-command create a new prd   # Execute command via natural language
    auto-prdgen nl-command show me my tasks --suggest-only # Interpret and suggest command

  General:
    auto-prdgen <command> --help              # Show help for a specific command
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # PRD Init Subcommand
    prd_init_parser = subparsers.add_parser(
        "prd-init", 
        help="Initialize a new Product Requirement Document (PRD)."
    )
    prd_init_parser.add_argument(
        "-nq", "--num-questions",
        type=str,
        help="Number of clarifying questions to ask (e.g., '5' or '3-5'). Default: 3-5."
    )
    prd_init_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name/title (for non-interactive mode)"
    )
    prd_init_parser.add_argument(
        "--project-description", 
        type=str,
        help="Project description (for non-interactive mode)"
    )
    prd_init_parser.add_argument(
        "--complexity",
        type=str,
        choices=['low', 'medium', 'high'],
        help="Project complexity level (for non-interactive mode)"
    )
    prd_init_parser.add_argument(
        "--priority",
        type=str, 
        choices=['low', 'medium', 'high'],
        help="Project priority level (for non-interactive mode)"
    )
    prd_init_parser.set_defaults(func=handle_prd_init)

    # Task Init Subcommand
    task_init_parser = subparsers.add_parser(
        "task-init", 
        help="Convert a PRD into a list of tasks."
    )
    task_init_parser.add_argument(
        "--level", 
        type=str, 
        choices=['simple', 'detailed'], 
        default='detailed', 
        help="Set the level of detail for task generation. 'simple' for high-level tasks, 'detailed' for granular tasks."
    )
    task_init_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    task_init_parser.set_defaults(func=handle_task_init)

    # Task Update Subcommand
    task_update_parser = subparsers.add_parser(
        "task-update", 
        help="Update task status and details."
    )
    task_update_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    task_update_parser.add_argument(
        "--task-id",
        type=int,
        help="Task ID to update (for non-interactive mode)"
    )
    task_update_parser.add_argument(
        "--status",
        type=str,
        choices=['pending', 'in-progress', 'completed'],
        help="New task status (for non-interactive mode)"
    )
    task_update_parser.add_argument(
        "--priority",
        type=str,
        choices=['low', 'medium', 'high'],
        help="New task priority (for non-interactive mode)"
    )
    task_update_parser.add_argument(
        "--description",
        type=str,
        help="New task description (for non-interactive mode)"
    )
    task_update_parser.add_argument(
        "--details",
        type=str,
        help="New task details (for non-interactive mode)"
    )
    task_update_parser.set_defaults(func=handle_task_update)

    # Task View Subcommand
    task_view_parser = subparsers.add_parser(
        "task-view", 
        help="Display tasks with filtering options."
    )
    task_view_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    task_view_parser.add_argument(
        "--filter",
        type=str,
        choices=['all', 'status', 'priority', 'pending', 'completed'],
        help="Filter type (for non-interactive mode)"
    )
    task_view_parser.add_argument(
        "--status",
        type=str,
        choices=['pending', 'in-progress', 'completed'],
        help="Status to filter by (use with --filter status)"
    )
    task_view_parser.add_argument(
        "--priority",
        type=str,
        choices=['low', 'medium', 'high'],
        help="Priority to filter by (use with --filter priority)"
    )
    task_view_parser.set_defaults(func=handle_task_view)

    # Task Export Subcommand
    task_export_parser = subparsers.add_parser(
        "task-export", 
        help="Export tasks to project management tools (Jira, Trello, GitHub Issues)."
    )
    task_export_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    task_export_parser.add_argument(
        "--format",
        type=str,
        choices=['jira', 'trello', 'github', 'githubissues'],
        help="Export format: jira, trello, github/githubissues (for non-interactive mode)"
    )
    task_export_parser.set_defaults(func=handle_task_export)

    # PRD Update Subcommand
    prd_update_parser = subparsers.add_parser(
        "prd-update", 
        help="Modify existing PRDs."
    )
    prd_update_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    prd_update_parser.add_argument(
        "--modification-request",
        type=str,
        help="Description of changes to make to the PRD (for non-interactive mode)"
    )
    prd_update_parser.set_defaults(func=handle_prd_update)

    # PRD Compare Subcommand
    prd_compare_parser = subparsers.add_parser(
        "prd-compare", 
        help="Show differences between PRD versions."
    )
    prd_compare_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    prd_compare_parser.add_argument(
        "--first-version",
        type=str,
        help="First version to compare (e.g., 'current', 'backup_123456', or index number)"
    )
    prd_compare_parser.add_argument(
        "--second-version",
        type=str,
        help="Second version to compare (e.g., 'current', 'backup_123456', or index number)"
    )
    prd_compare_parser.set_defaults(func=handle_prd_compare)

    # PRD Validate Subcommand
    prd_validate_parser = subparsers.add_parser(
        "prd-validate", 
        help="Check PRD completeness and quality."
    )
    prd_validate_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    prd_validate_parser.set_defaults(func=handle_prd_validate)

    # Task Next Subcommand (Priority 1 Enhancement)
    task_next_parser = subparsers.add_parser(
        "task-next", 
        help="Uses AI to recommend the most logical next task from available (pending and unblocked) tasks, considering impact and flow. Provides justification."
    )
    task_next_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    task_next_parser.set_defaults(func=handle_task_next)

    # Task Expand Subcommand (Priority 1 Enhancement)
    task_expand_parser = subparsers.add_parser(
        "task-expand", 
        help="Break down a task into subtasks using AI."
    )
    task_expand_parser.add_argument("--id", type=int, required=True, help="Task ID to expand")
    task_expand_parser.add_argument("--force", action="store_true", help="Force regeneration of existing subtasks")
    task_expand_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    task_expand_parser.set_defaults(func=handle_task_expand)

    # Task Dependencies Subcommand (Priority 1 Enhancement)
    task_deps_parser = subparsers.add_parser(
        "task-deps", 
        help="Manage task dependencies."
    )
    task_deps_parser.add_argument("--add", action="store_true", help="Add a dependency")
    task_deps_parser.add_argument("--remove", action="store_true", help="Remove a dependency")
    task_deps_parser.add_argument("--id", type=int, help="Task ID (required unless using --validate)")
    task_deps_parser.add_argument("--depends-on", type=int, help="Dependency task ID")
    task_deps_parser.add_argument("--validate", action="store_true", help="Validate all dependencies")
    task_deps_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    task_deps_parser.set_defaults(func=handle_task_dependencies)

    # Task Complexity Subcommand (Priority 1 Enhancement)
    task_complexity_parser = subparsers.add_parser(
        "task-complexity", 
        help="Analyze task complexity, store results in tasks.json, and generate a report. Use --id for a specific task or --all for all tasks."
    )
    complexity_group = task_complexity_parser.add_mutually_exclusive_group(required=True)
    complexity_group.add_argument("--id", type=int, help="ID of the specific task to analyze.")
    complexity_group.add_argument("--all", action="store_true", help="Analyze all tasks in the project.")
    task_complexity_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    task_complexity_parser.set_defaults(func=handle_task_complexity)

    # PRD Complexity Analysis Subcommand (Priority 2 Enhancement)
    prd_complexity_parser = subparsers.add_parser(
        "prd-complexity", 
        help="Analyze PRD complexity and get recommendations."
    )
    prd_complexity_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    prd_complexity_parser.set_defaults(func=handle_prd_complexity)

    # Natural Language Command Subcommand (Priority 2 Enhancement)
    nl_command_parser = subparsers.add_parser(
        "nl-command",
        help="Execute commands using natural language queries."
    )
    nl_command_parser.add_argument(
        "query",
        type=str,
        nargs='+',
        help="The natural language query describing the command to execute."
    )
    nl_command_parser.add_argument(
        "--suggest-only",
        action="store_true",
        help="Suggest the command interpretation without executing it."
    )
    nl_command_parser.set_defaults(func=handle_natural_language_command)

    # Research-Backed Task Generation Subcommand (Priority 2 Enhancement)
    research_tasks_parser = subparsers.add_parser(
        "task-research", 
        help="Generate research-backed tasks with industry best practices."
    )
    research_tasks_parser.add_argument(
        "--level", 
        type=str, 
        choices=['simple', 'detailed'], 
        default='detailed', 
        help="Set the level of detail for task generation. 'simple' for high-level epics, 'detailed' for granular tasks."
    )
    research_tasks_parser.add_argument("--force", action="store_true", help="Force regeneration of existing tasks")
    research_tasks_parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for non-interactive mode)"
    )
    research_tasks_parser.set_defaults(func=handle_research_backed_tasks)

    args = parser.parse_args()

    if args.command is None:
        display_header("Auto-PRDGen", "Product Requirements Document Generator")
        parser.print_help()
    else:
        try:
            args.func(args)
        except KeyboardInterrupt:
            colored_print("\n\nOperation cancelled by user.", Fore.YELLOW)
        except Exception as e:
            colored_print(f"\nUnexpected error: {e}", Fore.RED)
            if config.get('ui.debug', False):
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    main()