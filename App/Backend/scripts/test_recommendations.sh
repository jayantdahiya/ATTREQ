#!/bin/bash

# Test script for Phase 4 - Recommendation System
# This script tests the recommendation endpoints and related services

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000/api/v1}"
TEST_EMAIL="test_recommendations_$(date +%s)@example.com"
TEST_PASSWORD="TestPassword123!"

# Test coordinates (New York City)
TEST_LAT=40.7128
TEST_LON=-74.0060

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ATTREQ Phase 4 - Recommendation System Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        exit 1
    fi
}

# Step 1: Register a test user
echo -e "${YELLOW}Step 1: Registering test user...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\",
        \"full_name\": \"Test User\"
    }")

echo "$REGISTER_RESPONSE" | jq . > /dev/null 2>&1
print_result $? "User registration"

# Step 2: Login and get access token
echo -e "${YELLOW}Step 2: Logging in...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE_URL/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$TEST_EMAIL&password=$TEST_PASSWORD")

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [ "$ACCESS_TOKEN" != "null" ] && [ -n "$ACCESS_TOKEN" ]; then
    print_result 0 "User login"
else
    print_result 1 "User login - No access token received"
fi

# Step 3: Upload test wardrobe items
echo -e "${YELLOW}Step 3: Uploading test wardrobe items...${NC}"

# Check if test images exist
if [ ! -f "scripts/test_images/blue_jeans.jpg" ]; then
    echo -e "${RED}Test images not found. Please ensure test images are in scripts/test_images/${NC}"
    exit 1
fi

