# tests_p3_8.py
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
        self.executable = executable

    def run_all_tests(self):
        tests = [
            {"name": "two numbers", "input": "1.5\n2.5\n-99.0\n"},
            {"name": "three numbers", "input": "10.0\n20.0\n30.0\n-99.0\n"},
            {"name": "single number", "input": "5.0\n-99.0\n"}
        ]

        results = []
        for t in tests:
            try:
                # parse input floats up to sentinel -99.0
                vals = []
                for line in t["input"].strip().splitlines():
                    try:
                        v = float(line.strip())
                    except:
                        continue
                    if v == -99.0:
                        break
                    vals.append(v)

                if len(vals) == 0:
                    expected_sum = 0.0
                    expected_avg = 0.0
                else:
                    expected_sum = sum(vals)
                    expected_avg = expected_sum / len(vals)

                proc = subprocess.run([f"./{self.executable}"],
                                      input=t["input"],
                                      text=True,
                                      capture_output=True,
                                      timeout=4)
                out = proc.stdout or proc.stderr or ""

                # find numbers in output, attempt to match expected sum & avg
                numbers = extract_numbers(out)
                sum_matched = False
                avg_matched = False
                used_indices = set()
                for i, num in enumerate(numbers):
                    if not sum_matched and math.isclose(num, expected_sum, rel_tol=1e-6, abs_tol=1e-9):
                        sum_matched = True
                        used_indices.add(i)
                for i, num in enumerate(numbers):
                    if i in used_indices:
                        continue
                    if not avg_matched and math.isclose(num, expected_avg, rel_tol=1e-6, abs_tol=1e-9):
                        avg_matched = True
                        used_indices.add(i)

                # fallback: check for formatted substrings "sum=..." or "average=..."
                if not sum_matched:
                    if f"{expected_sum:.6f}" in out:
                        sum_matched = True
                if not avg_matched:
                    if f"{expected_avg:.6f}" in out:
                        avg_matched = True

                passed = sum_matched and avg_matched

                results.append({
                    "name": t["name"],
                    "passed": passed,
                    "expected": f"Sum={expected_sum:.6f} Average={expected_avg:.6f}",
                    "received": out,
                    "reason": "" if passed else f"Expected sum {expected_sum:.6f} and avg {expected_avg:.6f} not both found in output"
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
