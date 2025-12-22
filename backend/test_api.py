import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_response(response, title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")

def test_health():
    '''Test health endpoint'''
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "Health Check")
    return response.status_code == 200

def test_create_company():
    '''Test company creation'''
    data = {
        "name": f"Test Company {datetime.now().strftime('%H%M%S')}",
        "description": "Automated test company"
    }
    response = requests.post(f"{BASE_URL}/api/companies/", json=data)
    print_response(response, "Create Company")
    if response.status_code == 200:
        return response.json()['id']
    return None

def test_get_companies():
    '''Test get all companies'''
    response = requests.get(f"{BASE_URL}/api/companies/")
    print_response(response, "Get All Companies")
    return response.status_code == 200

def test_get_company(company_id):
    '''Test get single company'''
    response = requests.get(f"{BASE_URL}/api/companies/{company_id}")
    print_response(response, f"Get Company {company_id}")
    return response.status_code == 200

def test_update_company(company_id):
    '''Test company update'''
    data = {
        "name": f"Updated Company {datetime.now().strftime('%H%M%S')}",
        "description": "Updated description"
    }
    response = requests.put(f"{BASE_URL}/api/companies/{company_id}", json=data)
    print_response(response, f"Update Company {company_id}")
    return response.status_code == 200

def test_create_product(company_id):
    '''Test product creation'''
    data = {
        "company_id": company_id,
        "name": f"Test Product {datetime.now().strftime('%H%M%S')}",
        "sku": f"SKU{datetime.now().strftime('%H%M%S')}",
        "category": "Test Category",
        "brand": "Test Brand",
        "reference_colors": {
            "primary": "#FF0000",
            "secondary": "#00FF00"
        }
    }
    response = requests.post(f"{BASE_URL}/api/products/", json=data)
    print_response(response, "Create Product")
    if response.status_code == 200:
        return response.json()['id']
    return None

def test_get_products(company_id):
    '''Test get company products'''
    response = requests.get(f"{BASE_URL}/api/products/company/{company_id}")
    print_response(response, f"Get Products for Company {company_id}")
    return response.status_code == 200

def test_create_dataset(company_id):
    '''Test dataset creation'''
    data = {
        "company_id": company_id,
        "name": f"Test Dataset {datetime.now().strftime('%H%M%S')}",
        "description": "Automated test dataset"
    }
    response = requests.post(f"{BASE_URL}/api/datasets/", json=data)
    print_response(response, "Create Dataset")
    if response.status_code == 200:
        return response.json()['id']
    return None

def test_get_datasets(company_id):
    '''Test get company datasets'''
    response = requests.get(f"{BASE_URL}/api/datasets/company/{company_id}")
    print_response(response, f"Get Datasets for Company {company_id}")
    return response.status_code == 200

def run_all_tests():
    '''Run all API tests'''
    print("\n" + "="*60)
    print("RETAIL SHELF AI - API TEST SUITE")
    print("="*60 + "\n")
    
    results = []
    
    # Test 1: Health Check
    print("TEST 1: Health Check")
    results.append(("Health Check", test_health()))
    
    # Test 2: Create Company
    print("\nTEST 2: Create Company")
    company_id = test_create_company()
    results.append(("Create Company", company_id is not None))
    
    if not company_id:
        print("\n❌ Failed to create company. Stopping tests.")
        return
    
    # Test 3: Get All Companies
    print("\nTEST 3: Get All Companies")
    results.append(("Get Companies", test_get_companies()))
    
    # Test 4: Get Single Company
    print("\nTEST 4: Get Single Company")
    results.append(("Get Company", test_get_company(company_id)))
    
    # Test 5: Update Company
    print("\nTEST 5: Update Company")
    results.append(("Update Company", test_update_company(company_id)))
    
    # Test 6: Create Product
    print("\nTEST 6: Create Product")
    product_id = test_create_product(company_id)
    results.append(("Create Product", product_id is not None))
    
    # Test 7: Get Products
    print("\nTEST 7: Get Company Products")
    results.append(("Get Products", test_get_products(company_id)))
    
    # Test 8: Create Dataset
    print("\nTEST 8: Create Dataset")
    dataset_id = test_create_dataset(company_id)
    results.append(("Create Dataset", dataset_id is not None))
    
    # Test 9: Get Datasets
    print("\nTEST 9: Get Company Datasets")
    results.append(("Get Datasets", test_get_datasets(company_id)))
    
    # Print Results Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed. Check the output above.")

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server.")
        print("Please make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")
