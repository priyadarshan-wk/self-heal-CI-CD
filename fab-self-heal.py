import subprocess
import requests
import os

FAB_EXPY_API_KEY = os.getenv("OPENAI_API_KEY")
FAB_EXPY_API_URL = os.getenv("FAB_EXPY_API_URL")

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
                "content": "Fix this error:\n\n" + error_log + "\n\nHere is the affected code snippet (in context):\n" + affected_code + "\n\nPlease provide the smallest code change necessary to fix the issue, either by modifying the existing line or adding new lines. Show full file updated code, without any additional explanation or comments. Do not include any other text in the response. Just provide the fixed updated code."
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
    print("response_content: " + response_content)
    return response_content

def error_and_patch():
    error_log = run_command('cat /home/runner/work/self-heal-CI-CD/self-heal-CI-CD/error.txt')
    print(f"Error Log: {error_log}")
    affected_code = run_command('cat /home/runner/work/self-heal-CI-CD/self-heal-CI-CD/src/bug.py')
    print(f"Affected Code: {affected_code}")
    fixed_code = analyze_with_fab(error_log, affected_code)
    print(f"Fixed Code: {fixed_code}")
    apply_fixed_code = run_command('echo "' + fixed_code + '" > /home/runner/work/self-heal-CI-CD/self-heal-CI-CD/src/bug.py')
    print("show bug.py\n")
    print(run_command('cat /home/runner/work/self-heal-CI-CD/self-heal-CI-CD/src/bug.py'))
    return apply_fixed_code

if __name__ == "__main__":
    error_and_patch()
