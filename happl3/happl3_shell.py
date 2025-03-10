import subprocess
import platform
import os

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
            [self.shell_executable, "-NoExit", "-Command", "-"] if self.shell_type == "pwsh" else [self.shell_executable],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self.env
        )

    def run_command(self, command):
        if self.shell_type == "pwsh":
            marked_command = f'{command}; Write-Output "OUTPUT_COMPLETE_MARKER"\n'
        else:
            marked_command = f'{command}\necho "OUTPUT_COMPLETE_MARKER"\n'
        self.process.stdin.write(marked_command)
        self.process.stdin.flush()

        output_lines = []
        while True:
            line = self.process.stdout.readline()
            if "OUTPUT_COMPLETE_MARKER" in line:
                break
            if line:
                output_lines.append(line.strip())

        return "\n".join(output_lines)

    def close_session(self):
        if self.shell_type == "pwsh":
            self.process.stdin.write("exit\n")
        self.process.stdin.flush()
        self.process.terminate()

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
