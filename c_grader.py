import re
import subprocess
import argparse
import os
import importlib.util

# --- Configuration ---
MAX_LINE_LENGTH = 80
DEDUCTIONS = {
    # Formatting
    "inconsistent_indent": (5, "Indentation is inconsistent (mix of tabs and spaces found)."),
    "line_too_long": (5, f"At least one line exceeds {MAX_LINE_LENGTH} characters."),
    "non_ascii": (5, "Non-ASCII characters found in the source code."),
    # Comments
    "missing_header": (5, "Required header comment block is missing or malformed."),
    # Compiling
    "compiles_with_warnings": (10, "Program compiles with warnings."),
    "does_not_compile": (50, "Program does not compile."),
    "segmentation_fault": (30, "Program terminated with a segmentation fault or runtime error."),
    # Correctness
    "no_null_check": (5, "Potential null pointer: malloc/calloc without a subsequent NULL check."),
    "mem_leak": (20, "Potential memory leak: Mismatch between memory allocation and deallocation calls."),
    "failed_tests": (35, "Program produced improper output for one or more test cases.")
}

class CGrader:
    """
    Analyzes a C file against a predefined grading rubric.
    """
    def __init__(self, c_file):
        if not os.path.exists(c_file):
            raise FileNotFoundError(f"Error: The file '{c_file}' was not found.")
        self.c_file = c_file
        self.executable_file = "temp_executable_checker"
        self.report = {
            "total_deduction": 0,
            "details": [],
            "test_report": None,
            "compile_status": None
        }
        self.lines = []
        try:
            with open(self.c_file, 'r', encoding='utf-8', errors='ignore') as f:
                self.lines = f.readlines()
            ''.join(self.lines).encode('ascii')  # check for non-ASCII
        except UnicodeEncodeError:
            self._add_deduction("non_ascii")
        except Exception as e:
            self.report['details'].append(f"Could not read file: {e}")

    def _add_deduction(self, key, extra_info=""):
        """Adds a deduction to the report if not already present."""
        if key not in [item['key'] for item in self.report['details']]:
            points, message = DEDUCTIONS[key]
            self.report["total_deduction"] += points
            self.report["details"].append({
                'key': key,
                'points': points,
                'message': f"{message} {extra_info}".strip()
            })

    def grade(self, test_cases_file=None):
        """Runs all checks and returns the final report dictionary."""
        self._check_formatting()
        self._check_comments()
        self._check_memory()
        compile_status = self._check_compilation()
        self.report["compile_status"] = compile_status

        # ✅ Run tests even if there were warnings
        if compile_status in ("success", "warnings"):
            if test_cases_file:
                self._run_test_cases(test_cases_file)
            else:
                self._check_runtime()

        self._cleanup()
        return self.report

    def _check_formatting(self):
        """Checks for line length and indentation style."""
        has_tabs = False
        has_spaces = False
        for i, line in enumerate(self.lines, 1):
            if len(line.rstrip('\n')) > MAX_LINE_LENGTH:
                self._add_deduction("line_too_long", f"(e.g., line {i})")

            if not has_tabs and line.startswith('\t'):
                has_tabs = True
            if not has_spaces and line.startswith(' '):
                has_spaces = True

        if has_tabs and has_spaces:
            self._add_deduction("inconsistent_indent")

    def _check_comments(self):
        """Checks for the required header comment."""
        content = "".join(self.lines)
        header_pattern = re.compile(
            r'/\*.*?'
            r'CH-230-A\s*\n'
            r'\s*a\d{1,2}_p\d{1,2}(?:_?\d*)\.c[orcpph]*\s*\n'
            r'.+\n'
            r'\s*[\w\.-]+@constructor\.university\s*'
            r'.*?\*/',
            re.DOTALL | re.IGNORECASE
        )
        if not header_pattern.search(content):
            self._add_deduction("missing_header")

    def _check_compilation(self):
        """Tries to compile the C code and captures errors/warnings."""
        try:
            command = ["gcc", "-Wall", self.c_file, "-o", self.executable_file, "-lm"]
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self._add_deduction("does_not_compile", f"\n--- Compiler Output ---\n{result.stderr}")
                return "fail"
            elif result.stderr:
                self._add_deduction("compiles_with_warnings", f"\n--- Compiler Warnings ---\n{result.stderr}")
                return "warnings"
            return "success"
        except FileNotFoundError:
            self.report['details'].append("GCC not found. Please ensure GCC is installed and in your PATH.")
            return "fail"
        except subprocess.TimeoutExpired:
            self._add_deduction("does_not_compile", "Compilation timed out.")
            return "fail"

    def _check_runtime(self):
        """Runs the compiled executable to check for runtime errors."""
        if not os.path.exists(self.executable_file):
            return
        try:
            result = subprocess.run([f"./{self.executable_file}"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0 and result.returncode != 1:
                self._add_deduction("segmentation_fault", f"(program exited with code {result.returncode})")
        except subprocess.TimeoutExpired:
            self._add_deduction("segmentation_fault", "(program timed out during execution)")

    def _check_memory(self):
        """Basic checks for memory usage patterns."""
        content = "".join(self.lines)
        allocs = len(re.findall(r'\bmalloc\b|\bcalloc\b|\brealloc\b', content))
        frees = len(re.findall(r'\bfree\b', content))
        if allocs > frees:
            self._add_deduction("mem_leak", f"({allocs} allocations, {frees} frees)")

        alloc_lines = [i for i, line in enumerate(self.lines) if "malloc" in line or "calloc" in line]
        for line_num in alloc_lines:
            match = re.search(r'(\w+)\s*=\s*\(.*?\*\s*\)\s*(?:malloc|calloc)', self.lines[line_num])
            if not match:
                continue
            var_name = match.group(1)
            found_check = False
            for i in range(line_num + 1, min(line_num + 6, len(self.lines))):
                line = self.lines[i]
                if line.strip() == "":
                    continue
                if "if" in line and (f"{var_name} == NULL" in line or f"!{var_name}" in line):
                    found_check = True
                    break
            if not found_check:
                self._add_deduction("no_null_check", f"(around line {line_num + 1} for variable '{var_name}')")

    def _run_test_cases(self, test_cases_file):
        """Loads and runs the test cases from the specified module."""
        if not os.path.exists(self.executable_file):
            return

        module_name = os.path.splitext(test_cases_file)[0]
        try:
            spec = importlib.util.spec_from_file_location(module_name, test_cases_file)
            test_cases_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_cases_module)

            if hasattr(test_cases_module, 'TestRunner'):
                runner = test_cases_module.TestRunner(self.executable_file)
                test_results = runner.run_all_tests()
                self.report["test_report"] = test_results

                if any(not r['passed'] for r in test_results):
                    self._add_deduction("failed_tests")
            else:
                self.report["test_report"] = [{
                    "name": "Error",
                    "passed": False,
                    "reason": "Could not find 'TestRunner' class in the test case file.",
                    "expected": "",
                    "received": ""
                }]

        except Exception as e:
            self.report["test_report"] = [{
                "name": "Error",
                "passed": False,
                "reason": f"Failed to load or run test cases: {e}",
                "expected": "",
                "received": ""
            }]

    def _cleanup(self):
        """Removes the temporary executable file."""
        if os.path.exists(self.executable_file):
            os.remove(self.executable_file)

def print_report(report, c_file):
    """Prints a formatted grading report."""
    print(f"--- Analyzing {c_file} ---\n")
    if not report["details"] and (not report["test_report"] or all(r.get('passed', False) for r in report["test_report"])):
        print("✅ No issues found by the automated checker.")

    print("--- Grading Report ---")
    print("Initial Score: 100")
    for item in report["details"]:
        print(f"  - {item['points']:<5} | {item['message']}")

    if report["test_report"]:
        passed_count = sum(1 for r in report["test_report"] if r.get('passed', False))
        total_count = len(report["test_report"])
        status_symbol = "⚠️ " if report.get("compile_status") == "warnings" else ""
        print(f"\n--- Test Case Results {status_symbol}---")
        print(f"Summary: {passed_count} / {total_count} tests passed.")
        for res in report["test_report"]:
            if res.get('passed', False):
                print(f"  ✅ PASSED: {res['name']}")
                print(f"     Expected: '{res.get('expected', '').strip()}'")
                print(f"     Received: '{res.get('received', '').strip()}'")
            else:
                print(f"  ❌ FAILED: {res['name']}")
                print(f"     Reason: {res.get('reason', 'N/A')}")
                print(f"     Expected: '{res.get('expected', '').strip()}'")
                print(f"     Received: '{res.get('received', '').strip()}'")

    final_score = max(0, 100 - report["total_deduction"])
    print("--------------------")
    print(f"Total Deduction: {report['total_deduction']}")
    print(f"Final Score (Automated Check): {final_score} / 100")
    print("\nNOTE: Manual grading is still required for logic, variable naming, and correctness not covered by tests.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated C code checker.")
    parser.add_argument("c_file", help="The path to the C file to be graded.")
    parser.add_argument("--tests", "--test-file", dest="tests", help="Optional path to a Python file with test cases.")
    args = parser.parse_args()

    try:
        grader = CGrader(args.c_file)
        final_report = grader.grade(args.tests)
        print_report(final_report, args.c_file)
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
