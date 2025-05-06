import subprocess
import os
import sys
from openai import OpenAI
from github import Github
import re
import requests
from collections import defaultdict
 
REPO_ROOT = '/home/runner/work/self-heal-CI-CD/self-heal-CI-CD'

# Configure GitHub API
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")
BRANCH_NAME = "self-healing-branch-Sarang-Auto"

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI API
# openai.api_key = OPENAI_API_KEY

# Initialize GitHub API client
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def create_pr(branch_name, message):
    """Create a pull request on GitHub"""
    try:
        base = "main"
        head = branch_name
        print("in create_pr")
        pr = repo.create_pull(title="Auto Fix: " + message,
                               body="Automated fix applied based on CI/CD error",
                               head=head, base=base)
        return pr.html_url
    except Exception as e:
        print(f"Error creating PR: {str(e)}")
        sys.exit(1)

def run_command(command):
    """Helper function to run shell commands"""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return e.stderr.decode('utf-8')

def analyze_with_fab(error_log, affected_code):
    """Analyze error log with OpenAI GPT to suggest fixes for specific lines of code"""
    response = requests.post('https://ybihb67gu2iuqydrxllnml64ku0lbcgt.lambda-url.us-east-1.on.aws/agent/a-demo-priyadarshan/send_message',
    headers={
    'content-type': 'application/json',
    'x-user-id': 'demo-priyadarshan',
    'x-authentication': 'api-key D0D53A3E15AADEDAF56AF13A:94cf03f1599f98793a78a9aa58abca36'
    },

    json={
        "input": {
        "expyId": "",
        "source": "",
        "persistent": False,
        "messages": [
            {
            "role": "user",
            "payload": {
                "content": "Fix this error: " + error_log + "\n\nHere is the affected code snippet (in context):\n" + affected_code + "\n\nPlease provide the smallest code change necessary to fix the issue, either by modifying the existing line or adding new lines. Show only the code that needs to be changed, without any additional explanation or comments. Do not include any other text in the response. Just provide the fixed code snippet."
            },
            "context": {
                "contentFilters": []
            }
            }
        ]
        }
    }
    )
    # Extracting the response (fix suggestion)
    response_json = response.json()
    response_content = response_json['output']['payload']['content']
    return response_content
    # except Exception as e:
    #     print(f"Error with OpenAI API: {str(e)}")
    #     return None

def apply_patch(file_path, line_number, fixed_code):
    """Apply the fix to the affected line of the file"""
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Check if the fix contains multiple lines
    fixed_lines = fixed_code.strip().split('\n')
    
    # Replace the affected line with the fixed code
    if len(fixed_lines) == 1:
        # Single line replacement
        lines[line_number - 1] = fixed_code + '\n'
    else:
        # Multi-line replacement - remove original line and insert new lines
        lines[line_number - 1:line_number] = [line + '\n' for line in fixed_lines]
    
    with open(file_path, "w") as file:
        file.writelines(lines)
    
    print(f"Applied fix to {file_path} at line {line_number}")
    print("cat app.py")
    app_file = run_command('cat /home/runner/work/self-heal-CI-CD/self-heal-CI-CD/app.py')
    print(app_file)

