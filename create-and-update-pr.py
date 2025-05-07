import os
import sys
import subprocess
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")
BRANCH_NAME = "self-heal-branch"

# Initialize GitHub API client
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def run_command(command):
    """Helper function to run shell commands"""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return e.stderr.decode('utf-8')

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

def create_or_update_branch():
    # Create a branch and commit all fixes
    print("git checkout\n" + run_command('git checkout -b ' + BRANCH_NAME))
    print("git branch\n" + run_command('git branch'))
    print("git remote -v\n" + run_command('git remote -v'))
    print("git add .\n" + run_command('git add .'))
    print("git commit\n" + run_command(f'git commit -m "Auto-fix applied for multiple errors"'))
    
    
    #check remote branch exists
    check_remote_branch = run_command('git ls-remote --heads origin ' + BRANCH_NAME)
    if not check_remote_branch:
        # Step 6: Create a Pull Request with the fixes
        print("git push\n" + run_command('git push origin ' + BRANCH_NAME + ' --force'))
        pr_url = create_pr(BRANCH_NAME, "Fix based on AI suggestion")
        print(f"PR created: {pr_url}")
        print("GUITHUB_ENV\n" + os.environ["GITHUB_ENV"])
        with open(os.environ["GITHUB_ENV"], "a") as f:
            f.write(f"PR_URL={pr_url}\n")
        return pr_url
    else:
        print("git push\n" + run_command('git push origin ' + BRANCH_NAME + ' --force'))
        print("Remote branch already exists. No new PR created.")
        return None

if __name__ == "__main__":
    create_or_update_branch()