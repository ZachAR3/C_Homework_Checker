import re
import subprocess

class TestCase:
    """
    A base class for running a single test case on a C executable.
    """
    def __init__(self, name, description, executable, expected_output, input_data=None):
        self.name = name
        self.description = description
        self.executable = executable
        self.expected_output = expected_output
        self.input_data = input_data

    def _normalize_output_for_comparison(self, output):
        """
        Extracts all numbers (integers and floats) from a string and returns them as a list of strings.
        This makes the comparison robust against variations in text and spacing.
        """
        # This regex finds integers and floating-point numbers.
        return re.findall(r'-?\d+\.\d+|-?\d+', output)

    def run(self):
        """
        Runs the test case and compares the actual output with the expected output.
        Returns a tuple: (passed, reason, actual_output).
        """
        try:
            result = subprocess.run(
                [f"./{self.executable}"],
                input=self.input_data,
                capture_output=True,
                text=True,
                timeout=5
            )
            actual_output = result.stdout.strip().replace('\r\n', '\n')

            # Normalize both expected and actual output to compare only numbers
            expected_normalized = self._normalize_output_for_comparison(self.expected_output)
            actual_normalized = self._normalize_output_for_comparison(actual_output)

            if expected_normalized == actual_normalized:
                return (True, "Output matched expected values.", actual_output)
            else:
                reason = "Numerical output did not match expected values."
                return (False, reason, actual_output)

        except subprocess.TimeoutExpired:
            return (False, "Execution timed out (possible infinite loop).", "")
        except Exception as e:
            return (False, f"An unexpected error occurred during execution: {e}", "")


class TestRunner:
    """
    Manages and runs a collection of test cases for a specific assignment.
    """
    def __init__(self, executable_file):
        self.executable = executable_file
        self.tests = self._get_test_cases()

    def _get_test_cases(self):
        """
        Defines all the test cases for the specific assignment.
        This is the primary method to edit when adding new tests.
        """
        return [
            TestCase(
                name="test_arithmetic_operations_p4",
                description="Checks the output of basic arithmetic operations.",
                executable=self.executable,
                expected_output="""
                x=17
                y=4
                sum=21
                product=68
                difference=13
                division=4.250000
                remainder of division=1
                """,
                input_data=None  # No input required for this test
            ),
            # You can add more TestCase objects here for other tests
        ]

    def run_all_tests(self):
        """
        Runs all defined test cases and returns a list of results.
        """
        results = []
        for test in self.tests:
            passed, reason, actual_output = test.run()
            results.append({
                "name": test.name,
                "passed": passed,
                "reason": reason,
                "expected": test.expected_output,
                "received": actual_output
            })
        return results

