#!/bin/bash

# Configuration
SIGNER_URL="http://localhost:5000"
RECEIPTS_URL="http://localhost:6000"
DEMO_DATA_DIR="../demo-data"
OUTPUT_DIR="./signed"

# Colors for output
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Check if a PDF file was provided as an argument
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: ./sign_pdf.sh [land_record.pdf|psu_tender.pdf]${NC}"
    echo -e "${YELLOW}No PDF specified, defaulting to land_record.pdf${NC}"
    SAMPLE_PDF="$DEMO_DATA_DIR/land_record.pdf"
else
    # Check if the argument is one of our demo PDFs
    case "$1" in
        "land_record.pdf")
            SAMPLE_PDF="$DEMO_DATA_DIR/land_record.pdf"
            ;;
        "psu_tender.pdf")
            SAMPLE_PDF="$DEMO_DATA_DIR/psu_tender.pdf"
            ;;
        *)
            # If it's a full path, use it directly
            if [ -f "$1" ]; then
                SAMPLE_PDF="$1"
            else
                echo -e "${RED}Error: Unknown PDF '$1'${NC}"
                echo -e "${YELLOW}Please use 'land_record.pdf' or 'psu_tender.pdf'${NC}"
                exit 1
            fi
            ;;
    esac
fi

# Check if the PDF exists
if [ ! -f "$SAMPLE_PDF" ]; then
    echo -e "${RED}Error: PDF file '$SAMPLE_PDF' not found${NC}"
    echo -e "${YELLOW}Please ensure the demo-data directory contains the required PDF files${NC}"
    exit 1
fi

# Get the base name of the PDF file without extension
BASENAME=$(basename "$SAMPLE_PDF" .pdf)
OUTPUT_PDF="$OUTPUT_DIR/${BASENAME}-signed.pdf"

echo -e "${BLUE}=== PQC PDF Signer Test ===${NC}"
echo -e "${YELLOW}Signing PDF: $SAMPLE_PDF${NC}"

# Sign the PDF using the signer service
echo -e "${YELLOW}Sending to signer service...${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "file=@$SAMPLE_PDF" \
    -o "$OUTPUT_PDF" \
    "$SIGNER_URL/sign")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}PDF signed successfully!${NC}"
    echo -e "${YELLOW}Signed PDF saved to: ${NC}$OUTPUT_PDF"
    
    # Extract receipt ID from response headers
    RECEIPT_ID=$(curl -s -I -X POST \
        -H "Content-Type: multipart/form-data" \
        -F "file=@$SAMPLE_PDF" \
        "$SIGNER_URL/sign" | grep -i "X-Receipt-ID" | cut -d' ' -f2 | tr -d '\r')
    
    if [ -n "$RECEIPT_ID" ]; then
        echo -e "${YELLOW}Receipt ID: ${NC}$RECEIPT_ID"
        echo -e "${YELLOW}View receipt at: ${NC}$RECEIPTS_URL/receipts/$RECEIPT_ID"
    fi
    
    # Verify the signed PDF
    echo -e "\n${BLUE}=== Verifying Signed PDF ===${NC}"
    VERIFY_RESPONSE=$(curl -s -X POST \
        -H "Content-Type: multipart/form-data" \
        -F "file=@$OUTPUT_PDF" \
        "$SIGNER_URL/verify")
    
    # Extract verification result
    VERIFIED=$(echo "$VERIFY_RESPONSE" | grep -o '"verified":\s*\(true\|false\)' | cut -d':' -f2 | tr -d ' ,')
    ALGORITHM=$(echo "$VERIFY_RESPONSE" | grep -o '"algorithm":\s*"[^"]*"' | cut -d'"' -f4)
    
    if [ "$VERIFIED" = "true" ]; then
        echo -e "${GREEN}Signature verified successfully!${NC}"
        echo -e "${YELLOW}Algorithm: ${NC}$ALGORITHM"
        echo -e "\nSigned successfully with Dilithium. Verified: VALID. Receipt ID: $RECEIPT_ID"
        
        # Generate Section 65B Certificate
        echo -e "\n${BLUE}=== Generating Section 65B Certificate ===${NC}"
        CERT_FILE="$OUTPUT_DIR/${BASENAME}-certificate.pdf"
        curl -s -o "$CERT_FILE" "$RECEIPTS_URL/receipts/$RECEIPT_ID/certificate"
        
        echo -e "${GREEN}Certificate generated!${NC}"
        echo -e "${YELLOW}Certificate saved to: ${NC}$CERT_FILE"
    else
        echo -e "${RED}Signature verification failed!${NC}"
        echo "$VERIFY_RESPONSE"
    fi
else
    echo -e "${RED}Failed to sign PDF. HTTP Code: $HTTP_CODE${NC}"
    echo "Response: $RESPONSE"
fi

echo -e "\n${BLUE}=== Test Complete ===${NC}"