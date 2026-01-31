#!/bin/bash

# Configuration
GATEWAY_HOST="localhost"
GATEWAY_PORT="2525"
DEMO_EMAIL_PATH="../demo-data/email_demo.txt"

# Colors for output
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

echo -e "${BLUE}=== PQC Email Gateway Test ===${NC}"
echo -e "${YELLOW}Connecting to $GATEWAY_HOST:$GATEWAY_PORT...${NC}"

# Check if demo email exists
if [ ! -f "$DEMO_EMAIL_PATH" ]; then
    echo -e "${RED}Error: Demo email file not found at $DEMO_EMAIL_PATH${NC}"
    echo "Please ensure the demo-data directory contains email_demo.txt"
    exit 1
fi

# Extract sender and recipient from demo email
FROM_EMAIL=$(grep -E "^From:" "$DEMO_EMAIL_PATH" | sed 's/From: *//')
TO_EMAIL=$(grep -E "^To:" "$DEMO_EMAIL_PATH" | sed 's/To: *//')

# Use the demo email file directly
EMAIL_FILE="$DEMO_EMAIL_PATH"

# Use openssl s_client to connect with TLS and send the email
echo -e "${YELLOW}Sending email with TLS...${NC}"
(
sleep 1
echo "EHLO localhost"
sleep 1
echo "MAIL FROM: <$FROM_EMAIL>"
sleep 1
echo "RCPT TO: <$TO_EMAIL>"
sleep 1
echo "DATA"
sleep 1
cat "$EMAIL_FILE"
echo "."
sleep 1
echo "QUIT"
) | openssl s_client -connect "$GATEWAY_HOST:$GATEWAY_PORT" -starttls smtp -quiet 2>&1 | tee /tmp/pqc_mail_output.log

# Extract TLS parameters from the output
echo -e "\n${BLUE}=== TLS Parameters ===${NC}"
grep -E "Protocol|Cipher|Server Temp Key|Verification" /tmp/pqc_mail_output.log

# Extract the receipt ID from the X-PQC-Signature header
RECEIPT_ID=$(grep -o "X-PQC-Signature: DILITHIUM-SIGNATURE-[a-f0-9]*" /tmp/pqc_mail_output.log | cut -d'-' -f4)

# Extract TLS cipher information
TLS_INFO=$(grep -E "Cipher" /tmp/pqc_mail_output.log | head -1 | sed 's/.*: //')

if [ -n "$RECEIPT_ID" ]; then
    echo -e "\n${GREEN}=== Email sent successfully! ===${NC}"
    echo -e "Sent email $FROM_EMAIL with PQC TLS [$TLS_INFO]. Receipt ID: $RECEIPT_ID"
    echo -e "\n${YELLOW}View receipt at: ${NC}http://localhost:6000/receipts/$RECEIPT_ID"
else
    echo -e "\n${RED}=== Failed to extract receipt ID ===${NC}"
    echo "Check /tmp/pqc_mail_output.log for details"
fi

# No cleanup needed as we're using the demo file directly

echo -e "\n${BLUE}=== Test Complete ===${NC}"