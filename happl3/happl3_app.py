import curses
import subprocess
import os
import json
import sys
import locale  # Add this import
from datetime import datetime
from .happl3_utils import hash_command  # Update this import

class Happl3:
    def __init__(self, plan_file=None, log_file=None):
        if plan_file is None:
            self.display_help()
            sys.exit(1)
        
        self.plan_file = plan_file
        self.log_file = log_file if log_file else f"{plan_file}.log"
        self.index_file = f"{plan_file}.index"
        self.commands = []
        self.index_data = {}
        self.highlight = 0
        self.scroll_offset = 0
        self.log_scroll_offset = 0
        self.focus = "preview"
        self.load_plan()
        self.load_index()

    def display_help(self):
        help_message = """
        Usage:
            happl3 <PlanFile> [LogFile]

        Parameters:
            PlanFile: The file containing the migration plan (required)
            LogFile: The file containing the log output (default to <PlanFile>.log)

        Description:
            Happl3 is a tool to apply a series of powershell or bash/zsh shell commands from a plan file.
            The plan is a text file containing a list of commands to be executed in sequence. The tool will
            execute the commands in the plan in a user-controlled manner and log the output to a file. The
            tool will also track the status of each command in the plan and allow the user to re-run failed commands.
        """
        print(help_message)

    def load_plan(self):
        with open(self.plan_file, 'r') as f:
            self.commands = [line.strip() for line in f.readlines() if line.strip()]
        with open(self.log_file, 'a') as log:
            log.write(f"[{datetime.now()}] Loaded {len(self.commands)} commands from {self.plan_file}\n")

    def load_index(self):
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r') as f:
                self.index_data = json.load(f)
        else:
            self.index_data = {}
        
        # Ensure all commands have an entry in the index data
        for i, cmd in enumerate(self.commands):
            if str(i) not in self.index_data:
                self.index_data[str(i)] = {
                    "hash": hash_command(cmd),
                    "selected": False,
                    "status": "pending",
                    "update_timestamp": None
                }
            else:
                # Ensure the status is correctly set
                self.index_data[str(i)]["hash"] = hash_command(cmd)
                if "status" not in self.index_data[str(i)]:
                    self.index_data[str(i)]["status"] = "pending"
                if "selected" not in self.index_data[str(i)]:
                    self.index_data[str(i)]["selected"] = False
                if "update_timestamp" not in self.index_data[str(i)]:
                    self.index_data[str(i)]["update_timestamp"] = None

        # Move highlight to the first pending row
        self.highlight = self.find_next_pending(0)

    def save_index(self):
        with open(self.index_file, 'w') as f:
            json.dump(self.index_data, f, indent=2)

    def is_pending(self, index):
        """Check if the row at index has 'pending' status."""
        return self.index_data[str(index)]["status"] == "pending"

    def find_next_pending(self, start_index):
        """Find the next row with 'pending' status starting from start_index."""
        for i in range(start_index, len(self.commands)):
            if self.is_pending(i) and not self.commands[i].startswith('#'):
                return i
        return len(self.commands) - 1  # Return last row if no pending found

    def run(self, stdscr):
        locale.setlocale(locale.LC_ALL, '')  # Ensure UTF-8 is used
        curses.curs_set(0)
        self.stdscr = stdscr
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Normal text
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Status bar
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Separator
        curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Comments
        curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)   # Border
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Title
        curses.init_pair(8, curses.COLOR_RED, curses.COLOR_BLACK)    # Error
        self.stdscr.bkgd(' ', curses.color_pair(1))

        self.max_y, self.max_x = stdscr.getmaxyx()
        with open(self.log_file, 'a') as log:
            log.write(f"Terminal size: {self.max_y} rows × {self.max_x} cols\n")

        while True:
            self.draw()
            key = stdscr.getch()
            if key == ord('q'):
                break
            elif key == 9:  # Tab key
                self.focus = "log" if self.focus == "preview" else "preview"
            elif self.focus == "preview":
                if key == curses.KEY_UP and self.highlight > 0:
                    self.highlight -= 1
                elif key == curses.KEY_DOWN and self.highlight < len(self.commands) - 1:
                    self.highlight += 1
                elif key == curses.KEY_HOME or key == ord('H'):
                    self.highlight = 0
                elif key == curses.KEY_END or key == ord('E'):
                    self.highlight = len(self.commands) - 1
                elif key == ord(' '):
                    if not self.commands[self.highlight].startswith('#'):
                        self.index_data[str(self.highlight)]["selected"] = not self.index_data[str(self.highlight)]["selected"]
                    if self.highlight < len(self.commands) - 1:
                        self.highlight += 1
                elif key == ord('a'):
                    for i in range(len(self.commands)):
                        if not self.commands[i].startswith('#'):
                            self.index_data[str(i)]["selected"] = True
                elif key == ord('n'):
                    for i in range(len(self.commands)):
                        self.index_data[str(i)]["selected"] = False
                elif key == ord('p'):
                    for i in range(len(self.commands)):
                        self.index_data[str(i)]["selected"] = self.is_pending(i)
                elif key == ord('f'):
                    for i in range(len(self.commands)):
                        self.index_data[str(i)]["selected"] = self.index_data[str(i)]["status"] == "failed"
                elif key == ord('b'):
                    for i in range(self.highlight, len(self.commands)):
                        if self.commands[i].startswith('#'):
                            break
                        if self.is_pending(i):
                            self.index_data[str(i)]["selected"] = True
                elif key == curses.KEY_ENTER or key == 10 or key == 13:
                    self.execute_selected()
            elif self.focus == "log":
                if os.path.exists(self.log_file):
                    with open(self.log_file, 'r') as f:
                        lines = f.readlines()
                    max_scroll = max(0, len(lines) - (self.max_y - (self.max_y - 1) // 2 - 2))
                    if key == curses.KEY_UP and self.log_scroll_offset > 0:
                        self.log_scroll_offset -= 1
                    elif key == curses.KEY_DOWN and self.log_scroll_offset < max_scroll:
                        self.log_scroll_offset += 1
                    elif key == curses.KEY_HOME or key == ord('H'):
                        self.log_scroll_offset = 0
                    elif key == curses.KEY_END or key == ord('E'):
                        self.log_scroll_offset = max_scroll

    def draw(self):
        self.stdscr.clear()

        # Calculate pane heights
        cmd_height = (self.max_y - 3) // 2 - 1  # Adjust for title and borders
        separator_row = cmd_height + 2
        out_height = self.max_y - cmd_height - 4

        # Draw application title
        title = "Happl3 - The Happy Command Applier"
        self.stdscr.addstr(0, 0, title, curses.color_pair(7) | curses.A_BOLD)

        # Draw command pane
        visible_lines = cmd_height - 1  # Adjust for navigation status bar
        self.scroll_offset = max(0, min(self.highlight - visible_lines // 2, 
                                      len(self.commands) - visible_lines))

        if not self.commands:
            self.stdscr.addstr(2, 1, "No commands loaded", curses.color_pair(1))
        else:
            for i in range(self.scroll_offset, 
                         min(self.scroll_offset + visible_lines, len(self.commands))):
                cmd = self.commands[i]
                index = str(i)
                status = self.index_data[index]["status"] if not cmd.startswith('#') else ""
                selected = self.index_data[index]["selected"]
                select_display = '[x]' if selected else '[ ]' if not cmd.startswith('#') else '   '
                status_emoji = {
                    "success": "✔",  # Checkmark
                    "failed": "✖",   # Cross
                    "pending": "⌛"   # Hourglass
                }.get(status, "")
                line = f"{i + 1:3} {select_display} {status_emoji:<2} {cmd[:self.max_x-25]}".ljust(self.max_x - 2)
                row = i - self.scroll_offset + 2
                if 0 <= row < cmd_height + 1:
                    try:
                        if i == self.highlight and self.focus == "preview":
                            attr = curses.color_pair(2)
                        elif cmd.startswith('#'):
                            attr = curses.color_pair(5)  # Green for comments
                        else:
                            attr = curses.color_pair(1)
                        self.stdscr.addstr(row, 1, line.encode('utf-8'), attr)
                    except curses.error:
                        break

        # Draw navigation status bar
        help_text = "↑↓:navigate Space:select Enter:run a:all n:none p:pending b:block f:failed Tab:switch H/E:top/bottom  q:quit"
        self.stdscr.addstr(cmd_height + 1, 1, help_text[:self.max_x-2], curses.color_pair(3))

        # Draw row counter and plan file name in the lower right corner of the preview pane
        preview_row_counter = f"{self.plan_file} | Row {self.highlight + 1}/{len(self.commands)}"
        self.stdscr.addstr(cmd_height + 1, self.max_x - len(preview_row_counter) - 2, preview_row_counter, curses.color_pair(3))

        # Draw thick separator
        separator = "═" * (self.max_x - 2)
        self.stdscr.addstr(separator_row, 1, separator, curses.color_pair(4))

        # Draw output pane (reverse order, scrollable, no highlight)
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                reversed_lines = lines[::-1]
                start = self.log_scroll_offset
                end = min(start + out_height, len(reversed_lines))
                for i, line in enumerate(reversed_lines[start:end]):
                    row = separator_row + 1 + i
                    if row < self.max_y - 2:
                        try:
                            attr = curses.color_pair(8) if "ERROR:" in line or "EXCEPTION:" in line else curses.color_pair(1)
                            self.stdscr.addstr(row, 1, line.encode('utf-8').rstrip(), attr)
                        except curses.error:
                            break

        # Draw row number counter and log file name in the lower right corner of the log pane
        log_row_counter = f"{self.log_file} | Row {self.log_scroll_offset + 1}/{len(lines)}"
        self.stdscr.addstr(self.max_y - 2, self.max_x - len(log_row_counter) - 2, log_row_counter, curses.color_pair(3))

        # Draw single line blue border around the perimeter of each pane
        for y in range(1, self.max_y - 1):
            try:
                self.stdscr.addch(y, 0, curses.ACS_VLINE, curses.color_pair(6))
                self.stdscr.addch(y, self.max_x - 1, curses.ACS_VLINE, curses.color_pair(6))
            except curses.error:
                pass
        for x in range(self.max_x):
            try:
                self.stdscr.addch(1, x, curses.ACS_HLINE, curses.color_pair(6))
                self.stdscr.addch(self.max_y - 1, x, curses.ACS_HLINE, curses.color_pair(6))
            except curses.error:
                pass
        try:
            self.stdscr.addch(1, 0, curses.ACS_ULCORNER, curses.color_pair(6))
            self.stdscr.addch(1, self.max_x - 1, curses.ACS_URCORNER, curses.color_pair(6))
            self.stdscr.addch(self.max_y - 1, 0, curses.ACS_LLCORNER, curses.color_pair(6))
            self.stdscr.addch(self.max_y - 1, self.max_x - 1, curses.ACS_LRCORNER, curses.color_pair(6))
        except curses.error:
            pass

        self.stdscr.noutrefresh()
        curses.doupdate()

    def execute_selected(self):
        shell = "pwsh" if self.plan_file.endswith('.ps1') else "bash"
        executed = False
        selected_count = sum(1 for i in range(len(self.commands)) if self.index_data[str(i)]["selected"])
    
        # Move highlight to the first selected row
        for i in range(len(self.commands)):
            if self.index_data[str(i)]["selected"]:
                self.highlight = i
                break

        current_index = self.highlight
        error_occurred = False

        while current_index < len(self.commands):
            if self.index_data[str(current_index)]["selected"] and not self.commands[current_index].startswith('#'):
                hash_key = hash_command(self.commands[current_index])
                with open(self.log_file, 'a') as log:
                    log.write(f"\n[{datetime.now()}] > {self.commands[current_index]}\n")
                    try:
                        if shell == "pwsh":
                            result = subprocess.run(["pwsh", "-Command", self.commands[current_index]], 
                                                    capture_output=True, text=True)
                        else:
                            result = subprocess.run(self.commands[current_index], shell=True, 
                                                    capture_output=True, text=True)
                        log.write(result.stdout)
                        if result.stderr:
                            log.write(f"ERROR: {result.stderr}\n")
                        new_status = "success" if result.returncode == 0 else "failed"
                        status_emoji = "✔" if new_status == "success" else "✖"
                        log.write(f"{status_emoji} {new_status.upper()}\n")
                        self.index_data[str(current_index)]["status"] = new_status
                        self.index_data[str(current_index)]["update_timestamp"] = datetime.now().isoformat()
                        if new_status == "success":
                            self.index_data[str(current_index)]["selected"] = False
                        executed = True
                        if new_status == "failed":
                            error_occurred = True
                            break
                    except subprocess.CalledProcessError as e:
                        log.write(f"✖ ERROR: CalledProcessError: {str(e)}\n")
                        self.index_data[str(current_index)]["status"] = "failed"
                        self.index_data[str(current_index)]["update_timestamp"] = datetime.now().isoformat()
                        executed = True
                        error_occurred = True
                        break
                    except Exception as e:
                        log.write(f"✖ ERROR: EXCEPTION: {str(e)}\n")
                        self.index_data[str(current_index)]["status"] = "failed"
                        self.index_data[str(current_index)]["update_timestamp"] = datetime.now().isoformat()
                        executed = True
                        error_occurred = True
                        break
                self.save_index()
                self.draw()  # Redraw to update the status emojis
            current_index += 1

            # Move highlight to the next selected row or next pending row if no more selected rows
            if not error_occurred:
                for i in range(current_index, len(self.commands)):
                    if self.index_data[str(i)]["selected"]:
                        self.highlight = i
                        current_index = i  # Adjust current_index to continue from the next row
                        break
                else:
                    # start looking for next pending at the current_index
                    self.highlight = self.find_next_pending(self.highlight)

        if executed:
            self.draw()