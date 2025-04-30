import subprocess
import os
import sys
from openai import OpenAI
from github import Github
import re

# Configure GitHub API
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")
BRANCH_NAME = "self-healing-branch"

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

def analyze_with_openai(error_log, affected_code):
    """Analyze error log with OpenAI GPT to suggest fixes for specific lines of code"""
    client = OpenAI()
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Or "gpt-4" if you're using GPT-4
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "The following is an error log from a CI/CD pipeline. Please analyze it and suggest a fix for the affected line(s) of code. The error log is as follows:\n\n{error_log}\n\nHere is the affected code snippet (in context):\n\n{affected_code}\n\nPlease provide the smallest code change necessary to fix the issue, either by modifying the existing line or adding new lines."}
            ],
        )
        # Extracting the response (fix suggestion)
        fixed_code = response.choices[0].message.content
        return fixed_code
    except Exception as e:
        print(f"Error with OpenAI API: {str(e)}")
        return None

def apply_patch(file_path, line_number, fixed_code):
    """Apply the fix to the affected line of the file"""
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Apply the fix only to the affected line or add new lines
    lines[line_number - 1] = fixed_code + '\n'  # Adjust to replace the line

    with open(file_path, "w") as file:
        file.writelines(lines)

def self_heal():
    # Step 1: Check the error type and get logs
    error_log = run_command('cat /home/runner/work/self-heal-CI-CD/self-heal-CI-CD/error.txt')
    print(f"Error Log: {error_log}")

    # Extract file name and line number from the error log using regex
    match = re.search(r'File "([^"]+)", line (\d+)', error_log)
    if match:
        file_name = match.group(1)
        line_number = int(match.group(2))
    else:
        print("Could not parse error log for file and line.")
        return
    
    # Step 2: Extract the affected line(s) of code from the file
    with open(file_name, "r") as file:
        lines = file.readlines()
        affected_code = lines[line_number - 1]  # Extract the affected line

    print(f"Affected file: {file_name}, Line {line_number}")
    print(f"Affected code: {affected_code}")
    
    # Step 3: Use OpenAI to analyze the error and generate the fixed code for that line
    fixed_code = analyze_with_openai(error_log, affected_code)
    if fixed_code:
        print(f"AI generated fix: {fixed_code}")
    else:
        print("No fix suggestion from AI. Manual intervention required.")
        return

    # Step 4: Apply the generated fix to the affected line of the code file
    apply_patch(file_name, line_number, fixed_code)

    # Step 5: Commit and push changes to create a new PR
    run_command('git checkout -b ' + BRANCH_NAME)
    run_command('git add .')
    run_command('git commit -m "Auto-fix applied by GPT"')
    run_command('git push origin ' + BRANCH_NAME)

    # Step 6: Create a Pull Request with the fixes
    pr_url = create_pr(BRANCH_NAME, "Fix based on AI suggestion")
    print(f"PR created: {pr_url}")
    return pr_url

if __name__ == "__main__":
    pr_link = self_heal()
    print(f"Self-healing completed. PR Link: {pr_link}")
