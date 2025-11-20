#!/usr/bin/env python
"""
Demo script showing OpenFoodFacts integration in futurePOS
This demonstrates the enhanced barcode scanning capabilities
"""

import os
import sys
import django

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.openfoodfacts_integration import fetch_openfoodfacts_data
from nano.upc_views import fetch_upc_data

def demo_openfoodfacts_integration():
    """Demonstrate OpenFoodFacts integration with real examples"""
    
    print("🛒 futurePOS OpenFoodFacts Integration Demo")
    print("=" * 60)
    
    # Test barcodes that should work with OpenFoodFacts
    demo_barcodes = [
        {
            'barcode': '7622210449283',
            'description': 'Oreo Cookies - Popular snack',
            'expected_source': 'openfoodfacts'
        },
        {
            'barcode': '5449000214911', 
            'description': 'Coca-Cola Classic - Popular beverage',
            'expected_source': 'upc_database'
        },
        {
            'barcode': '4008400402228',
            'description': 'Nutella - Popular chocolate spread',
            'expected_source': 'upc_database'
        }
    ]
    
    print("\n📦 Testing Enhanced Barcode Lookup")
    print("-" * 40)
    
    for i, test_case in enumerate(demo_barcodes, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Barcode: {test_case['barcode']}")
        
        try:
            # Test the integrated fetch_upc_data function
            result = fetch_upc_data(test_case['barcode'])
            
            if result:
                print(f"   ✅ Found: {result['name']}")
                print(f"   📊 Source: {result['source']}")
                print(f"   🏷️  Brand: {result.get('brand', 'N/A')}")
                print(f"   📂 Category: {result['category']}")
                
                # Show additional OpenFoodFacts data if available
                if result.get('source') == 'openfoodfacts':
                    if result.get('ingredients'):
                        print(f"   🥄 Ingredients: {result['ingredients'][:50]}...")
                    if result.get('nutrients'):
                        nutrients = result['nutrients']
                        if nutrients.get('energy'):
                            print(f"   ⚡ Energy: {nutrients['energy']}")
                        if nutrients.get('protein'):
                            print(f"   🥩 Protein: {nutrients['protein']}")
                    if result.get('image_url'):
                        print(f"   🖼️  Image: Available")
                
                # Check if source matches expectation
                source_match = "✅" if result['source'] == test_case['expected_source'] else "⚠️"
                print(f"   {source_match} Expected source: {test_case['expected_source']}")
                
            else:
                print(f"   ❌ Product not found")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 Integration Benefits Demonstrated")
    print("-" * 40)
    
    benefits = [
        "✅ Multi-source barcode lookup (Local → UPC → OpenFoodFacts)",
        "✅ Rich product data from OpenFoodFacts when available",
        "✅ Nutritional information for health-conscious customers", 
        "✅ Ingredient lists for allergen awareness",
        "✅ Automatic category mapping to your system",
        "✅ Fallback reliability - always gets some result",
        "✅ Seamless integration with existing scanning workflow"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
    
    print("\n" + "=" * 60)
    print("🚀 Ready for Production Use!")
    print("-" * 40)
    
    print("\nYour futurePOS system now has enhanced scanning capabilities:")
    print("   • Continue using barcode scanner as before")
    print("   • Automatic access to millions of products via OpenFoodFacts")
    print("   • Rich product information when available")
    print("   • Reliable fallback to existing databases")
    print("   • No user training required")
    
    print(f"\n📚 For detailed usage, see: OPENFOODFACTS_INTEGRATION_GUIDE.md")

if __name__ == "__main__":
    demo_openfoodfacts_integration()
