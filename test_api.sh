#!/bin/bash

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Retail Shelf AI - API Tests (curl)"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Test 1: Health Check
echo -e "\nTEST 1: Health Check"
curl -s -X GET "\/health" | jq .

# Test 2: Create Company
echo -e "\nTEST 2: Create Company"
COMPANY_RESPONSE=\
echo \ | jq .
COMPANY_ID=\

# Test 3: Get All Companies
echo -e "\nTEST 3: Get All Companies"
curl -s -X GET "\/api/companies/" | jq .

# Test 4: Create Product
echo -e "\nTEST 4: Create Product"
curl -s -X POST "\/api/products/" \
  -H "Content-Type: application/json" \
  -d "{
    \"company_id\": \,
    \"name\": \"Test Product\",
    \"sku\": \"SKU123\",
    \"category\": \"Test Category\"
  }" | jq .

echo -e "\n=========================================="
echo -e "Tests completed!"
echo -e "==========================================\n"
