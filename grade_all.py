import os
import re
import subprocess
import argparse
import sys
import shutil

# --- Configuration ---
GRADER_SCRIPT_NAME = "c_grader.py"
OUTPUT_DIR_NAME = "graded_submissions"
REPORT_FILE_NAME = "grading_report.txt"
ASSIGNMENT_FOLDER_NAME = "c_c___f25_a1_p4"  # The specific assignment folder to look for

def find_latest_version_folder(assignment_path):
    """Finds the folder with the highest version number."""
    version_folders = [d for d in os.listdir(assignment_path) if os.path.isdir(os.path.join(assignment_path, d))]
    
    latest_version = -1
    latest_version_path = None
    
    version_pattern = re.compile(r'Version (\d+)', re.IGNORECASE)
    
    for folder in version_folders:
        match = version_pattern.match(folder)
        if match:
            version_num = int(match.group(1))
            if version_num > latest_version:
                latest_version = version_num
                latest_version_path = os.path.join(assignment_path, folder)
                
    return latest_version_path

def find_c_file(directory):
    """Finds the first .c file in a given directory."""
    if not directory or not os.path.isdir(directory):
        return None
    for item in os.listdir(directory):
        if item.lower().endswith('.c'):
            return os.path.join(directory, item)
    return None

def main(source_dir):
    """
    Main function to orchestrate the grading process from a directory of student folders.
    """
    # 1. Validate paths
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory not found at '{source_dir}'")
        sys.exit(1)
    if not os.path.exists(GRADER_SCRIPT_NAME):
        print(f"Error: Grader script '{GRADER_SCRIPT_NAME}' not found.")
        print("Please ensure it's in the same directory as this script.")
        sys.exit(1)

    # 2. Create main output directory
    base_output_dir = os.path.join(os.getcwd(), OUTPUT_DIR_NAME)
    os.makedirs(base_output_dir, exist_ok=True)
    print(f"Created/found output directory: '{base_output_dir}'")

    # 3. Iterate through student folders and grade
    print("\n--- Searching for submissions and running grader ---")
    processed_students = 0
    
    student_folders = [d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))]

    for student_name in student_folders:
        print(f"\nChecking student: {student_name}")
        student_source_path = os.path.join(source_dir, student_name)
        
        # Find the specific assignment folder
        assignment_path = os.path.join(student_source_path, ASSIGNMENT_FOLDER_NAME)
        if not os.path.isdir(assignment_path):
            print(f"  -> Assignment folder '{ASSIGNMENT_FOLDER_NAME}' not found. Skipping.")
            continue
            
        # Find the latest version folder within the assignment folder
        latest_version_path = find_latest_version_folder(assignment_path)
        if not latest_version_path:
            print(f"  -> No 'Version X' folders found in assignment directory. Skipping.")
            continue
        print(f"  -> Found latest version: {os.path.basename(latest_version_path)}")
            
        # Find the .c file in the latest version folder
        c_file_to_grade_path = find_c_file(latest_version_path)
        if not c_file_to_grade_path:
            print(f"  -> No .c file found in the latest version folder. Skipping.")
            continue
        print(f"  -> Found C file: {os.path.basename(c_file_to_grade_path)}")
            
        # Create the student's output directory
        student_output_dir = os.path.join(base_output_dir, student_name)
        os.makedirs(student_output_dir, exist_ok=True)
        
        # Copy the C file to the output directory to keep originals safe
        new_c_file_path = os.path.join(student_output_dir, os.path.basename(c_file_to_grade_path))
        try:
            shutil.copy(c_file_to_grade_path, new_c_file_path)
        except Exception as e:
            print(f"  -> Error copying C file. Skipping. Error: {e}")
            continue

        # Run the c_grader.py script
        try:
            command = [sys.executable, GRADER_SCRIPT_NAME, new_c_file_path]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'
            )
            report_content = result.stdout

        except subprocess.CalledProcessError as e:
            report_content = e.stdout + e.stderr
            print(f"  -> Grader script finished with an error for {student_name} (report generated).")
        except Exception as e:
            print(f"  -> An unexpected error occurred while grading for {student_name}: {e}")
            report_content = f"An unexpected error occurred during grading: {e}"
            
        # Save the report
        report_path = os.path.join(student_output_dir, REPORT_FILE_NAME)
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"  ✅ Report generated at: {report_path}")
            processed_students += 1
        except IOError as e:
            print(f"  ❌ Error writing report for {student_name}: {e}")

    print(f"\n--- Automation Complete ---")
    print(f"Processed {processed_students} submissions.")
    print(f"All graded folders and reports are located in: '{base_output_dir}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automate the grading of C submissions from a directory of student folders.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "source_dir",
        help="The path to the main directory containing all student submission folders."
    )
    args = parser.parse_args()
    main(args.source_dir)

