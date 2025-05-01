import requests
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
            "content": "Please analyze it and suggest a fix for the affected line(s) of code. The error log is as followsHere is the affected code snippet (in context)Please provide the smallest code change necessary to fix the issue, either by modifying the existing line or adding new lines."
          },
          "context": {
            "contentFilters": []
          }
        }
      ]
    }
  }
)
print(response.json())
response_json = response.json()
response_content = response_json['output']['payload']['content']
print(response_content)

  