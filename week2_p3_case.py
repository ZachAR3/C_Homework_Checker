import subprocess
import re

class TestRunner:
    """
    A test runner for C programs that require stdin input.
    """
    def __init__(self, executable_path):
        """
        Initializes the test runner.
        Args:
            executable_path (str): The path to the compiled C executable.
        """
        self.executable_path = executable_path
        # A list of all test methods to be run.
        self.tests = [
            self.test_standard_conversion,
            self.test_zero_values,
            self.test_large_values,
        ]

    def _run_single_test(self, test_function):
        """Helper to run one test and handle results."""
        name, test_input, expected_output = test_function()
        
        try:
            # Run the executable, providing the input via stdin.
            # The input must be a string, encoded to bytes.
            result = subprocess.run(
                [f"./{self.executable_path}"],
                input=test_input,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Normalize both outputs by stripping whitespace and keeping only numbers.
            actual_output = ''.join(filter(str.isdigit, result.stdout))
            
            if actual_output == expected_output:
                return {"name": name, "passed": True, "expected": expected_output, "received": actual_output}
            else:
                return {"name": name, "passed": False, "reason": "Output did not match expected value.", "expected": expected_output, "received": actual_output}

        except subprocess.TimeoutExpired:
            return {"name": name, "passed": False, "reason": "Program timed out.", "expected": expected_output, "received": "Timeout"}
        except Exception as e:
            return {"name": name, "passed": False, "reason": f"An error occurred: {e}", "expected": expected_output, "received": "Error"}


    def run_all_tests(self):
        """Runs all tests defined in the self.tests list."""
        results = []
        for test in self.tests:
            results.append(self._run_single_test(test))
        return results

    # --- Test Cases ---

    def test_standard_conversion(self):
        """Tests a standard set of weeks, days, and hours."""
        test_name = "Standard Conversion (1 week, 2 days, 3 hours)"
        # Input format: weeks days hours
        test_input = "1 2 3" 
        # (1 * 168) + (2 * 24) + 3 = 168 + 48 + 3 = 219
        expected_output = "219"
        return test_name, test_input, expected_output

    def test_zero_values(self):
        """Tests with all zero values."""
        test_name = "Zero Values (0 weeks, 0 days, 0 hours)"
        test_input = "0 0 0"
        expected_output = "0"
        return test_name, test_input, expected_output
        
    def test_large_values(self):
        """Tests with larger values."""
        test_name = "Large Values (10 weeks, 5 days, 12 hours)"
        test_input = "10 5 12"
        # (10 * 168) + (5 * 24) + 12 = 1680 + 120 + 12 = 1812
        expected_output = "1812"
        return test_name, test_input, expected_output
