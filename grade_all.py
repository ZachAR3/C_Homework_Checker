import os
import sys
import pandas as pd
import subprocess
import argparse
import shutil

def get_students_to_grade(excel_path):
    """Reads the Excel file to find students with a 'Turned in' status."""
    try:
        df = None
        # Search the first 10 rows for the header
        for i in range(10):
            try:
                temp_df = pd.read_excel(excel_path, header=i)
                if 'Full Name' in temp_df.columns and 'Status' in temp_df.columns:
                    df = temp_df
                    break
            except Exception:
                continue
        
        if df is None:
            print(f"Error: Excel file '{excel_path}' is missing 'Full Name' or 'Status' columns in the first 10 rows.")
            sys.exit(1)

        submitted_df = df[df['Status'] == 'Turned in']
        return set(submitted_df['Full Name'])
    except FileNotFoundError:
        print(f"Error: The Excel file '{excel_path}' was not found. Grading will be skipped.")
        return set()
    except Exception as e:
        print(f"An error occurred while reading the Excel file: {e}")
        return set()

def grade_directory(directory_path, test_cases_file):
    """Grades all valid student submissions in a directory."""
    excel_path = "status_list.xlsx"
    students_to_grade = get_students_to_grade(excel_path)
    
    if not students_to_grade:
        print("No students to grade based on the Excel sheet. Exiting.")
        return

    print(f"Found {len(students_to_grade)} students marked as 'Turned in' to grade.")

    # Create a main directory for all reports
    main_reports_dir = "grading_reports"
    os.makedirs(main_reports_dir, exist_ok=True)

    for student_folder_name in os.listdir(directory_path):
        full_student_path = os.path.join(directory_path, student_folder_name)

        if not os.path.isdir(full_student_path):
            continue

        # Handle "Last Name, First Name" folder format
        parts = [p.strip() for p in student_folder_name.split(',')]
        student_name = f"{parts[1]} {parts[0]}" if len(parts) == 2 else student_folder_name
            
        if student_name in students_to_grade:
            assignment_folder = os.path.join(full_student_path, 'c_c___f25_a1_p4')
            if not os.path.exists(assignment_folder):
                continue

            # Find the latest version folder
            latest_version_folder = ''
            latest_version_num = -1
            for item in os.listdir(assignment_folder):
                version_path = os.path.join(assignment_folder, item)
                if os.path.isdir(version_path) and item.lower().startswith('version '):
                    try:
                        version_num = int(item.split(' ')[1])
                        if version_num > latest_version_num:
                            latest_version_num = version_num
                            latest_version_folder = version_path
                    except (ValueError, IndexError):
                        continue
            
            if not latest_version_folder:
                continue

            # Find the .c file in the latest version folder
            c_file_path = None
            for file in os.listdir(latest_version_folder):
                if file.endswith('.c'):
                    c_file_path = os.path.join(latest_version_folder, file)
                    break 
            
            if c_file_path:
                print(f"Grading: {student_folder_name}...")

                # Create a dedicated report folder for the student
                student_report_dir = os.path.join(main_reports_dir, student_folder_name)
                os.makedirs(student_report_dir, exist_ok=True)

                # Copy the original C file to the report folder
                shutil.copy(c_file_path, student_report_dir)

                try:
                    command = ["python3", "c_grader.py", c_file_path]
                    if test_cases_file:
                        command.extend(["--tests", test_cases_file])
                    
                    # Run the grader and capture its output
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        check=False # Do not raise an exception on non-zero exit codes
                    )
                    
                    # Combine stdout and stderr for a complete report
                    report_content = result.stdout
                    if result.stderr:
                        report_content += f"\n--- SCRIPT ERRORS ---\n{result.stderr}"

                    # Write the captured output to a report file
                    report_file_path = os.path.join(student_report_dir, 'report.txt')
                    with open(report_file_path, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                    
                    print(f" -> Report saved in '{student_report_dir}/'")

                except Exception as e:
                    print(f"   -> An unexpected error occurred: {e}")

def grade_single_file(file_path, test_cases_file):
    """Grades a single C file and prints the output to the console."""
    print(f"--- Grading Single File: {os.path.basename(file_path)} ---")
    try:
        command = ["python3", "c_grader.py", file_path]
        if test_cases_file:
            command.extend(["--tests", test_cases_file])
        # Run and print directly to console
        subprocess.run(command, check=True)
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Master script to grade C submissions. Can handle a directory of submissions or a single file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("path", help="Path to the submissions directory or a single .c file.")
    parser.add_argument("--tests", help="Optional: Path to a Python file with test cases.")
    args = parser.parse_args()

    if os.path.isfile(args.path) and args.path.endswith('.c'):
        grade_single_file(args.path, args.tests)
    elif os.path.isdir(args.path):
        grade_directory(args.path, args.tests)
    else:
        print(f"Error: The path '{args.path}' is not a valid directory or .c file.")
        sys.exit(1)

if __name__ == "__main__":
    main()

