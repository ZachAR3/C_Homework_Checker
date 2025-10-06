import subprocess
import re # Import the regular expressions module

class TestRunner:
    """
    A highly flexible test runner using regular expressions to validate output.
    It handles variations in case, whitespace, prompts, and common word swaps
    (like 'and'/'or').
    """
    def __init__(self, executable_path):
        """
        Initializes the test runner.
        Args:
            executable_path (str): The path to the compiled C executable.
        """
        self.executable_path = executable_path
        self.tests = [
            self.test_divisible_by_both,
            self.test_divisible_by_2_not_7,
            self.test_divisible_by_7_not_2,
            self.test_divisible_by_neither,
            self.test_zero,
            self.test_negative_divisible,
        ]

    def _run_single_test(self, test_function):
        """Helper to run one test and handle results using regex."""
        name, test_input, expected_pattern = test_function()
        
        try:
            result = subprocess.run(
                [f"./{self.executable_path}"],
                input=test_input,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Get the student's full output.
            actual_output = result.stdout
            
            # **MODIFICATION**: Use regular expressions for the most flexible check.
            # re.search() finds the pattern anywhere in the string.
            # re.IGNORECASE handles 'NOT' vs 'not'.
            if re.search(expected_pattern, actual_output, re.IGNORECASE):
                return {"name": name, "passed": True, "expected": f"Pattern: /{expected_pattern}/", "received": result.stdout.strip()}
            else:
                reason = "The required output pattern was not found."
                return {"name": name, "passed": False, "reason": reason, "expected": f"Pattern: /{expected_pattern}/", "received": result.stdout.strip()}

        except subprocess.TimeoutExpired:
            return {"name": name, "passed": False, "reason": "Program timed out.", "expected": f"Pattern: /{expected_pattern}/", "received": "Timeout"}
        except Exception as e:
            return {"name": name, "passed": False, "reason": f"An error occurred: {e}", "expected": f"Pattern: /{expected_pattern}/", "received": "Error"}

    def run_all_tests(self):
        """Runs all tests defined in the self.tests list."""
        results = []
        for test in self.tests:
            results.append(self._run_single_test(test))
        return results

    # --- Test Cases for Problem 2.8 ---
    # The expected output is now a regex pattern.

    def test_divisible_by_both(self):
        """Tests a number divisible by both 2 and 7."""
        test_name = "Divisible by Both (14)"
        test_input = "14"
        # This pattern finds the core phrase, ignoring case.
        expected_pattern = r"number is divisible by 2 and 7"
        return test_name, test_input, expected_pattern

    def test_divisible_by_2_not_7(self):
        """Tests a number divisible by 2 but not 7."""
        test_name = "Divisible by 2, Not 7 (10)"
        test_input = "10"
        # This pattern allows for 'and' OR 'or' in the negative case.
        expected_pattern = r"number is not divisible by 2 (and|or) 7"
        return test_name, test_input, expected_pattern
    
    def test_divisible_by_7_not_2(self):
        """Tests a number divisible by 7 but not 2."""
        test_name = "Divisible by 7, Not 2 (21)"
        test_input = "21"
        expected_pattern = r"number is not divisible by 2 (and|or) 7"
        return test_name, test_input, expected_pattern

    def test_divisible_by_neither(self):
        """Tests a number divisible by neither 2 nor 7."""
        test_name = "Divisible by Neither (15)"
        test_input = "15"
        expected_pattern = r"number is not divisible by 2 (and|or) 7"
        return test_name, test_input, expected_pattern

    def test_zero(self):
        """Tests the edge case of 0."""
        test_name = "Zero Value (0)"
        test_input = "0"
        expected_pattern = r"number is divisible by 2 and 7"
        return test_name, test_input, expected_pattern
        
    def test_negative_divisible(self):
        """Tests a negative number that is divisible by both."""
        test_name = "Negative Divisible (-28)"
        test_input = "-28"
        expected_pattern = r"number is divisible by 2 and 7"
        return test_name, test_input, expected_pattern

# --- Example Usage ---
# if __name__ == '__main__':
#     runner = TestRunner('your_executable_name') 
#     test_results = runner.run_all_tests()
#     for result in test_results:
#         print(f"Test: {result['name']}")
#         print(f"  Passed: {result['passed']}")
#         if not result['passed']:
#             print(f"  Reason: {result.get('reason', 'N/A')}")
#             print(f"  Expected to find: {result['expected']}")
#             print(f"  Received: '{result['received']}'")
#         print("-" * 20)