import subprocess

class TestRunner:
    def __init__(self, executable):
        self.executable = executable

    def run_all_tests(self):
        tests = [
            {
                "name": "3x3_matrix",
                "input": "3\n1\n2\n3\n4\n5\n6\n7\n8\n9\n",
                "expected_matrix": ["1 2 3", "4 5 6", "7 8 9"],
                "expected_under": ["4 7 8"]
            },
            {
                "name": "4x4_matrix",
                "input": (
                    "4\n"
                    "1\n2\n3\n4\n"
                    "5\n6\n7\n8\n"
                    "9\n10\n11\n12\n"
                    "13\n14\n15\n16\n"
                ),
                "expected_matrix": [
                    "1 2 3 4",
                    "5 6 7 8",
                    "9 10 11 12",
                    "13 14 15 16"
                ],
                # Elements under the main diagonal (i>j):
                # (2,1)=5, (3,1)=9, (3,2)=10, (4,1)=13, (4,2)=14, (4,3)=15
                "expected_under": ["5 9 10 13 14 15"]
            }
        ]

        results = []
        for t in tests:
            try:
                proc = subprocess.run(
                    [f"./{self.executable}"],
                    input=t["input"],
                    text=True,
                    capture_output=True,
                    timeout=4
                )
                out = proc.stdout.strip()

                # Check matrix content
                matrix_ok = all(line in out for line in t["expected_matrix"])
                # Check values under the main diagonal
                under_ok = any(" ".join(t["expected_under"]).split()[0] in out for _ in [0])
                # To make it stricter, look for the actual sequence
                under_ok = any(" ".join(t["expected_under"]).strip() in line for line in out.splitlines())

                passed = matrix_ok and under_ok

                results.append({
                    "name": t["name"],
                    "passed": passed,
                    "expected": (
                        "The entered matrix is:\n" +
                        "\n".join(t["expected_matrix"]) +
                        "\nUnder the main diagonal:\n" +
                        " ".join(t["expected_under"])
                    ),
                    "received": out,
                    "reason": "" if passed else "Matrix or under-diagonal elements incorrect."
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
