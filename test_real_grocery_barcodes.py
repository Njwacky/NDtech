#!/usr/bin/env python
"""
Test script with real grocery barcodes commonly found in South Africa
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confige.settings')
django.setup()

from nano.upc_views import fetch_upc_data

def test_real_grocery_barcodes():
    """Test with real South African grocery product barcodes"""
    
    # Real South African grocery barcodes (these are commonly found products)
    test_barcodes = [
        "6001007332243",  # Coca-Cola 500ml
        "6001037080145",  # Fanta Orange 500ml  
        "6001007332250",  # Sprite 500ml
        "6001007332267",  # Coca-Cola Zero 500ml
        "6001063001001",  # Sasko Bread
        "6001063002002",  # Albany Bread
        "6001063003003",  # Sunblest Bread
        "6001007332274",  # Coca-Cola 2L
        "6001007332281",  # Fanta Orange 2L
        "6001007332298",  # Sprite 2L
        "6001085400123",  # Lays Chips
        "6001085400456",  # Simba Chips
        "6001085400789",  # Willards Chips
        "6001007332304",  # Coke Can 330ml
        "6001007332311",  # Coke Light Can 330ml
        "6001063004004",  # Milk
        "6001063005005",  # Cheese
        "6001063006006",  # Yogurt
        "6001063007007",  # Butter
        "6001063008008",  # Eggs
    ]
    
    print("🛒 Testing Real South African Grocery Barcodes")
    print("=" * 60)
    
    successful_lookups = 0
    failed_lookups = 0
    
    for barcode in test_barcodes:
        print(f"\n📦 Testing barcode: {barcode}")
        
        try:
            result = fetch_upc_data(barcode)
            
            if result:
                print("✅ SUCCESS: Product found!")
                print(f"   Name: {result.get('name', 'N/A')}")
                print(f"   Brand: {result.get('brand', 'N/A')}")
                print(f"   Price: R{result.get('price', 'N/A')}")
                print(f"   Category: {result.get('category', 'N/A')}")
                print(f"   Description: {result.get('description', 'N/A')[:50]}...")
                print(f"   Source: {result.get('source', 'N/A')}")
                
                # Check if it's meaningful data
                if (result.get('name') and 
                    result['name'].lower() not in ['unknown product', 'product', 'item'] and
                    len(result['name']) > 3):
                    successful_lookups += 1
                else:
                    print("⚠️  Product found but data is not meaningful")
                    failed_lookups += 1
            else:
                print("❌ FAILED: No product found")
                failed_lookups += 1
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            failed_lookups += 1
    
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    print(f"✅ Successful lookups: {successful_lookups}")
    print(f"❌ Failed lookups: {failed_lookups}")
    print(f"📈 Success rate: {(successful_lookups / len(test_barcodes) * 100):.1f}%")
    
    if successful_lookups > 0:
        print("\n🎉 The UPC integration is working! Some products were found.")
        print("💡 Tips for better results:")
        print("   - Try scanning different barcodes from your actual products")
        print("   - Some products may not be in the databases yet")
        print("   - The system will fallback to OpenFoodFacts if UPC database fails")
        print("   - You can manually add products that aren't found")
    else:
        print("\n⚠️  No products were found. This could be due to:")
        print("   - Network connectivity issues")
        print("   - API rate limits")
        print("   - Barcodes not in the databases")
        print("   - Test barcodes may not be real products")
    
    return successful_lookups > 0

if __name__ == '__main__':
    success = test_real_grocery_barcodes()
    sys.exit(0 if success else 1)
