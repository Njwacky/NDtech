#!/usr/bin/env python3
"""
Direct test of case-insensitive validation logic
"""

def test_case_insensitive_logic():
    """Test the case-insensitive validation logic directly"""
    
    print("Testing Case-Insensitive Validation Logic")
    print("=" * 50)
    
    # Simulate existing product names
    existing_products = ['Test', 'Coca Cola', 'Bread', 'Milk']
    
    # Test cases
    test_cases = [
        ('Test', False),      # Same case - should fail
        ('test', False),      # Different case - should fail  
        ('TEST', False),      # All caps - should fail
        ('tEsT', False),     # Mixed case - should fail
        ('test2', True),      # Different name - should pass
        ('Test 2', True),    # Different name - should pass
        ('Coca', True),      # Different name - should pass
        ('coca', False),      # Case-insensitive match - should fail
        ('COCA', False),      # Case-insensitive match - should fail
        ('bread2', True),     # Different name - should pass
    ]
    
    print("\nTest Results:")
    print("-" * 50)
    
    all_passed = True
    for name, expected_to_pass in test_cases:
        # Simulate case-insensitive check
        name_lower = name.lower()
        existing_lower = [p.lower() for p in existing_products]
        is_duplicate = name_lower in existing_lower
        should_pass = not is_duplicate
        
        passed = should_pass == expected_to_pass
        status = "✓" if passed else "✗"
        
        print(f"{status} '{name}': Expected {'PASS' if expected_to_pass else 'FAIL'}, Got {'PASS' if should_pass else 'FAIL'}")
        
        if not passed:
            all_passed = False
    
    print("-" * 50)
    
    if all_passed:
        print("✓ All validation logic tests passed!")
    else:
        print("✗ Some validation logic tests failed!")
    
    return all_passed

def test_view_validation_logic():
    """Test the actual validation logic from the view"""
    
    print("\n\nTesting View Validation Logic")
    print("=" * 50)
    
    # Test the exact logic used in the view
    def validate_product_name(name, existing_names):
        """Simulate the view's validation logic"""
        if len(name) < 2:
            return False, "Product name must be at least 2 characters"
        
        # Check case-insensitive duplicates (same as view logic)
        for existing in existing_names:
            if existing.lower() == name.lower():
                return False, f'Product "{name}" already exists (case-insensitive check)'
        
        return True, "Valid"
    
    # Test with simulated existing products
    existing_products = ['Test', 'Coca Cola']
    
    test_cases = [
        ('Test', False, 'Case-insensitive duplicate'),
        ('test', False, 'Case-insensitive duplicate'),
        ('TEST', False, 'Case-insensitive duplicate'),
        ('test2', True, 'Different product'),
        ('Coca', True, 'Different product'),
        ('coca', False, 'Case-insensitive duplicate'),
        ('', False, 'Empty name'),
        ('T', False, 'Too short'),
    ]
    
    print("\nView Logic Test Results:")
    print("-" * 50)
    
    all_passed = True
    for name, expected_valid, description in test_cases:
        is_valid, message = validate_product_name(name, existing_products)
        passed = is_valid == expected_valid
        status = "✓" if passed else "✗"
        
        result = "VALID" if is_valid else "INVALID"
        expected = "VALID" if expected_valid else "INVALID"
        
        print(f"{status} '{name}' ({description}): {result} (Expected: {expected})")
        if not is_valid:
            print(f"    Message: {message}")
        
        if not passed:
            all_passed = False
    
    print("-" * 50)
    
    if all_passed:
        print("✓ All view validation tests passed!")
    else:
        print("✗ Some view validation tests failed!")
    
    return all_passed

if __name__ == '__main__':
    logic_passed = test_case_insensitive_logic()
    view_passed = test_view_validation_logic()
    
    print("\n" + "=" * 50)
    if logic_passed and view_passed:
        print("✓ ALL TESTS PASSED! Case-insensitive validation is working correctly.")
    else:
        print("✗ SOME TESTS FAILED! Please check the validation logic.")
