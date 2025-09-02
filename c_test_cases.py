import subprocess
import os

class TestRunner:
    """
    A helper class to run a compiled C executable and check its output.
    """
    def __init__(self, executable_path):
        if not os.path.exists(executable_path):
            raise FileNotFoundError(f"Executable not found at {executable_path}")
        self.executable_path = executable_path
        
    def run(self, test_input, expected_output, timeout=5):
        """
        Runs the executable with given input and compares its output.
        
        Args:
            test_input (str): The string to be passed to the program's stdin.
            expected_output (str): The exact string expected from the program's stdout.
            timeout (int): Seconds to wait before timing out.
            
        Returns:
            dict: A dictionary containing the test result.
        """
        try:
            process = subprocess.run(
                [self.executable_path],
                input=test_input,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )
            
            # Normalize whitespace for comparison (strips leading/trailing and replaces multiple newlines)
            actual_output = process.stdout.strip().replace('\r\n', '\n')
            expected_output_normalized = expected_output.strip().replace('\r\n', '\n')

            if actual_output == expected_output_normalized:
                return {"passed": True, "reason": "Output matched expected result."}
            else:
                return {
                    "passed": False,
                    "reason": "Output did not match expected result.",
                    "expected": expected_output_normalized,
                    "received": actual_output
                }

        except subprocess.TimeoutExpired:
            return {"passed": False, "reason": "Test timed out (possible infinite loop)."}
        except Exception as e:
            return {"passed": False, "reason": f"An error occurred during execution: {e}"}

# ==============================================================================
# == EDIT THIS CLASS TO CREATE YOUR TEST CASES FOR THE ASSIGNMENT ==
# ==============================================================================
class AssignmentTests:
    """
    Contains all test cases for a specific assignment.
    The grader will automatically run any method that starts with 'test_'.
    """
    def __init__(self, runner: TestRunner):
        self.runner = runner
        # Per-test-case point deduction for failures.
        self.points_per_test = 5

    def test_case_1_example_addition(self):
        """
        Description: Tests basic addition.
        Input: Two positive integers.
        Expected Output: The sum of the two integers.
        """
        # --- Test Data ---
        test_input = "5\n10\n"
        expected_output = "Sum: 15"
        
        # --- Run Test ---
        return self.runner.run(test_input, expected_output)

    def test_case_2_example_edge_case(self):
        """
        Description: Tests with zero values.
        Input: Zero and a positive integer.
        Expected Output: The sum.
        """
        # --- Test Data ---
        test_input = "0\n7\n"
        expected_output = "Sum: 7"
        
        # --- Run Test ---
        return self.runner.run(test_input, expected_output)

    # --- Add more test cases below as needed ---
    # def test_case_3_another_one(self):
    #     test_input = "...\n"
    #     expected_output = "..."
    #     return self.runner.run(test_input, expected_output)
