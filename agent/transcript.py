import json
from pathlib import Path


class Recorder:
    def __init__(self, path):
        self.path = path
        self.parts = []

    def add(self, title, body):
        if self.path:
            self.parts.append(f"## {title}\n\n{body}".rstrip())

    def turn(self, message):
        if not self.path:
            return
        body = message.content or ""
        for call in message.tool_calls or []:
            body += f"\n\n**bash**\n```bash\n{json.loads(call.function.arguments or '{}').get('command', '')}\n```"
        self.parts.append(f"## assistant\n\n{body}".rstrip())

    def tool(self, result):
        if self.path:
            self.parts.append(f"### tool result\n\n```\n{result}\n```")

    def flush(self, verdict):
        if self.path:
            Path(self.path).write_text(f"# {verdict}\n\n" + "\n\n".join(self.parts) + "\n")
