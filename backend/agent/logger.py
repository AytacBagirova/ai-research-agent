import json
import os
from datetime import datetime
from pathlib import Path

# Logların saxlanacağı qovluq
LOGS_DIR = Path("logs")


class AgentLogger:
    """
    Agentin hər addımını:
    1. Terminala çap edir
    2. JSONL faylına yazır (logs/session_X.jsonl)
    """

    def __init__(self, session_id: int):
        # logs/ qovluğu yoxdursa yarat
        LOGS_DIR.mkdir(exist_ok=True)
        self.session_id = session_id
        self.log_file = LOGS_DIR / f"session_{session_id}.jsonl"

    def _write(self, entry: dict) -> None:
        """JSONL faylına bir sətir yazar."""
        entry["timestamp"] = datetime.utcnow().isoformat()
        entry["session_id"] = self.session_id
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def log_thought(self, content: str) -> None:
        print(f"[Session {self.session_id}] 💭 THOUGHT: {content[:100]}...")
        self._write({"type": "thought", "content": content})

    def log_tool_use(self, tool_name: str, inputs: dict) -> None:
        print(f"[Session {self.session_id}] 🔧 TOOL USE: {tool_name} → {inputs}")
        self._write({"type": "tool_use", "tool_name": tool_name, "inputs": inputs})

    def log_tool_result(self, tool_name: str, success: bool, content: str) -> None:
        status = "✅" if success else "❌"
        print(f"[Session {self.session_id}] {status} TOOL RESULT: {tool_name} → {content[:100]}...")
        self._write({
            "type": "tool_result",
            "tool_name": tool_name,
            "success": success,
            "content": content[:500]
        })

    def log_critique(self, content: str) -> None:
        print(f"[Session {self.session_id}] 🔄 CRITIQUE: {content[:100]}...")
        self._write({"type": "critique", "content": content})

    def log_final_report(self, content: str) -> None:
        print(f"[Session {self.session_id}] 📄 FINAL REPORT: {len(content)} simvol")
        self._write({"type": "final_report", "content": content})

    def log_error(self, error: str) -> None:
        print(f"[Session {self.session_id}] ❌ ERROR: {error}")
        self._write({"type": "error", "content": error})

    def log_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Token sayımını log edir — tiktoken inteqrasiyası üçün."""
        total = input_tokens + output_tokens
        print(f"[Session {self.session_id}] 🔢 TOKENS: input={input_tokens} output={output_tokens} total={total}")
        self._write({
            "type": "tokens",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total
        })