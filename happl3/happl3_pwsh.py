import subprocess
import platform
import os

class Happl3Pwsh:
    def __init__(self):
        self.process = None
        self.env = os.environ.copy()
        self.env["TERM"] = "dumb"
        self.powershell_executable = "powershell.exe" if platform.system() == "Windows" else "pwsh"
        self.start_session()

    def start_session(self):
        self.process = subprocess.Popen(
            [self.powershell_executable, "-NoExit", "-Command", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self.env
        )

    def run_command(self, command):
        marked_command = f'{command}; Write-Output "OUTPUT_COMPLETE_MARKER"\n'
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
        self.process.stdin.write("exit\n")
        self.process.stdin.flush()
        self.process.terminate()

def run_powershell_commands(commands):
    pwsh_session = Happl3Pwsh()
    results = []

    try:
        for command in commands:
            result = pwsh_session.run_command(command)
            results.append(result)
    finally:
        pwsh_session.close_session()

    return results