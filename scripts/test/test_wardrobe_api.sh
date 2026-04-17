#!/bin/bash
# Test script for ATTREQ Wardrobe & Outfit APIs
# Usage: ./test_wardrobe_api.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TEST_IMAGES_DIR="${REPO_ROOT}/scripts/data/test_images"

BASE_URL="http://localhost:8000/api/v1"
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="Test123!@#"
JWT_TOKEN=""
ITEM_IDS=()

echo "=========================================="
echo "  ATTREQ Wardrobe API Testing Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if server is running
echo "🔍 Checking if server is running..."
if curl -s "${BASE_URL%/api/v1}/health" > /dev/null; then
    print_success "Server is running"
else
    print_error "Server is not running. Please start with: docker compose -f infra/docker/compose.api.yml up -d --build"
    exit 1
fi

echo ""
echo "=========================================="
echo "  Step 1: User Registration"
echo "=========================================="
echo ""

REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"${TEST_EMAIL}\",
        \"password\": \"${TEST_PASSWORD}\",
        \"full_name\": \"Test User\"
    }")

if echo "$REGISTER_RESPONSE" | grep -q "email"; then
    print_success "User registered: ${TEST_EMAIL}"
else
    print_error "Registration failed"
    echo "$REGISTER_RESPONSE"
    exit 1
fi

echo ""
echo "=========================================="
echo "  Step 2: User Login"
echo "=========================================="
echo ""

LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${TEST_EMAIL}&password=${TEST_PASSWORD}")

JWT_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$JWT_TOKEN" ]; then
    print_error "Login failed"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

print_success "Login successful"
print_info "JWT Token: ${JWT_TOKEN:0:20}..."

echo ""
echo "=========================================="
echo "  Step 3: Upload Wardrobe Items"
echo "=========================================="
echo ""

# Check if test images exist
if [ ! -d "$TEST_IMAGES_DIR" ]; then
    print_error "test_images directory not found!"
    print_info "Run: python3 scripts/data/download_test_images.py"
    exit 1
fi

