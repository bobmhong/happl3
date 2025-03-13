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
            env=self.env,
            bufsize=0  # Disable Line buffering
        )

    # Restart Shell Session in the event of an error
    def restart_session(self):
        self.close_session()
        self.start_session()

    # Run a single command in the shell appended by a marker to indicate the end of the output
    # If the call is successful, this function will return the output of the command from stdout
    # If the command fails, it will raise a subprocess.CalledProcessError and return the error message from stderr
    def run_command(self, command):
        # marked_command = f'{command};\necho "OUTPUT_COMPLETE_MARKER"\n'

        if self.shell_type == "pwsh":
            marked_command = f'{command}; if ($?) {{ Write-Output "OUTPUT_COMPLETE_MARKER" }} else {{ Write-Output "OUTPUT_COMPLETE_MARKER"; exit 1 }}\n'
        else:
            marked_command = f'{command}\necho "OUTPUT_COMPLETE_MARKER"\n'
        
        self.process.stdin.write(marked_command)
        self.process.stdin.flush()

        output_lines = []
        error_lines = []

        while True:
            reads, _, _ = select.select([self.process.stdout, self.process.stderr], [], [], 0.1)
            # if reads:
            #     # Check if the process has finished
            #     if self.process.poll() is not None:
            #         # Read any remaining output
            #         while True:
            #             line = self.process.stdout.readline()
            #             if not line:
            #                 break
            #             output_lines.append(line.strip())
            #         while True:
            #             err_line = self.process.stderr.readline()
            #             if not err_line:
            #                 break
            #             error_lines.append(err_line.strip())
            #         break

            for read in reads:
                # Read a line from the stdout or stderr
                line = read.readline()
                while line:
                    # Check if the line contains the end marker
                    if "OUTPUT_COMPLETE_MARKER" in line:
                        break
                    elif read == self.process.stdout:
                        output_lines.append(line.strip())
                    elif read == self.process.stderr:
                        error_lines.append(line.strip())
                    
                    line = read.readline()

            # Check if there was an error
            if error_lines:
                return_code = self.process.poll()
                raise subprocess.CalledProcessError(return_code, command, output="\n".join(output_lines), stderr="\n".join(error_lines))

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
