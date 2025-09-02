import re
import subprocess
import argparse
import os
import sys
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
    "improper_output": (35, "Program produced improper output for one or more test cases.")
}

class CGrader:
    """
    Analyzes a C file against a predefined grading rubric.
    """
    def __init__(self, c_file, test_file=None):
        if not os.path.exists(c_file):
            raise FileNotFoundError(f"Error: The file '{c_file}' was not found.")
        self.c_file = c_file
        # Place executable next to the C file to avoid permission issues in restricted directories
        self.executable_file = os.path.join(os.path.dirname(c_file), "temp_executable_checker")
        self.report = {
            "total_deduction": 0,
            "details": [],
            "test_summary": []
        }
        self.lines = []
        self.test_module = None
        self.test_file = test_file

        # Load test cases if a file is provided
        if self.test_file:
            self._load_test_module()

        try:
            with open(self.c_file, 'r', encoding='utf-8') as f:
                self.lines = f.readlines()
            # Check for non-ascii characters by trying to encode with 'ascii'
            ''.join(self.lines).encode('ascii')
        except UnicodeEncodeError:
            self._add_deduction("non_ascii")
        except Exception as e:
            self.report['details'].append(f"Could not read file: {e}")

    def _load_test_module(self):
        if not os.path.exists(self.test_file):
            print(f"Warning: Test file '{self.test_file}' not found. Skipping tests.")
            self.test_file = None
            return
        try:
            spec = importlib.util.spec_from_file_location("c_test_cases", self.test_file)
            self.test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.test_module)
            print(f"Successfully loaded test cases from '{self.test_file}'")
        except Exception as e:
            print(f"Error loading test file '{self.test_file}': {e}. Skipping tests.")
            self.test_module = None
            self.test_file = None

    def _add_deduction(self, key, extra_info=""):
        """Adds a deduction to the report."""
        points, message = DEDUCTIONS[key]
        
        self.report["total_deduction"] += points
        self.report["details"].append({
            'key': key,
            'points': points,
            'message': f"{message} {extra_info}".strip()
        })

    def check_all(self):
        """Runs all checks and prints the final report."""
        print(f"--- Analyzing {os.path.basename(self.c_file)} ---")
        self._check_formatting()
        self._check_comments()
        self._check_memory()
        compile_status = self._check_compilation()

        if compile_status == "success":
             self._check_runtime()
             if self.test_file and os.path.exists(self.executable_file):
                 self._run_test_cases()
                 # If any test failed, apply the single 35% deduction
                 if any(not t.get('passed', False) for t in self.report['test_summary']):
                     if 'improper_output' not in [d['key'] for d in self.report['details']]:
                         self._add_deduction('improper_output')

        self._print_report()
        self._cleanup()

    def _check_formatting(self):
        """Checks for line length and indentation style."""
        has_tabs = False
        has_spaces = False
        for i, line in enumerate(self.lines, 1):
            if len(line.rstrip('\n')) > MAX_LINE_LENGTH:
                if 'line_too_long' not in [d['key'] for d in self.report['details']]:
                    self._add_deduction("line_too_long", extra_info=f"(e.g., line {i})")

            if not has_tabs and line.startswith('\t'):
                has_tabs = True
            if not has_spaces and line.startswith(' '):
                has_spaces = True

        if has_tabs and has_spaces:
            self._add_deduction("inconsistent_indent")

    def _check_comments(self):
        """Checks for the required header comment."""
        content = "".join(self.lines)
        # Regex to find the header block with a specific line-by-line structure.
        header_pattern = re.compile(
            r'/\*\s*'
            r'CH-230-A\s*\n\s*'
            r'a\d+_p\d+\.(?:c|cpp|h)\s*\n\s*'
            r'.+\s*\n\s*'
            r'.+@constructor\.university\s*'
            r'\*/',
            re.IGNORECASE
        )
        if not header_pattern.search(content):
            self._add_deduction("missing_header")

    def _check_compilation(self):
        """Tries to compile the C code and captures errors/warnings."""
        try:
            command = [
                "gcc", "-Wall", "-Wextra", "-pedantic",
                self.c_file, "-o", self.executable_file, "-lm"
            ]
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                self._add_deduction("does_not_compile", extra_info=f"\n--- Compiler Output ---\n{result.stderr}")
                return "fail"
            elif result.stderr:
                self._add_deduction("compiles_with_warnings", extra_info=f"\n--- Compiler Warnings ---\n{result.stderr}")
                return "warnings"
            return "success"
        except FileNotFoundError:
            self.report['details'].append({'key': 'gcc_not_found', 'points': 0, 'message': "GCC not found. Please ensure GCC is installed and in your PATH."})
            return "fail"
        except subprocess.TimeoutExpired:
            self._add_deduction("does_not_compile", extra_info="Compilation timed out.")
            return "fail"

    def _check_runtime(self):
        """Runs the compiled executable to check for runtime errors like segfaults."""
        if not os.path.exists(self.executable_file):
            return
        try:
            result = subprocess.run(
                [self.executable_file], input="", capture_output=True, text=True, timeout=5
            )
            if result.returncode not in [0, 1]:
                 self._add_deduction("segmentation_fault", extra_info=f"(program exited with code {result.returncode} on simple run)")
        except subprocess.TimeoutExpired:
            self._add_deduction("segmentation_fault", extra_info="(program timed out during basic execution)")
        except Exception as e:
            self._add_deduction("segmentation_fault", extra_info=f"(an error occurred while running: {e})")

    def _check_memory(self):
        """Performs basic checks for memory management best practices."""
        content = "".join(self.lines)
        allocs = len(re.findall(r'\bmalloc\b|\bcalloc\b|\brealloc\b', content))
        frees = len(re.findall(r'\bfree\b', content))

        if allocs > frees:
            self._add_deduction("mem_leak", extra_info=f"({allocs} allocations, {frees} frees)")

        alloc_lines = [i for i, line in enumerate(self.lines) if "malloc" in line or "calloc" in line]

        for line_num in alloc_lines:
            match = re.search(r'(\w+)\s*=\s*\(.*?\*\s*\)\s*(?:malloc|calloc)', self.lines[line_num])
            if not match:
                continue

            var_name = match.group(1)
            found_check = False
            for i in range(line_num + 1, min(line_num + 6, len(self.lines))):
                line = self.lines[i]
                if line.strip() == "": continue
                if f"if" in line and (f"{var_name} == NULL" in line or f"!{var_name}" in line):
                    found_check = True
                    break
            if not found_check:
                if 'no_null_check' not in [d['key'] for d in self.report['details']]:
                    self._add_deduction("no_null_check", extra_info=f"(e.g., around line {line_num + 1} for variable '{var_name}')")

    def _run_test_cases(self):
        """Initializes and runs all test cases from the loaded module."""
        runner = self.test_module.TestRunner(self.executable_file)
        assignment_tests = self.test_module.AssignmentTests(runner)
        
        test_methods = [
            method for method in dir(assignment_tests)
            if callable(getattr(assignment_tests, method)) and method.startswith("test_")
        ]

        if not test_methods:
            print("Warning: No methods starting with 'test_' found in AssignmentTests class.")
            return

        for test_name in test_methods:
            test_func = getattr(assignment_tests, test_name)
            result = test_func()
            result['name'] = test_name
            self.report['test_summary'].append(result)

    def _print_report(self):
        """Prints the final formatted report."""
        print("\n--- Grading Report ---")
        if not self.report["details"] and all(t.get('passed', False) for t in self.report['test_summary']):
            print("✅ No issues found by the automated checker.")
            if self.report['test_summary']:
                print(f"✅ All {len(self.report['test_summary'])} test cases passed.")
            print("Final Score: 100 / 100")
            print("\nNOTE: Manual grading is still required for aspects not covered by this script.")
            return

        print(f"Initial Score: 100")
        for item in self.report["details"]:
            print(f"  - {item['points']:<5} | {item['message']}")

        if self.report['test_summary']:
            print("\n--- Test Case Results ---")
            passed_count = sum(1 for t in self.report['test_summary'] if t['passed'])
            total_count = len(self.report['test_summary'])
            print(f"Summary: {passed_count} / {total_count} tests passed.")

            for test in self.report['test_summary']:
                if not test['passed']:
                    print(f"  ❌ FAILED: {test['name']}")
                    print(f"     Reason: {test['reason']}")
                    if 'expected' in test:
                        print(f"     Expected: {repr(test['expected'])}")
                        print(f"     Received: {repr(test['received'])}")

        final_score = max(0, 100 - self.report["total_deduction"])
        print("--------------------")
        print(f"Total Deduction: {self.report['total_deduction']}")
        print(f"Final Score (Automated Check): {final_score} / 100")
        print("\nNOTE: Manual grading is still required for logic, variable naming, and correctness not covered by tests.")

    def _cleanup(self):
        """Removes the temporary executable file."""
        if os.path.exists(self.executable_file):
            try:
                os.remove(self.executable_file)
            except OSError as e:
                print(f"Warning: Could not remove temporary file {self.executable_file}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automated C code checker based on a grading rubric.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("c_file", help="The path to the C file to be graded.")
    parser.add_argument("--test-file", help="Optional path to a Python file containing test cases.")
    args = parser.parse_args()

    try:
        grader = CGrader(args.c_file, args.test_file)
        grader.check_all()
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


