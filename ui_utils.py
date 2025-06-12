#!/usr/bin/env python
"""
UI utilities for Auto-PRDGen
Provides progress bars, enhanced animations, and user interaction helpers
"""

import time
import sys
from typing import Optional, Iterator, Any
from colorama import Fore, Style
from config import config

class ProgressBar:
    """Enhanced progress bar with customizable appearance"""
    
    def __init__(self, total: int = 100, width: int = 50, desc: str = "Progress"):
        self.total = total
        self.width = width
        self.desc = desc
        self.current = 0
        self.start_time = time.time()
        self.enabled = config.get('ui.progress_bars', True) and not config.get('ui.quiet_mode', False)
    
    def update(self, amount: int = 1):
        """Update progress by specified amount"""
        if not self.enabled:
            return
        
        self.current = min(self.current + amount, self.total)
        self._render()
    
    def set_progress(self, value: int):
        """Set absolute progress value"""
        if not self.enabled:
            return
        
        self.current = min(max(value, 0), self.total)
        self._render()
    
    def _render(self):
        """Render the progress bar"""
        if not self.enabled:
            return
        
        percent = (self.current / self.total) * 100
        filled_width = int((self.current / self.total) * self.width)
        
        # Create progress bar
        bar = '█' * filled_width + '░' * (self.width - filled_width)
        
        # Calculate elapsed time and ETA
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f"{eta:.1f}s"
        else:
            eta_str = "--"
        
        # Color the progress bar based on completion
        if percent < 30:
            color = Fore.RED
        elif percent < 70:
            color = Fore.YELLOW
        else:
            color = Fore.GREEN
        
        # Render the line
        line = f"\r{self.desc}: {color}{bar}{Style.RESET_ALL} {percent:5.1f}% ({self.current}/{self.total}) ETA: {eta_str}"
        print(line, end='', flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete
    
    def finish(self):
        """Mark progress as complete"""
        if not self.enabled:
            return
        
        self.current = self.total
        self._render()

class EnhancedSpinner:
    """Enhanced spinner with customizable animations"""
    
    def __init__(self, desc: str = "Processing", style: str = "dots"):
        self.desc = desc
        self.style = style
        self.enabled = not config.get('ui.quiet_mode', False)
        self.speed = config.get('ui.animation_speed', 0.3)
        
        self.animations = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "classic": ["|", "/", "-", "\\"],
            "arrows": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
            "bounce": ["⠁", "⠂", "⠄", "⠂"],
            "pulse": ["●", "○", "●", "○"]
        }
        
        self.frames = self.animations.get(style, self.animations["dots"])
        self.idx = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if not self.enabled:
            time.sleep(self.speed)
            return
        
        frame = self.frames[self.idx % len(self.frames)]
        color = Fore.CYAN if config.get('ui.colors_enabled', True) else ""
        reset = Style.RESET_ALL if config.get('ui.colors_enabled', True) else ""
        
        print(f"\r{color}{frame} {self.desc}...{reset}", end="", flush=True)
        self.idx += 1
        time.sleep(self.speed)
    
    def stop(self):
        """Stop the spinner and clear the line"""
        if self.enabled:
            print("\r" + " " * (len(self.desc) + 10) + "\r", end="", flush=True)

def colored_print(text: str, color: str = Fore.WHITE, style: str = Style.NORMAL):
    """Print colored text if colors are enabled"""
    if config.get('ui.colors_enabled', True) and not config.get('ui.quiet_mode', False):
        print(f"{color}{style}{text}{Style.RESET_ALL}")
    else:
        print(text)

def quiet_print(text: str, force: bool = False):
    """Print text only if not in quiet mode, or if forced"""
    if not config.get('ui.quiet_mode', False) or force:
        print(text)

def get_user_input(prompt: str, history_key: Optional[str] = None) -> str:
    """Enhanced user input with history support"""
    if config.get('ui.colors_enabled', True):
        colored_prompt = f"{Fore.BLUE}{prompt}{Style.RESET_ALL}"
    else:
        colored_prompt = prompt
    

    
    response = input(colored_prompt)
    
    # Save to history if key provided
    if history_key and response.strip():
        config.add_to_history(history_key, {
            "input": response,
            "prompt": prompt
        })
    
    return response

def confirm_action(message: str, default: bool = True) -> bool:
    """Ask for user confirmation"""
    suffix = " [Y/n]" if default else " [y/N]"
    response = get_user_input(f"{message}{suffix}: ").lower().strip()
    
    if not response:
        return default
    
    return response in ['y', 'yes', 'true', '1']

def select_from_list(items: list, prompt: str = "Select an option", show_numbers: bool = True) -> tuple[int, Any]:
    """Enhanced list selection with better formatting"""
    if not items:
        raise ValueError("No items to select from")
    
    quiet_print(f"\n{prompt}:")
    
    for i, item in enumerate(items, 1):
        if show_numbers:
            colored_print(f"  {i}. {item}", Fore.CYAN)
        else:
            colored_print(f"  • {item}", Fore.CYAN)
    
    while True:
        try:
            choice = get_user_input("\nEnter your choice (number): ")
            index = int(choice) - 1
            
            if 0 <= index < len(items):
                return index, items[index]
            else:
                colored_print(f"Please enter a number between 1 and {len(items)}", Fore.RED)
        except ValueError:
            colored_print("Please enter a valid number", Fore.RED)

def display_header(title: str, subtitle: str = ""):
    """Display a formatted header"""
    if config.get('ui.quiet_mode', False):
        return
    
    width = max(len(title), len(subtitle)) + 4
    border = "═" * width
    
    colored_print(f"\n╔{border}╗", Fore.CYAN)
    colored_print(f"║ {title.center(width-2)} ║", Fore.CYAN)
    
    if subtitle:
        colored_print(f"║ {subtitle.center(width-2)} ║", Fore.YELLOW)
    
    colored_print(f"╚{border}╝\n", Fore.CYAN)

def stream_print(text: str, delay: float = 0.01):
    """Stream print text with configurable delay"""
    if config.get('ui.quiet_mode', False):
        print(text)
        return
    
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()