def self_heal():
    error_log = run_command(f'cat {REPO_ROOT}/error.txt')
    print(f"Error Log: {error_log}")
 
    error_matches = re.finditer(r'File "([^"]+)", line (\d+)', error_log)
    errors_by_file = defaultdict(list)
 
    for match in error_matches:
        file_path_raw = match.group(1)
        line_number = int(match.group(2))
 
        # Normalize file path
        file_path = os.path.abspath(os.path.join(REPO_ROOT, file_path_raw))
        errors_by_file[file_path].append(line_number)
 
    print(f"All errors grouped by file:\n{errors_by_file}")
 
    if not errors_by_file:
        print("Could not parse error log for file and line information.")
        return None
 
    fixed_files = set()
 
    for file_path, line_numbers in errors_by_file.items():
        print(f"\nProcessing file: {file_path}")
        try:
            with open(file_path, "r") as file:
                lines = file.readlines()
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            continue
 
        # Sort line numbers in reverse order to avoid offset issues
        line_numbers = sorted(set(line_numbers), reverse=True)
 
        for line_number in line_numbers:
            try:
                affected_code = lines[line_number - 1]
            except IndexError:
                print(f"Invalid line number {line_number} in {file_path}")
                continue
 
            print(f"\nProcessing error at line {line_number}")
            start_line = max(0, line_number - 3)
            end_line = min(len(lines), line_number + 2)
            context_code = "".join(lines[start_line:end_line])
 
            error_context = (
                f"Error in {file_path} at line {line_number}:\n{affected_code}"
                f"\nContext:\n{context_code}"
            )
 
            try:
                fixed_code = analyze_with_fab(error_log, error_context)
            except Exception as e:
                print(f"AI analysis failed for {file_path}, line {line_number}: {e}")
                continue
 
            if fixed_code:
                print(f"Fix from AI:\n{fixed_code}")
                fixed_lines = fixed_code.strip().split('\n')
                if len(fixed_lines) == 1:
                    lines[line_number - 1] = fixed_lines[0] + '\n'
                else:
                    lines[line_number - 1:line_number] = [l + '\n' for l in fixed_lines]
                fixed_files.add(file_path)
            else:
                print(f"No fix returned for {file_path}, line {line_number}")
 
        # Write changes after all lines in the file are patched
        try:
            with open(file_path, "w") as file:
                file.writelines(lines)
            print(f"✅ Applied all fixes to {file_path}")
        except Exception as e:
            print(f"❌ Failed to write file {file_path}: {e}")
 
    if not fixed_files:
        print("No fixes were applied. Manual intervention required.")
        return None
 
    print("git checkout\n" + run_command(f'git checkout -b {BRANCH_NAME}'))
    print("git add .\n" + run_command('git add .'))
    print("git commit\n" + run_command('git commit -m "Auto-fix applied for multiple errors"'))
    print("git push\n" + run_command(f'git push origin {BRANCH_NAME} --force'))
 
    pr_url = create_pr(BRANCH_NAME, f"Fix for multiple errors in {', '.join(fixed_files)}")
    print(f"🚀 PR created: {pr_url}")
    return pr_url

# def self_heal():
#     # Step 1: Check the error type and get logs
#     error_log = run_command('cat /home/runner/work/self-heal-CI-CD/self-heal-CI-CD/error.txt')
#     print(f"Error Log: {error_log}")

#     # Find all error occurrences instead of just one
#     error_matches = re.finditer(r'File "([^"]+)", line (\d+)', error_log)
#     matches_found = False
#     fixed_files = set()
    
#     # Process each error one by one
#     for match in error_matches:
#         matches_found = True
#         file_name = match.group(1)
#         line_number = int(match.group(2))
        
#         # Extract the affected line(s) of code from the file
#         try:
#             with open(file_name, "r") as file:
#                 lines = file.readlines()
#                 affected_code = lines[line_number - 1]  # Extract the affected line
#         except (FileNotFoundError, IndexError) as e:
#             print(f"Error accessing {file_name} at line {line_number}: {str(e)}")
#             continue
            
#         print(f"Processing error - Affected file: {file_name}, Line {line_number}")
#         print(f"Affected code: {affected_code}")
        
#         # Get context for better fixes (a few lines before and after)
#         start_line = max(0, line_number - 3)
#         end_line = min(len(lines), line_number + 2)
#         context_code = "".join(lines[start_line:end_line])
        
#         # Use AI to analyze the error and generate the fixed code
#         error_context = f"Error in {file_name} at line {line_number}:\n{affected_code}\nContext:\n{context_code}"
#         fixed_code = analyze_with_fab(error_log, error_context)
        
#         if fixed_code:
#             print(f"AI generated fix for {file_name}, line {line_number}: {fixed_code}")
#             # Apply the generated fix
#             apply_patch(file_name, line_number, fixed_code)
#             fixed_files.add(file_name)
#         else:
#             print(f"No fix suggestion for error in {file_name}, line {line_number}.")
    
#     if not matches_found:
#         print("Could not parse error log for file and line information.")
#         return None
        
#     if not fixed_files:
#         print("No fixes were applied. Manual intervention required.")
#         return None
        
#     # Create a branch and commit all fixes
#     print("git checkout\n" + run_command('git checkout -b ' + BRANCH_NAME))
#     print("git branch\n" + run_command('git branch'))
#     print("git remote -v\n" + run_command('git remote -v'))
#     print("git add .\n" + run_command('git add .'))
#     print("git commit\n" + run_command(f'git commit -m "Auto-fix applied for multiple errors"'))
#     print("git push\n" + run_command('git push origin ' + BRANCH_NAME + ' --force'))

#     # Create a PR with all the fixes
#     pr_url = create_pr(BRANCH_NAME, f"Fix for multiple errors in {', '.join(fixed_files)}")
#     print(f"PR created: {pr_url}")
#     return pr_url

def set_git_env_vars():
    with open('$GITHUB_ENV', 'a') as f:
        f.write(f'PR_LINK={pr_link}\n')

if __name__ == "__main__":
    pr_link = self_heal()
    print(f"Self-healing completed. PR Link: {pr_link}")
