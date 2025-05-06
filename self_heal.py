import subprocess
import os
import sys
from openai import OpenAI
from github import Github
import re
import requests

# Configure GitHub API
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")
BRANCH_NAME = "self-healing-branch-saurabh-testing"

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
    # Format the prompt to force a specific response pattern
    prompt = f"""Fix ONLY this specific error: {error_log}

Here is the affected code snippet:
```
{affected_code}
```

IMPORTANT INSTRUCTIONS:
1. Provide ONLY the exact code that should replace the problematic line(s)
2. DO NOT use markdown formatting in your response
3. DO NOT provide any explanations
4. DO NOT suggest multiple alternative fixes
5. DO NOT repeat any previously fixed code
6. Start your response with "CODE_FIX:" and then provide ONLY the fixed code

Example of proper response format:
CODE_FIX:
def example_function():
    fixed_code_here
"""

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
            "persistent": False,  # Ensure no persistence between requests
            "messages": [
                {
                    "role": "user",
                    "payload": {
                        "content": prompt
                    },
                    "context": {
                        "contentFilters": []
                    }
                }
            ]
        }
    })
    
    # Extract and strictly process the response
    try:
        response_json = response.json()
        full_response = response_json['output']['payload']['content']
        print(f"DEBUG - Raw AI response: {full_response}")
        
        # Extract only the code part using a specific marker
        if "CODE_FIX:" in full_response:
            code_only = full_response.split("CODE_FIX:")[1].strip()
        else:
            # Try to extract code between backticks if the AI didn't follow the FORMAT
            code_match = re.search(r'```(?:python)?\s*([\s\S]*?)\s*```', full_response)
            if code_match:
                code_only = code_match.group(1).strip()
            else:
                # Last resort: take everything after any explanations (risky)
                lines = full_response.split('\n')
                code_lines = []
                for line in lines:
                    # Skip obvious explanation lines
                    if line.startswith(('Here', 'This', 'The', 'To fix', 'Fixed', 'I would')):
                        continue
                    if re.match(r'^[\d\.\s]+[A-Z]', line):  # Numbered list items
                        continue
                    if line.strip() and not line.startswith('#'):
                        code_lines.append(line)
                code_only = '\n'.join(code_lines)
        
        # Final cleanup of any remaining markdown or noise
        code_only = re.sub(r'```.*$', '', code_only, flags=re.MULTILINE)
        code_only = re.sub(r'^```.*\n', '', code_only, flags=re.MULTILINE)
        
        print(f"DEBUG - Extracted code fix: {code_only}")
        return code_only.strip()
    except Exception as e:
        print(f"Error processing AI response: {str(e)}")
        print(f"Raw response: {response.text}")
        return None

def apply_patch(file_path, line_number, fixed_code):
    """Apply the fix to the affected line of the file"""
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Check if the fix contains multiple lines
    fixed_lines = fixed_code.strip().split('\n')
    
    # Validate the fix - make sure it doesn't have redundant repetitions
    # Remove duplicate consecutive lines
    unique_lines = []
    for line in fixed_lines:
        if not unique_lines or line.strip() != unique_lines[-1].strip():
            unique_lines.append(line)
            
    # Check indentation consistency (basic validation)
    if len(unique_lines) > 1:
        base_indent = len(unique_lines[0]) - len(unique_lines[0].lstrip())
        for i in range(1, len(unique_lines)):
            curr_indent = len(unique_lines[i]) - len(unique_lines[i].lstrip())
            if curr_indent > base_indent + 4:  # Probably a formatting error
                unique_lines[i] = ' ' * (base_indent + 4) + unique_lines[i].lstrip()
    
    # Replace the affected line with the fixed code
    if len(unique_lines) == 1:
        # Single line replacement
        lines[line_number - 1] = unique_lines[0] + '\n'
    else:
        # Multi-line replacement - remove original line and insert new lines
        lines[line_number - 1:line_number] = [line + '\n' for line in unique_lines]
    
    with open(file_path, "w") as file:
        file.writelines(lines)
    
    print(f"Applied fix to {file_path} at line {line_number}")
    print(f"New code (after cleanup):")
    for line in unique_lines:
        print(f"  {line}")
    if file_path.endswith('app.py'):
        app_file = run_command('cat /home/runner/work/self-heal-CI-CD/self-heal-CI-CD/app.py')
        print("Current app.py content:")
        print(app_file)

