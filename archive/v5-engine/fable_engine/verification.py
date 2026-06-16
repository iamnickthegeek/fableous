"""Self-verification engine that runs failable checks on stage outputs."""

import subprocess
from pathlib import Path
from typing import Any, Dict, List


class VerificationEngine:
    """Runs domain-specific failable checks on stage outputs."""

    def __init__(self):
        self.checks = []

    def add_file_check(self, path: Path, min_size: int = 100) -> None:
        self.checks.append({"type": "file", "path": path, "min_size": min_size})

    def add_url_check(self, url: str) -> None:
        self.checks.append({"type": "url", "url": url})

    def add_content_check(self, path: Path, required_substrings: List[str]) -> None:
        self.checks.append({"type": "content", "path": path, "required": required_substrings})

    def add_test_command(self, cmd: str, cwd: str = ".") -> None:
        self.checks.append({"type": "test", "cmd": cmd, "cwd": cwd})

    def run_checks(self) -> Dict[str, Any]:
        results = []
        all_passed = True
        for check in self.checks:
            result = self._run_single(check)
            results.append(result)
            if not result["passed"]:
                all_passed = False
        return {
            "passed": all_passed,
            "results": results,
            "errors": [r for r in results if not r["passed"]],
        }

    def _run_single(self, check: Dict[str, Any]) -> Dict[str, Any]:
        ctype = check["type"]
        if ctype == "file":
            path = check["path"]
            ok = path.exists() and path.stat().st_size >= check["min_size"]
            return {"type": ctype, "target": str(path), "passed": ok, "detail": f"size={path.stat().st_size if path.exists() else 0}"}
        elif ctype == "url":
            url = check["url"]
            try:
                r = subprocess.run(f"curl -s -o /dev/null -w '%{{http_code}}' {url}", shell=True, capture_output=True, text=True, timeout=30)
                code = r.stdout.strip()
                ok = code == "200"
                return {"type": ctype, "target": url, "passed": ok, "detail": f"HTTP {code}"}
            except Exception as e:
                return {"type": ctype, "target": url, "passed": False, "detail": str(e)}
        elif ctype == "content":
            path = check["path"]
            if not path.exists():
                return {"type": ctype, "target": str(path), "passed": False, "detail": "File not found"}
            text = path.read_text()
            missing = [s for s in check["required"] if s not in text]
            ok = len(missing) == 0
            return {"type": ctype, "target": str(path), "passed": ok, "detail": f"Missing: {missing}" if missing else "All required substrings found"}
        elif ctype == "test":
            try:
                r = subprocess.run(check["cmd"], shell=True, capture_output=True, text=True, timeout=120, cwd=check["cwd"])
                ok = r.returncode == 0
                return {"type": ctype, "target": check["cmd"], "passed": ok, "detail": r.stdout[:200] if ok else r.stderr[:200]}
            except Exception as e:
                return {"type": ctype, "target": check["cmd"], "passed": False, "detail": str(e)}
        return {"type": ctype, "passed": False, "detail": "Unknown check type"}

    def verify_stage(self, stage_id: str, output_file: Path, domain: str = "research") -> Dict[str, Any]:
        """Run domain-specific verification for a stage."""
        self.checks = []
        self.add_file_check(output_file, min_size=50)
        if domain == "research":
            self.add_content_check(output_file, required_substrings=["Source", "http"])
        elif domain == "software":
            self.add_content_check(output_file, required_substrings=["test", "build"])
        return self.run_checks()
