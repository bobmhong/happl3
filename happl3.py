#!/usr/bin/env python3

# Happl3 - The happy script applier

## Description

# Happl3 is a tool to apply a series of powershell or bash/zsh shell commands from a plan file.

# The plan is a text file containing a list of commands to be executed in sequence. The tool will execute the commands in the plan in a user-controlled manner and log the output to a file. The tool will also track the status of each command in the plan and allow the user to re-run failed commands.

import argparse
import curses
import hashlib
from happl3_app import Happl3

def hash_command(command):
    return hashlib.md5(command.encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Happl3 - The happy script applier")
    parser.add_argument("PlanFile", nargs='?', help="The file containing the migration plan")
    parser.add_argument("LogFile", nargs='?', help="The file containing the log output (default to ${PlanFile}.log)")
    args = parser.parse_args()

    if not args.PlanFile:
        Happl3().display_help()
        return

    log_file = args.LogFile if args.LogFile else f"{args.PlanFile}.log"
    app = Happl3(args.PlanFile, log_file)
    curses.wrapper(app.run)

if __name__ == "__main__":
    main()