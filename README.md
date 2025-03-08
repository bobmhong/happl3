# Happl3 - The Happy Script Applier

## Description

Happl3 is a tool to apply a series of PowerShell or Bash/Zsh shell commands from a plan file. The plan is a text file containing a list of commands to be executed in sequence. The tool will execute the commands in the plan in a user-controlled manner and log the output to a file. The tool will also track the status of each command in the plan and allow the user to re-run failed commands.

## Parameters

- **PlanFile**: The file containing the migration plan (required)
- **LogFile**: The file containing the log output (default to `<PlanFile>.log`)

## Usage

```bash
python3 ./happl3.py <PlanFile> [LogFile]

# Examples:
python3 ./happl3.py test.sh test.log
python3 ./happl3.py test.sh
python3 ./happl3.py  # Displays a program description and usage example.
```

## Requirements

- Python 3 or later

## User Interface

### Command Pane

- Displays the list of commands from the plan file.
- Columns: Select (checkbox), Status, Command.
- The first row is highlighted by default.
- The user can navigate using the arrow keys.
- The user can select/deselect rows using the space bar.
- The user can execute selected commands by pressing Enter.

### Output Pane

- Shows the log output of the executed commands.
- Each executed command writes FormattedCommandOutput:
  - Header Row: Timestamp, Status, Command.
  - Output Row: Standard Output and Standard Error from the executed command.
- FormattedCommandOutput will be written to the log file.
- The default sort order of the output pane is the most recent output at the top.
- The user can scroll through the log output using the arrow keys.

## Hotkeys

- **↑/↓**: Navigate through the commands.
- **Space**: Select/Deselect the highlighted command.
- **Enter**: Execute the selected commands.
- **a**: Select all commands.
- **n**: Deselect all commands.
- **p**: Select all pending commands.
- **f**: Select all failed commands.
- **Tab**: Switch focus between the command pane and the output pane.
- **H/E**: Move to the top/bottom of the command list.
- **q**: Quit the application.

## Command Execution Logic

1. **Selection**: The user selects the commands to be executed using the space bar. The selected commands are marked with a checkbox.
2. **Execution**: When the user presses Enter, selected rows are executed in sequence.
3. **Logging**: Each command's output (both stdout and stderr) is logged to the specified log file.
4. **Status Update**: The status of each command (pending, success, failed) is updated in the index file.
5. **Error Handling**: If a command fails, the execution stops, and the error is logged. The user can then re-run the failed commands.
6. **Highlight Update**: After executing a command, the highlight moves to the next selected row or the next pending row if no more selected rows are available.
