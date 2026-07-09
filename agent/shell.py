import os
import select
import subprocess
import sys
import time

from .config import CMD_TIMEOUT, OUTPUT_LIMIT

_SENTINEL = "__CMD_DONE_a7f2e__"

TOOL = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": (
            "Run commands in a bash shell\n"
            '* When invoking this tool, the contents of the "command" parameter does NOT need to be XML-escaped.\n'
            "* You don't have access to the internet via this tool.\n"
            "* Commands that take more than 120 seconds will time out and the tool will need to be restarted.\n"
            "* Commands that produce a stdout + stderr with more than 16000 characters will be truncated.\n"
            "* To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'.\n"
            "* State is persistent across command calls and discussions with the user.\n"
            "* Please run long lived commands in the background, e.g. 'sleep 10 &' or start a server in the background. "
            "A backgrounded command does not block this call's return, and anything it writes to stdout or stderr after "
            "the foreground part exits will not appear in this call's result."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to run. Required unless the tool is being restarted."},
                "restart": {"type": "boolean", "description": "Specifying true will restart this tool. Otherwise, leave this unspecified."},
            },
        },
    },
}


def clip(text):
    return text if len(text) <= OUTPUT_LIMIT else text[: OUTPUT_LIMIT - 5000] + "\n...[truncated]...\n" + text[-5000:]


class Shell:
    def __init__(self, cwd):
        self.cwd = str(cwd)
        self._spawn()

    def _spawn(self):
        env = dict(os.environ, PATH=os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", ""))
        self.proc = subprocess.Popen(["/bin/bash"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=self.cwd, env=env, bufsize=0)
        self.fd = self.proc.stdout.fileno()

    def restart(self):
        try:
            self.proc.kill()
        except Exception:  # pragma: no cover
            pass
        self._spawn()

    def run(self, command, timeout=CMD_TIMEOUT):
        if self.proc.poll() is not None:
            self._spawn()
        try:
            self.proc.stdin.write((command + f"\nprintf '\\n{_SENTINEL}%s\\n' \"$?\"\n").encode())
            self.proc.stdin.flush()
        except BrokenPipeError:  # pragma: no cover
            self._spawn()
            return "[bash session had crashed; it was restarted, rerun your command]"
        buffer, deadline, mark = b"", time.monotonic() + timeout, _SENTINEL.encode()
        while mark not in buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self.restart()
                return f"[timed out after {timeout}s; bash session restarted]"
            if select.select([self.fd], [], [], min(remaining, 1))[0]:
                chunk = os.read(self.fd, 65536)
                if not chunk:
                    self._spawn()
                    break
                buffer += chunk
        body, _, tail = buffer.decode("utf-8", "replace").partition(_SENTINEL)
        return clip(body.strip() or "(no output)") + f"\n[exit {tail.splitlines()[0].strip() if tail.strip() else '?'}]"
