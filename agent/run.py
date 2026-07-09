import argparse
import json
import os
import sys
from pathlib import Path

from openai import OpenAI

from .config import BASE_URL, MAX_TOKENS, MAX_TURNS, MODEL_DEFAULT, REPAIR_TURNS
from .gate import gate
from .probe import inventory, snapshot
from .prompt import system_prompt
from .shell import TOOL, Shell
from .transcript import Recorder
from .usage import log_usage


def _trim(messages):
    for m in messages[:-4]:
        if m["role"] == "tool" and len(m["content"]) > 300:
            m["content"] = m["content"][:300] + " …[trimmed]"
        for call in m.get("tool_calls") or []:
            if len(call["function"]["arguments"]) > 300:
                call["function"]["arguments"] = json.dumps({"command": "[earlier command omitted]"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", required=True)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    args = parser.parse_args()

    task_dir = Path(args.task_dir)
    workspace = task_dir / "workspace"
    task = (task_dir / "task.md").read_text()
    snap = snapshot(workspace)
    is_repair = (workspace / "tests").is_dir()
    is_redaction = any(k in task.lower() for k in ("redact", "[email]", "[phone]", "[name]", "pii"))
    sys_prompt = system_prompt(is_repair, is_redaction)
    user_msg = f"TASK:\n{task}\n\nWORKSPACE DIRECTORY (your shell's current directory; inputs live here, write the deliverable here): {workspace.resolve()}\n\nFILES (inspect further with small reads; never dump whole data files):\n{inventory(workspace)}"
    shell = Shell(workspace)
    client = OpenAI(base_url=BASE_URL, api_key=os.environ["OPENROUTER_API_KEY"])
    messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}]
    rec = Recorder(os.environ.get("AGENT_TRANSCRIPT"))
    rec.add("system prompt", sys_prompt)
    rec.add("task + files", user_msg)
    ok = False

    try:
        for _ in range(REPAIR_TURNS if is_repair else MAX_TURNS):
            response = client.chat.completions.create(model=args.model, max_tokens=MAX_TOKENS, temperature=0, tools=[TOOL], messages=messages)
            log_usage(response.usage)
            message = response.choices[0].message
            rec.turn(message)
            record = {"role": "assistant", "content": message.content or ""}
            if message.tool_calls:
                record["tool_calls"] = [call.model_dump() for call in message.tool_calls]
            messages.append(record)

            if not message.tool_calls:
                ok, reason = gate(workspace, task, snap)
                if ok:
                    return
                rec.add("self-gate", f"not finished: {reason}")
                messages.append({"role": "user", "content": f"Not finished: {reason}. Fix /tmp/solve.py and rerun until the check passes."})
                continue

            for call in message.tool_calls:
                payload = json.loads(call.function.arguments or "{}")
                if payload.get("restart"):
                    shell.restart()
                    result = "[bash restarted]"
                else:
                    command = payload.get("command", "")
                    if command:
                        print(f"  $ {command.splitlines()[0][:120]}", file=sys.stderr, flush=True)
                    result = shell.run(command)
                rec.tool(result)
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
            _trim(messages)

        ok = gate(workspace, task, snap)[0]
        sys.exit(0 if ok else 1)
    finally:
        rec.flush("agent self-gate PASSED" if ok else "agent self-gate did NOT pass (turns exhausted)")


if __name__ == "__main__":
    main()
