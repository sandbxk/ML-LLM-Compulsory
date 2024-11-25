def calculate_average(numbers):
    total_sum = sum(numbers)
    count = len(numbers)
    return total_sum / count

# Test cases
print(calculate_average([1, 2, 3, 4, 5]))  # Expected output: 3.0
print(calculate_average([10, 20, 30]))     # Expected output: 20.0
print(calculate_average([-5, 5, -10, 10])) # Expected output: 0.0