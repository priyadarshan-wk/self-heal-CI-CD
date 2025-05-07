import subprocess

def buggy_function():
    print("This is a buggy function")
    result = "some value"  # Define 'result' before using it
    print("Result:", result)
    subprocess.run("echo 'Hello, World!'", shell=True)
    print("This line is not executed due to the error")

if __name__ == "__main__":
    buggy_function()
    print("This is the main function")
    subprocess.run("echo 'Hello from the main function!'", shell=True)