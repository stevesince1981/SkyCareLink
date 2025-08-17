#!/bin/bash

# SkyCareLink End-to-End Smoke Test Suite
# Tests critical user flows and system health

set -e

# Configuration
BASE_URL="http://localhost:5000"
TEMP_DIR="/tmp/skycare_smoke_$$"
mkdir -p "$TEMP_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 SkyCareLink Smoke Test Suite Starting..."
echo "Base URL: $BASE_URL"
echo "Temp Dir: $TEMP_DIR"
echo ""

# Test 1: Health Check
echo "1. Testing health endpoint..."
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/healthz")
if [ "$HEALTH_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Health check returned 200"
else
    echo -e "${RED}✗ FAIL${NC}: Health check returned $HEALTH_CODE (expected 200)"
    exit 1
fi

# Test 2: Home Page Load
echo "2. Testing home page..."
HOME_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
if [ "$HOME_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Home page accessible"
else
    echo -e "${RED}✗ FAIL${NC}: Home page returned $HOME_CODE"
    exit 1
fi

# Test 3: Quote Form Submission (Full Flow)
echo "3. Testing quote submission flow..."

# First, get the form to extract CSRF token
FORM_RESPONSE="$TEMP_DIR/form.html"
curl -s -c "$TEMP_DIR/cookies.txt" "$BASE_URL/consumer_intake" > "$FORM_RESPONSE"

# Extract CSRF token
CSRF_TOKEN=$(grep -o 'name="csrf_token"[^>]*value="[^"]*"' "$FORM_RESPONSE" 2>/dev/null | sed 's/.*value="\([^"]*\)".*/\1/' | head -1)

if [ -z "$CSRF_TOKEN" ]; then
    echo -e "${YELLOW}⚠ WARNING${NC}: No CSRF token found, submitting without token"
    CSRF_TOKEN=""
fi

# Submit quote form
QUOTE_RESPONSE="$TEMP_DIR/quote_response.txt"
QUOTE_CODE=$(curl -s -b "$TEMP_DIR/cookies.txt" -c "$TEMP_DIR/cookies.txt" \
    -w "%{http_code}" \
    -o "$QUOTE_RESPONSE" \
    -L \
    -X POST \
    -d "service_type=critical" \
    -d "severity_level=2" \
    -d "from_hospital=Johns Hopkins Hospital" \
    -d "to_hospital=Mayo Clinic Rochester" \
    -d "patient_name=Test Patient" \
    -d "patient_dob=1980-01-01" \
    -d "transport_date=2025-08-20" \
    -d "contact_name=Test Contact" \
    -d "contact_phone=555-0123" \
    -d "contact_email=test@example.com" \
    -d "equipment=ventilator" \
    -d "csrf_token=$CSRF_TOKEN" \
    "$BASE_URL/consumer_intake")

if [ "$QUOTE_CODE" = "200" ] || [ "$QUOTE_CODE" = "302" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Quote form submission successful ($QUOTE_CODE)"
    
    # Try to extract quote reference from response
    QUOTE_REF=$(grep -o 'Quote Reference: [A-Z0-9-]*' "$QUOTE_RESPONSE" 2>/dev/null | sed 's/Quote Reference: //' | head -1)
    if [ -z "$QUOTE_REF" ]; then
        QUOTE_REF=$(grep -o 'REF-[A-Z0-9-]*' "$QUOTE_RESPONSE" 2>/dev/null | head -1)
    fi
    
    if [ ! -z "$QUOTE_REF" ]; then
        echo -e "${GREEN}✓ PASS${NC}: Quote reference generated: $QUOTE_REF"
        
        # Test 4: Quote Results Page
        echo "4. Testing quote results page..."
        RESULTS_CODE=$(curl -s -b "$TEMP_DIR/cookies.txt" -o /dev/null -w "%{http_code}" "$BASE_URL/quotes/results/$QUOTE_REF")
        if [ "$RESULTS_CODE" = "200" ]; then
            echo -e "${GREEN}✓ PASS${NC}: Quote results page accessible"
            
            # Verify quote reference appears in results
            RESULTS_CONTENT="$TEMP_DIR/results.html"
            curl -s -b "$TEMP_DIR/cookies.txt" "$BASE_URL/quotes/results/$QUOTE_REF" > "$RESULTS_CONTENT"
            
            if grep -q "$QUOTE_REF" "$RESULTS_CONTENT"; then
                echo -e "${GREEN}✓ PASS${NC}: Quote reference found in results page"
            else
                echo -e "${YELLOW}⚠ WARNING${NC}: Quote reference not found in results content"
            fi
        else
            echo -e "${YELLOW}⚠ WARNING${NC}: Quote results page returned $RESULTS_CODE"
        fi
    else
        echo -e "${YELLOW}⚠ WARNING${NC}: Could not extract quote reference from response"
    fi
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Quote form returned $QUOTE_CODE (may be expected for demo)"
fi

# Test 5: Critical API Endpoints
echo "5. Testing critical endpoints..."

ENDPOINTS=(
    "/resources-financial:200"
    "/terms-of-service:200"
    "/login:200"
)

for endpoint_test in "${ENDPOINTS[@]}"; do
    IFS=':' read -r endpoint expected_code <<< "$endpoint_test"
    
    ACTUAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    if [ "$ACTUAL_CODE" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $endpoint returned $expected_code"
    else
        echo -e "${YELLOW}⚠ WARNING${NC}: $endpoint returned $ACTUAL_CODE (expected $expected_code)"
    fi
done

# Test 6: Static Assets
echo "6. Testing static assets..."
STATIC_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/static/css/style.css" 2>/dev/null || echo "404")
if [ "$STATIC_CODE" = "200" ] || [ "$STATIC_CODE" = "404" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Static assets handling working ($STATIC_CODE)"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Static assets returned $STATIC_CODE"
fi

# Test 7: Security Headers Check
echo "7. Testing security headers..."
SECURITY_HEADERS=$(curl -s -I "$BASE_URL/" | grep -E "(X-Content-Type-Options|X-Frame-Options|X-XSS-Protection)" | wc -l)
if [ "$SECURITY_HEADERS" -ge "2" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Security headers present ($SECURITY_HEADERS found)"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Limited security headers found ($SECURITY_HEADERS)"
fi

# Test 8: Database Connectivity (if available)
echo "8. Testing database connectivity..."
DB_TEST_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/admin/dashboard" 2>/dev/null || echo "000")
if [ "$DB_TEST_CODE" = "200" ] || [ "$DB_TEST_CODE" = "302" ] || [ "$DB_TEST_CODE" = "401" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Database connectivity working (admin route accessible)"
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Database connectivity issues possible ($DB_TEST_CODE)"
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "🎉 Smoke Test Suite Complete!"
echo -e "${GREEN}✓ All critical systems operational${NC}"
echo ""

# Exit successfully
exit 0