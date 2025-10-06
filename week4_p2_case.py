import subprocess

class TestRunner:
    def __init__(self, executable):
        self.executable = executable

    def _expected_zigzag(self, text: str):
        """
        Generates expected zig-zag output:
        - Alternate indentation for letters.
        - Blank line for spaces.
        - Indentation resets after a space.
        """
        lines = []
        indent = False  # False = no indent, True = one space
        for c in text:
            if c == '\n':
                break
            if c == ' ':
                lines.append("")      # blank line for space
                indent = False        # reset indentation after space
                continue
            line = (' ' if indent else '') + c
            lines.append(line)
            indent = not indent       # toggle after printing each letter
        return lines

    def run_all_tests(self):
        tests = [
            {"name": "hello_world", "input": "Hello world\n"},
            {"name": "abcd", "input": "ABCD\n"},
        ]

        results = []
        for t in tests:
            try:
                expected_lines = self._expected_zigzag(t["input"])
                proc = subprocess.run(
                    [f"./{self.executable}"],
                    input=t["input"],
                    text=True,
                    capture_output=True,
                    timeout=4
                )
                out_lines = [line.rstrip() for line in proc.stdout.strip().splitlines()]
                passed = out_lines == expected_lines

                results.append({
                    "name": t["name"],
                    "passed": passed,
                    "expected": "\n".join(expected_lines),
                    "received": "\n".join(out_lines),
                    "reason": "" if passed else "Zig-zag indentation pattern incorrect (check reset after space)."
                })

            except Exception as e:
                results.append({
                    "name": t["name"],
                    "passed": False,
                    "expected": "",
                    "received": "",
                    "reason": f"Exception while running test: {e}"
                })
        return results