def self_heal():
    # Initialize variables
    fixed_files = set()
    max_iterations = 5  # Prevent infinite loops if something goes wrong
    iteration = 0
    has_errors = True
    
    while has_errors and iteration < max_iterations:
        iteration += 1
        print(f"\n===== Starting iteration {iteration} =====")
        
        # Run the script to generate fresh error log
        if iteration > 1:
            error_result = run_command('python3 bug.py > /home/runner/work/self-heal-CI-CD/self-heal-CI-CD/error.txt 2>&1')
            print(f"Script run result: {error_result if error_result else 'No output'}")
        
        # Read the current error log
        error_log = run_command('cat /home/runner/work/self-heal-CI-CD/self-heal-CI-CD/error.txt')
        print(f"Error Log: {error_log}")
        
        # Check if there are any errors left
        if "Error" not in error_log and "error" not in error_log.lower():
            print("No more errors detected!")
            has_errors = False
            break
            
        # Find the first error occurrence (fix one error at a time)
        match = re.search(r'File "([^"]+)", line (\d+)', error_log)
        if not match:
            print("Could not parse error log for file and line. Stopping iterations.")
            break
            
        file_name = match.group(1)
        line_number = int(match.group(2))
        
        # Extract the affected line(s) of code from the file
        try:
            with open(file_name, "r") as file:
                lines = file.readlines()
                affected_code = lines[line_number - 1]  # Extract the affected line
        except (FileNotFoundError, IndexError) as e:
            print(f"Error accessing {file_name} at line {line_number}: {str(e)}")
            break
            
        print(f"Processing error - Affected file: {file_name}, Line {line_number}")
        print(f"Affected code: {affected_code}")
        
        # Get context for better fixes (a few lines before and after)
        start_line = max(0, line_number - 3)
        end_line = min(len(lines), line_number + 2)
        context_code = "".join(lines[start_line:end_line])
        
        # Use AI to analyze the error and generate the fixed code
        error_context = f"Error in {file_name} at line {line_number}:\n{affected_code}\nContext:\n{context_code}"
        fixed_code = analyze_with_fab(error_log, error_context)
        
        if fixed_code:
            print(f"AI generated fix for {file_name}, line {line_number}: {fixed_code}")
            # Apply the generated fix
            apply_patch(file_name, line_number, fixed_code)
            fixed_files.add(file_name)
        else:
            print(f"No fix suggestion for error in {file_name}, line {line_number}. Stopping iterations.")
            break
    
    if not fixed_files:
        print("No fixes were applied. Manual intervention required.")
        return None
        
    # Create a branch and commit all fixes
    print("git checkout\n" + run_command('git checkout -b ' + BRANCH_NAME))
    print("git branch\n" + run_command('git branch'))
    print("git remote -v\n" + run_command('git remote -v'))
    print("git add .\n" + run_command('git add .'))
    print("git commit\n" + run_command(f'git commit -m "Auto-fix applied for multiple errors - {iteration} iterations"'))
    print("git push\n" + run_command('git push origin ' + BRANCH_NAME + ' --force'))

    # Create a PR with all the fixes
    pr_url = create_pr(BRANCH_NAME, f"Fix for multiple errors in {', '.join(fixed_files)} ({iteration} iterations)")
    print(f"PR created: {pr_url}")
    return pr_url

def set_git_env_vars():
    with open('$GITHUB_ENV', 'a') as f:
        f.write(f'PR_LINK={pr_link}\n')

if __name__ == "__main__":
    pr_link = self_heal()
    print(f"Self-healing completed. PR Link: {pr_link}")
