"""Context compression for long-running fable tasks."""

from pathlib import Path
from typing import Dict, List


class ContextCompressor:
    """Compresses long stage outputs into summaries for downstream stages."""

    def __init__(self, max_lines: int = 100):
        self.max_lines = max_lines

    def compress_file(self, path: Path) -> str:
        if not path.exists():
            return f"[File not found: {path}]"
        lines = path.read_text().splitlines()
        total = len(lines)
        if total <= self.max_lines:
            return path.read_text()
        head = "\n".join(lines[:30])
        tail = "\n".join(lines[-30:])
        return f"{head}\n\n... [{total - 60} lines omitted] ...\n\n{tail}"

    def compress_files(self, paths: List[Path]) -> Dict[str, str]:
        return {str(p): self.compress_file(p) for p in paths}

    def create_context_packet(self, task: str, dependency_files: Dict[str, Path]) -> str:
        parts = [f"Base task: {task}"]
        for dep_name, dep_path in dependency_files.items():
            summary = self.compress_file(dep_path)
            parts.append(f"\n--- {dep_name} summary ---\n{summary}")
        return "\n".join(parts)
