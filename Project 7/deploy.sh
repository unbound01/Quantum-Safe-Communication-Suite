#!/bin/bash

# Unified Quantum-Safe Communication Suite - Deployment Script
# This script automates the build and deployment process

# Colors for output
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# Function to display usage information
show_usage() {
    echo -e "${BLUE}Unified Quantum-Safe Communication Suite - Deployment Script${NC}"
    echo -e "Usage: ./deploy.sh [OPTION]"
    echo -e "Options:"
    echo -e "  ${GREEN}start${NC}       Build and start all services"
    echo -e "  ${GREEN}stop${NC}        Stop all services"
    echo -e "  ${GREEN}restart${NC}     Restart all services"
    echo -e "  ${GREEN}logs${NC}        View logs from all services"
    echo -e "  ${GREEN}status${NC}      Check status of all services"
    echo -e "  ${GREEN}clean${NC}       Remove all containers and volumes"
    echo -e "  ${GREEN}build${NC}       Rebuild all images"
    echo -e "  ${GREEN}demo${NC}        Start in demo mode (with predefined settings)"
    echo -e "  ${GREEN}help${NC}        Show this help message"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
        echo -e "Please install Docker and Docker Compose before running this script"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed or not in PATH${NC}"
        echo -e "Please install Docker Compose before running this script"
        exit 1
    fi
}

# Function to check if .env file exists, create if not
check_env_file() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Warning: .env file not found, creating default configuration...${NC}"
        cat > .env << EOF
# Unified Quantum-Safe Communication Suite - Environment Configuration

# Service Ports
GATEWAY_PORT=2525
SIGNER_PORT=5000
RECEIPTS_PORT=6000
DASHBOARD_PORT=8080

# Mail Configuration
MAIL_DOMAIN=localhost

# Logging
LOG_LEVEL=info  # Options: debug, info, warning, error

# Dashboard Configuration
DASHBOARD_REFRESH=5  # Refresh interval in seconds

# Volume Names (for persistence)
RECEIPTS_VOLUME=receipts-data
SIGNER_VOLUME=signer-output

# Demo Data Path (relative to docker-compose.yml)
DEMO_DATA_PATH=./demo-data
EOF
        echo -e "${GREEN}Created default .env file${NC}"
    fi
}

# Function to check if demo data exists
check_demo_data() {
    if [ ! -d "demo-data" ]; then
        echo -e "${RED}Error: demo-data directory not found${NC}"
        echo -e "Please ensure the demo-data directory exists with required files:"
        echo -e "  - email_demo.txt"
        echo -e "  - land_record.pdf"
        echo -e "  - psu_tender.pdf"
        exit 1
    fi
    
    # Check for required demo files
    required_files=("demo-data/email_demo.txt" "demo-data/land_record.pdf" "demo-data/psu_tender.pdf")
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}Error: Required demo file $file not found${NC}"
            exit 1
        fi
    done
}

# Function to create dashboard directory if it doesn't exist
ensure_dashboard_exists() {
    if [ ! -d "dashboard" ]; then
        echo -e "${YELLOW}Creating dashboard directory and files...${NC}"
        mkdir -p dashboard
        
        # Create dashboard files (will be implemented in the next steps)
        echo -e "${GREEN}Dashboard directory created${NC}"
    fi
}

# Main script execution
check_docker

# Process command line arguments
if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

case "$1" in
    start)
        check_env_file
        check_demo_data
        ensure_dashboard_exists
        echo -e "${BLUE}Starting all services...${NC}"
        docker-compose up -d
        echo -e "${GREEN}Services started successfully!${NC}"
        echo -e "\nAccess points:"
        echo -e "  - Gateway: http://localhost:$(grep GATEWAY_PORT .env | cut -d= -f2)"
        echo -e "  - Signer: http://localhost:$(grep SIGNER_PORT .env | cut -d= -f2)"
        echo -e "  - Receipts: http://localhost:$(grep RECEIPTS_PORT .env | cut -d= -f2)"
        echo -e "  - Dashboard: http://localhost:$(grep DASHBOARD_PORT .env | cut -d= -f2)"
        ;;
    stop)
        echo -e "${BLUE}Stopping all services...${NC}"
        docker-compose down
        echo -e "${GREEN}Services stopped successfully!${NC}"
        ;;
    restart)
        echo -e "${BLUE}Restarting all services...${NC}"
        docker-compose restart
        echo -e "${GREEN}Services restarted successfully!${NC}"
        ;;
    logs)
        echo -e "${BLUE}Showing logs from all services...${NC}"
        docker-compose logs -f
        ;;
    status)
        echo -e "${BLUE}Checking status of all services...${NC}"
        docker-compose ps
        ;;
    clean)
        echo -e "${YELLOW}Warning: This will remove all containers and volumes!${NC}"
        read -p "Are you sure you want to continue? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Removing all containers and volumes...${NC}"
            docker-compose down -v
            echo -e "${GREEN}Cleanup completed successfully!${NC}"
        fi
        ;;
    build)
        check_env_file
        check_demo_data
        ensure_dashboard_exists
        echo -e "${BLUE}Building all images...${NC}"
        docker-compose build --no-cache
        echo -e "${GREEN}Build completed successfully!${NC}"
        ;;
    demo)
        check_env_file
        check_demo_data
        ensure_dashboard_exists
        echo -e "${BLUE}Starting in demo mode...${NC}"
        # Set demo-specific environment variables
        export LOG_LEVEL=debug
        export DASHBOARD_REFRESH=2
        docker-compose up -d
        echo -e "${GREEN}Demo mode started successfully!${NC}"
        echo -e "\nAccess points:"
        echo -e "  - Gateway: http://localhost:$(grep GATEWAY_PORT .env | cut -d= -f2)"
        echo -e "  - Signer: http://localhost:$(grep SIGNER_PORT .env | cut -d= -f2)"
        echo -e "  - Receipts: http://localhost:$(grep RECEIPTS_PORT .env | cut -d= -f2)"
        echo -e "  - Dashboard: http://localhost:$(grep DASHBOARD_PORT .env | cut -d= -f2)"
        ;;
    help)
        show_usage
        ;;
    *)
        echo -e "${RED}Error: Unknown option '$1'${NC}"
        show_usage
        exit 1
        ;;
esac

# Cloud deployment suggestions
if [ "$1" == "start" ] || [ "$1" == "demo" ]; then
    echo -e "\n${BLUE}Cloud Deployment Options:${NC}"
    echo -e "  - ${YELLOW}AWS EC2 (Free Tier):${NC} Use t2.micro with Docker installed"
    echo -e "  - ${YELLOW}Railway:${NC} Push to GitHub and connect repository to Railway"
    echo -e "  - ${YELLOW}Render:${NC} Use Web Service with Docker runtime"
    echo -e "  - ${YELLOW}Digital Ocean:${NC} Use App Platform or $5 Droplet"
    echo -e "\nFor cloud deployment, ensure ports are properly exposed in security groups/firewalls"
    echo -e "For production, consider using managed databases instead of container volumes"
fi

exit 0