import subprocess
import re

class TestRunner:
    def __init__(self, executable):
        self.executable = executable

    def _normalize(self, s: str) -> str:
        """Normalize output to simplify comparison."""
        s = s.lower()
        s = re.sub(r'[^a-z0-9\s]', ' ', s)  # remove punctuation
        s = re.sub(r'\s+', ' ', s)          # collapse whitespace
        return s.strip()

    def _passes_replacement_test(self, out: str, before: str, after: str) -> bool:
        """
        Pass if the program clearly shows the 'before' and 'after' strings,
        regardless of formatting, wording, or line order.
        """
        out_norm = self._normalize(out)
        before_norm = self._normalize(before)
        after_norm = self._normalize(after)

        # Must include both strings somewhere in output
        if before_norm not in out_norm or after_norm not in out_norm:
            return False

        # Optional sanity check: the 'after' must differ from 'before'
        return before_norm != after_norm

    def run_all_tests(self):
        tests = [
            {
                "name": "replace_vowels",
                "input": "banana\na\no\nstop\n",
                "before": "banana",
                "after": "bonono",
            },
            {
                "name": "replace_letter",
                "input": "hello world\nl\nx\nstop\n",
                "before": "hello world",
                "after": "hexxo worxd",
            },
        ]

        results = []
        for t in tests:
            try:
                proc = subprocess.run(
                    [f"./{self.executable}"],
                    input=t["input"],
                    text=True,
                    capture_output=True,
                    timeout=4,
                )
                out = (proc.stdout or proc.stderr or "").strip()
                passed = self._passes_replacement_test(out, t["before"], t["after"])

                results.append({
                    "name": t["name"],
                    "passed": passed,
                    "expected": f"Before: {t['before']} → After: {t['after']}",
                    "received": out,
                    "reason": "" if passed else "Output missing or mismatched before/after strings.",
                })

            except Exception as e:
                results.append({
                    "name": t["name"],
                    "passed": False,
                    "expected": "",
                    "received": "",
                    "reason": f"Exception while running test: {e}",
                })
        return results
