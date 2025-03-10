import subprocess
import platform
import os
import select


class Happl3Shell:
    def __init__(self, shell_type="pwsh"):
        self.process = None
        self.env = os.environ.copy()
        self.env["TERM"] = "dumb"
        self.shell_type = shell_type
        if shell_type == "pwsh":
            self.shell_executable = "powershell.exe" if platform.system() == "Windows" else "pwsh"
        elif shell_type == "bash":
            self.shell_executable = "bash"
        self.start_session()

    def start_session(self):
        self.process = subprocess.Popen(
            [self.shell_executable, "-NoExit", "-Command",
                "-"] if self.shell_type == "pwsh" else [self.shell_executable],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self.env
        )

    # Restart Shell Session in the event of an error
    def restart_session(self):
        self.close_session()
        self.start_session()

    def run_command(self, command):
        if self.shell_type == "pwsh":
            marked_command = f'{command}; if ($?) {{ Write-Output "OUTPUT_COMPLETE_MARKER" }} else {{ Write-Output "OUTPUT_COMPLETE_MARKER"; exit 1 }}\n'
        else:
            marked_command = f'{command}\necho "OUTPUT_COMPLETE_MARKER"\n'
        self.process.stdin.write(marked_command)
        self.process.stdin.flush()

        output_lines = []
        error_lines = []

        process_outputs = True
        while process_outputs:
            reads = [self.process.stderr, self.process.stdout]
            readable, _, _ = select.select(reads, [], [])

            for r in readable:
                if r is self.process.stderr:
                    err_line = r.readline()
                    if err_line == '':
                        process_outputs = False
                        break
                    if err_line:
                        error_lines.append(err_line.strip())
                        break
                elif r is self.process.stdout:
                    line = r.readline()
                    if "OUTPUT_COMPLETE_MARKER" in line:
                        process_outputs = False
                        break
                    if line:
                        output_lines.append(line.strip())

            # Check for the process return code
        return_code = self.process.poll()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command, output="\n".join(
                output_lines), stderr="\n".join(error_lines))

        # Clear the checkmark after successful command execution
        if self.shell_type == "pwsh":
            self.process.stdin.write("Clear-Host\n")
        else:
            self.process.stdin.write("clear\n")
        self.process.stdin.flush()

        # Return the output if all commands were successful
        return "\n".join(output_lines)

    def close_session(self):
        try:
            if self.shell_type == "pwsh":
                self.process.stdin.write("exit\n")
            self.process.stdin.flush()
            self.process.terminate()
        except Exception as e:
            print(f"Error closing session: {e}")


def run_shell_commands(commands, shell_type="pwsh"):
    shell_session = Happl3Shell(shell_type)
    results = []

    try:
        for command in commands:
            result = shell_session.run_command(command)
            results.append(result)
    finally:
        shell_session.close_session()

    return results
