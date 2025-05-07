def buggy_function():
    print("This is a buggy function")
    print("Result:", result)
    subprocess.run("echo 'Hello, World!'", shell=True)
    print("This line is not executed due to the error")

if __name__ == "__main__":
    buggy_function()
    prinht("This is the main function")
    subprocess.run("echo 'Hello from the main function!'", shell=True)