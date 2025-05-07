import subprocess

def buggy_function():
    print("This is a buggy function")
    result = "No result defined"
    print("Result:", result)
    subprocess.run("echo 'Hello, World!'", shell=True)

if __name__ == "__main__":
    buggy_function()
    print("This is the main function")
    subprocess.run("echo 'Hello from the main function!'", shell=True)