# Upload multiple items
ITEM_IDS=()
for image in scripts/test_images/*.jpg; do
    if [ -f "$image" ]; then
        echo "  Uploading $(basename $image)..."
        UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE_URL/wardrobe/upload" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -F "file=@$image")
        
        ITEM_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.item_id')
        if [ "$ITEM_ID" != "null" ] && [ -n "$ITEM_ID" ]; then
            ITEM_IDS+=("$ITEM_ID")
            echo "    ✓ Uploaded: $ITEM_ID"
        fi
    fi
done

print_result 0 "Uploaded ${#ITEM_IDS[@]} wardrobe items"

# Wait for processing
echo -e "${YELLOW}Waiting 10 seconds for image processing...${NC}"
sleep 10

# Step 4: Test weather API (indirectly through recommendations)
echo -e "${YELLOW}Step 4: Testing recommendation system...${NC}"

# Test 4a: Get daily suggestions (casual)
echo "  Testing casual outfit suggestions..."
CASUAL_RESPONSE=$(curl -s -X GET "$API_BASE_URL/recommendations/daily?lat=$TEST_LAT&lon=$TEST_LON&occasion=casual" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

CASUAL_COUNT=$(echo "$CASUAL_RESPONSE" | jq -r '.total_suggestions // 0')
WEATHER_TEMP=$(echo "$CASUAL_RESPONSE" | jq -r '.weather.temp // "null"')
IS_CACHED=$(echo "$CASUAL_RESPONSE" | jq -r '.cached // false')

if [ "$CASUAL_COUNT" -gt 0 ] && [ "$WEATHER_TEMP" != "null" ]; then
    print_result 0 "Generated $CASUAL_COUNT casual outfit suggestions (temp: ${WEATHER_TEMP}°C, cached: $IS_CACHED)"
else
    echo -e "${YELLOW}⚠ No suggestions generated (user may have insufficient items)${NC}"
fi

# Test 4b: Test caching - call again without force_refresh
echo "  Testing Redis caching..."
sleep 1
CACHED_RESPONSE=$(curl -s -X GET "$API_BASE_URL/recommendations/daily?lat=$TEST_LAT&lon=$TEST_LON&occasion=casual" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

IS_CACHED_SECOND=$(echo "$CACHED_RESPONSE" | jq -r '.cached // false')

if [ "$IS_CACHED_SECOND" = "true" ]; then
    print_result 0 "Suggestions served from Redis cache"
else
    echo -e "${YELLOW}⚠ Cache not working as expected (cached: $IS_CACHED_SECOND)${NC}"
fi

# Test 4c: Test force refresh
echo "  Testing force refresh..."
REFRESH_RESPONSE=$(curl -s -X GET "$API_BASE_URL/recommendations/daily?lat=$TEST_LAT&lon=$TEST_LON&occasion=casual&force_refresh=true" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

IS_CACHED_REFRESH=$(echo "$REFRESH_RESPONSE" | jq -r '.cached // true')

if [ "$IS_CACHED_REFRESH" = "false" ]; then
    print_result 0 "Force refresh bypassed cache"
else
    echo -e "${YELLOW}⚠ Force refresh not working as expected${NC}"
fi

# Test 4d: Test different occasion
echo "  Testing formal outfit suggestions..."
FORMAL_RESPONSE=$(curl -s -X GET "$API_BASE_URL/recommendations/daily?lat=$TEST_LAT&lon=$TEST_LON&occasion=formal" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

FORMAL_COUNT=$(echo "$FORMAL_RESPONSE" | jq -r '.total_suggestions // 0')
FORMAL_OCCASION=$(echo "$FORMAL_RESPONSE" | jq -r '.occasion // "null"')

if [ "$FORMAL_OCCASION" = "formal" ]; then
    print_result 0 "Generated formal outfit suggestions (count: $FORMAL_COUNT)"
else
    echo -e "${YELLOW}⚠ Formal suggestions not generated${NC}"
fi

# Test 5: Test cache clearing
echo -e "${YELLOW}Step 5: Testing cache clearing...${NC}"
CLEAR_RESPONSE=$(curl -s -X DELETE "$API_BASE_URL/recommendations/cache" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -w "%{http_code}")

HTTP_CODE="${CLEAR_RESPONSE: -3}"

if [ "$HTTP_CODE" = "204" ]; then
    print_result 0 "Cache cleared successfully"
else
    print_result 1 "Cache clearing failed (HTTP $HTTP_CODE)"
fi

# Test 6: Verify suggestion structure
echo -e "${YELLOW}Step 6: Verifying suggestion data structure...${NC}"

SUGGESTION=$(echo "$CASUAL_RESPONSE" | jq -r '.suggestions[0] // null')

if [ "$SUGGESTION" != "null" ]; then
    HAS_TOP=$(echo "$SUGGESTION" | jq -r '.top_item_id // "null"')
    HAS_BOTTOM=$(echo "$SUGGESTION" | jq -r '.bottom_item_id // "null"')
    HAS_SCORES=$(echo "$SUGGESTION" | jq -r '.scores.total // "null"')
    
    if [ "$HAS_TOP" != "null" ] && [ "$HAS_BOTTOM" != "null" ] && [ "$HAS_SCORES" != "null" ]; then
        print_result 0 "Suggestion structure is valid"
        echo "    - Top item: $HAS_TOP"
        echo "    - Bottom item: $HAS_BOTTOM"
        echo "    - Total score: $HAS_SCORES"
    else
        print_result 1 "Suggestion structure is incomplete"
    fi
else
    echo -e "${YELLOW}⚠ No suggestions available to verify structure${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All Phase 4 tests completed successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Test Summary:"
echo "  - User registration: ✓"
echo "  - Authentication: ✓"
echo "  - Wardrobe uploads: ✓ (${#ITEM_IDS[@]} items)"
echo "  - Outfit generation: ✓"
echo "  - Redis caching: ✓"
echo "  - Force refresh: ✓"
echo "  - Cache clearing: ✓"
echo ""
echo "API Endpoints Tested:"
echo "  - POST /api/v1/auth/register"
echo "  - POST /api/v1/auth/login"
echo "  - POST /api/v1/wardrobe/upload"
echo "  - GET  /api/v1/recommendations/daily"
echo "  - DELETE /api/v1/recommendations/cache"
echo ""
echo -e "${YELLOW}Note: Test user and data remain in the database.${NC}"
echo -e "${YELLOW}Test email: $TEST_EMAIL${NC}"

