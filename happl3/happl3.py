#!/usr/bin/env python3

import argparse
import curses
from happl3.happl3_app import Happl3
from happl3.happl3_shell import Happl3Shell

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
    
    # Initialize Happl3Shell instance
    shell_type = "pwsh" if args.PlanFile.endswith('.ps1') else "bash"
    app.shell_session = Happl3Shell(shell_type)
    
    try:
        curses.wrapper(app.run)
    finally:
        # Close Happl3Shell session when app quits
        app.shell_session.close_session()

if __name__ == "__main__":
    main()
