// Comprehensive test for Small-C Interpreter
// Tests all major features

// Test 1: Basic arithmetic
int test_arithmetic() {
    return 10 + 5 * 2 - 3;  // Should be 17
}

// Test 2: Fibonacci
int fib(int n) {
    if (n <= 1) return n;
    return fib(n-1) + fib(n-2);
}

// Test 3: Max function
int max(int a, int b) {
    if (a > b) return a;
    return b;
}

// Test 4: Factorial
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n-1);
}

// Test 5: Loop and variables
int sum_to_n(int n) {
    int sum = 0;
    int i = 1;
    while (i <= n) {
        sum = sum + i;
        i = i + 1;
    }
    return sum;
}

// Test 6: Logical operators
int test_logic() {
    if (5 > 3 && 2 < 4) {
        return 1;
    }
    return 0;
}

// Test 7: Comparison operators
int test_compare() {
    if (10 == 10) return 1;
    if (5 != 5) return 0;
    if (3 < 5) return 1;
    return 0;
}

// Main test runner
int main() {
    // Test arithmetic
    printf(test_arithmetic());      // 17
    
    // Test fibonacci
    printf(fib(8));                 // 21
    
    // Test max
    printf(max(15, 9));             // 15
    
    // Test factorial
    printf(factorial(5));           // 120
    
    // Test loop
    printf(sum_to_n(10));           // 55
    
    // Test logic
    printf(test_logic());           // 1
    
    // Test compare
    printf(test_compare());         // 1
}
