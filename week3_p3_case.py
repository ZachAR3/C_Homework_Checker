# tests_p3_3.py
import subprocess
import re
import math

NUM_RE = re.compile(r'[-+]?\d*\.\d+|[-+]?\d+')

def extract_numbers(s):
    return [float(x) for x in NUM_RE.findall(s)]

def normalize(s: str) -> str:
    return re.sub(r'\s+', ' ', s.strip()).lower()

class TestRunner:
    def __init__(self, executable):
        # grader passes something like "temp_executable_checker"
        self.executable = executable

    def run_all_tests(self):
        tests = [
            {"name": "cm=12", "input": "12\n"},
            {"name": "cm=100000", "input": "100000\n"}
        ]

        results = []
        for t in tests:
            try:
                # parse cm from the test input
                m = re.search(r'[-+]?\d+', t["input"])
                if not m:
                    results.append({
                        "name": t["name"],
                        "passed": False,
                        "expected": "",
                        "received": "",
                        "reason": "Could not parse integer cm from test input"
                    })
                    continue
                cm = int(m.group())
                expected_km = cm / 100000.0  # correct conversion: 100000 cm = 1 km

                proc = subprocess.run([f"./{self.executable}"],
                                      input=t["input"],
                                      text=True,
                                      capture_output=True,
                                      timeout=4)
                out = proc.stdout or proc.stderr or ""

                # extract any numbers from output and try to match expected_km
                numbers = extract_numbers(out)
                matched = False
                for num in numbers:
                    if math.isclose(num, expected_km, rel_tol=1e-6, abs_tol=1e-9):
                        matched = True
                        break

                # fallback: check for formatted expected substring (normalized)
                if not matched:
                    if f"{expected_km:.6f}" in out:
                        matched = True

                # final fallback: substring fuzzy match of verbal phrase
                if not matched:
                    expected_phrase = f"result of conversion: {expected_km:.6f}"
                    if expected_phrase in normalize(out):
                        matched = True

                results.append({
                    "name": t["name"],
                    "passed": matched,
                    "expected": f"{expected_km:.6f}",
                    "received": out,
                    "reason": "" if matched else f"Expected km approx {expected_km:.6f} not found in output"
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
