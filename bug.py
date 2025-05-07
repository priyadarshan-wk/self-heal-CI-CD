def calculate_area(radius):
    pi = 3.14
    area = pi * radius * radius
    print(fThe area is: {area})

def calculate_perimeter(radius):
    perimeter = 2 * 3.14 * radius
    print(The perimeter is:, perimeter)

def main():
    radius = 5
    calculate_area(radius)
    calculate_perimeter(radius)
    calculate_area(radius)
    calculate_perimeter(radius)
    if radius > 0:
        print(The radius is positive!)
    else:
        print(The radius is negative!)

def check_radius(radius):
    if radius > 0:
        print(The radius is positive!)
    else:
        print(The radius is negative!)

result = subprocess.run([git, branch], capture_output=True)
print(Current branch:, result.stdout.decode().strip())

check_radius(5)
main()