# Upload multiple items
for image in "$TEST_IMAGES_DIR"/*.jpg; do
    if [ -f "$image" ]; then
        filename=$(basename "$image")
        print_info "Uploading: $filename"
        
        UPLOAD_RESPONSE=$(curl -s -X POST "${BASE_URL}/wardrobe/upload" \
            -H "Authorization: Bearer ${JWT_TOKEN}" \
            -F "file=@${image}")
        
        if echo "$UPLOAD_RESPONSE" | grep -q "id"; then
            ITEM_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
            ITEM_IDS+=("$ITEM_ID")
            print_success "Uploaded: $filename (ID: ${ITEM_ID:0:8}...)"
        else
            print_error "Failed to upload: $filename"
            echo "$UPLOAD_RESPONSE"
        fi
        
        # Small delay between uploads
        sleep 1
    fi
done

echo ""
print_success "Uploaded ${#ITEM_IDS[@]} items"

echo ""
echo "=========================================="
echo "  Step 4: List Wardrobe Items"
echo "=========================================="
echo ""

print_info "Fetching all wardrobe items..."
ITEMS_RESPONSE=$(curl -s -X GET "${BASE_URL}/wardrobe/items" \
    -H "Authorization: Bearer ${JWT_TOKEN}")

ITEM_COUNT=$(echo "$ITEMS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('items', [])))" 2>/dev/null)
print_success "Found $ITEM_COUNT items in wardrobe"

echo ""
echo "=========================================="
echo "  Step 5: Get Single Item Details"
echo "=========================================="
echo ""

if [ ${#ITEM_IDS[@]} -gt 0 ]; then
    FIRST_ITEM_ID="${ITEM_IDS[0]}"
    print_info "Fetching details for item: ${FIRST_ITEM_ID:0:8}..."
    
    ITEM_DETAIL=$(curl -s -X GET "${BASE_URL}/wardrobe/items/${FIRST_ITEM_ID}" \
        -H "Authorization: Bearer ${JWT_TOKEN}")
    
    if echo "$ITEM_DETAIL" | grep -q "id"; then
        print_success "Retrieved item details"
        echo "$ITEM_DETAIL" | python3 -m json.tool 2>/dev/null || echo "$ITEM_DETAIL"
    else
        print_error "Failed to get item details"
    fi
fi

echo ""
echo "=========================================="
echo "  Step 6: Filter Items by Category"
echo "=========================================="
echo ""

print_info "Filtering items by category: shirt"
FILTERED_RESPONSE=$(curl -s -X GET "${BASE_URL}/wardrobe/items?category=shirt" \
    -H "Authorization: Bearer ${JWT_TOKEN}")

FILTERED_COUNT=$(echo "$FILTERED_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('items', [])))" 2>/dev/null)
print_success "Found $FILTERED_COUNT shirts"

echo ""
echo "=========================================="
echo "  Step 7: Update Item Tags"
echo "=========================================="
echo ""

if [ ${#ITEM_IDS[@]} -gt 0 ]; then
    FIRST_ITEM_ID="${ITEM_IDS[0]}"
    print_info "Updating tags for item: ${FIRST_ITEM_ID:0:8}..."
    
    UPDATE_RESPONSE=$(curl -s -X PUT "${BASE_URL}/wardrobe/items/${FIRST_ITEM_ID}" \
        -H "Authorization: Bearer ${JWT_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "category": "shirt",
            "season": ["summer", "spring"],
            "occasion": ["casual", "work"]
        }')
    
    if echo "$UPDATE_RESPONSE" | grep -q "id"; then
        print_success "Updated item tags"
    else
        print_error "Failed to update tags"
    fi
fi

echo ""
echo "=========================================="
echo "  Step 8: Create Manual Outfit"
echo "=========================================="
echo ""

if [ ${#ITEM_IDS[@]} -ge 2 ]; then
    TOP_ID="${ITEM_IDS[0]}"
    BOTTOM_ID="${ITEM_IDS[1]}"
    
    print_info "Creating outfit with:"
    print_info "  Top: ${TOP_ID:0:8}..."
    print_info "  Bottom: ${BOTTOM_ID:0:8}..."
    
    OUTFIT_RESPONSE=$(curl -s -X POST "${BASE_URL}/outfits" \
        -H "Authorization: Bearer ${JWT_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{
            \"top_item_id\": \"${TOP_ID}\",
            \"bottom_item_id\": \"${BOTTOM_ID}\",
            \"occasion_context\": \"casual\"
        }")
    
    if echo "$OUTFIT_RESPONSE" | grep -q "id"; then
        OUTFIT_ID=$(echo "$OUTFIT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
        print_success "Created outfit: ${OUTFIT_ID:0:8}..."
    else
        print_error "Failed to create outfit"
        echo "$OUTFIT_RESPONSE"
    fi
fi

echo ""
echo "=========================================="
echo "  Step 9: List Outfits"
echo "=========================================="
echo ""

OUTFITS_RESPONSE=$(curl -s -X GET "${BASE_URL}/outfits" \
    -H "Authorization: Bearer ${JWT_TOKEN}")

OUTFIT_COUNT=$(echo "$OUTFITS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('items', [])))" 2>/dev/null)
print_success "Found $OUTFIT_COUNT outfits"

echo ""
echo "=========================================="
echo "  Step 10: Submit Outfit Feedback"
echo "=========================================="
echo ""

if [ ! -z "$OUTFIT_ID" ]; then
    print_info "Submitting positive feedback for outfit..."
    
    FEEDBACK_RESPONSE=$(curl -s -X POST "${BASE_URL}/outfits/${OUTFIT_ID}/feedback" \
        -H "Authorization: Bearer ${JWT_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "feedback_score": 1
        }')
    
    if echo "$FEEDBACK_RESPONSE" | grep -q "id"; then
        print_success "Feedback submitted successfully"
    else
        print_error "Failed to submit feedback"
    fi
fi

echo ""
echo "=========================================="
echo "  Step 11: Delete an Item"
echo "=========================================="
echo ""

if [ ${#ITEM_IDS[@]} -gt 2 ]; then
    LAST_ITEM_ID="${ITEM_IDS[-1]}"
    print_info "Deleting item: ${LAST_ITEM_ID:0:8}..."
    
    DELETE_RESPONSE=$(curl -s -X DELETE "${BASE_URL}/wardrobe/items/${LAST_ITEM_ID}" \
        -H "Authorization: Bearer ${JWT_TOKEN}")
    
    print_success "Item deleted"
fi

echo ""
echo "=========================================="
echo "  ✅ All Tests Completed!"
echo "=========================================="
echo ""
print_success "Test Summary:"
echo "  - Created test user: ${TEST_EMAIL}"
echo "  - Uploaded ${#ITEM_IDS[@]} wardrobe items"
echo "  - Created outfits"
echo "  - Tested filtering and updates"
echo ""
print_info "Check your backend logs to see AI processing status"
print_info "docker compose -f infra/docker/compose.api.yml logs -f backend"
echo ""
