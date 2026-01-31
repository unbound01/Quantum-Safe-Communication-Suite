# Unified Quantum-Safe Communication Suite - Deployment Script (PowerShell version)
# This script automates the build and deployment process

# Function to display usage information
function Show-Usage {
    Write-Host "Unified Quantum-Safe Communication Suite - Deployment Script" -ForegroundColor Blue
    Write-Host "Usage: .\deploy.ps1 [OPTION]"
    Write-Host "Options:"
    Write-Host "  start       Build and start all services" -ForegroundColor Green
    Write-Host "  stop        Stop all services" -ForegroundColor Green
    Write-Host "  restart     Restart all services" -ForegroundColor Green
    Write-Host "  logs        View service logs" -ForegroundColor Green
    Write-Host "  status      Check service status" -ForegroundColor Green
    Write-Host "  clean       Remove containers and volumes" -ForegroundColor Green
    Write-Host "  build       Build services without starting" -ForegroundColor Green
    Write-Host "  demo        Run in demo mode with optimized settings" -ForegroundColor Green
}

# Function to check if Docker is installed
function Check-Docker {
    try {
        docker --version | Out-Null
        Write-Host "Docker is installed" -ForegroundColor Green
    } catch {
        Write-Host "Docker is not installed or not in PATH" -ForegroundColor Red
        Write-Host "Please install Docker and Docker Compose before proceeding."
        exit 1
    }
}

# Function to check if .env file exists, create if not
function Check-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Host "Creating default .env file..." -ForegroundColor Yellow
        
        $envContent = @"
# Unified Quantum-Safe Communication Suite - Environment Variables

# Service Ports
GATEWAY_PORT=2525
SIGNER_PORT=5000
RECEIPTS_PORT=6000
DASHBOARD_PORT=8080

# Mail Configuration
MAIL_DOMAIN=quantum-safe.gov.in

# Logging
LOG_LEVEL=info

# Dashboard Configuration
DASHBOARD_REFRESH=5000

# Volume Names
RECEIPTS_VOLUME=receipts-data
SIGNER_VOLUME=signer-output

# Demo Data Path
DEMO_DATA_PATH=./demo-data
"@
        
        $envContent | Out-File -FilePath ".env" -Encoding utf8
        Write-Host "Created default .env file" -ForegroundColor Green
    } else {
        Write-Host ".env file exists" -ForegroundColor Green
    }
}

# Function to check if demo data exists
function Check-DemoData {
    if (-not (Test-Path "demo-data")) {
        Write-Host "Demo data directory not found" -ForegroundColor Red
        Write-Host "Creating demo-data directory..."
        New-Item -Path "demo-data" -ItemType Directory | Out-Null
        
        # Create sample demo files
        "Sample email content for demo" | Out-File -FilePath "demo-data/email_demo.txt" -Encoding utf8
        "Sample land record PDF content" | Out-File -FilePath "demo-data/land_record.pdf" -Encoding utf8
        "Sample PSU tender document" | Out-File -FilePath "demo-data/psu_tender.pdf" -Encoding utf8
        
        Write-Host "Created demo data directory with sample files" -ForegroundColor Green
    } else {
        Write-Host "Demo data directory exists" -ForegroundColor Green
    }
}

# Function to start services
function Start-Services {
    param (
        [switch]$Demo
    )
    
    Write-Host "Starting services..." -ForegroundColor Blue
    
    if ($Demo) {
        Write-Host "Running in DEMO mode with optimized settings" -ForegroundColor Yellow
        docker-compose up --build -d
    } else {
        docker-compose up --build -d
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Services started successfully" -ForegroundColor Green
        Write-Host "\nAccess points:" -ForegroundColor Blue
        Write-Host "  - PQC Email Gateway: localhost:2525" -ForegroundColor Green
        Write-Host "  - PDF Signer: http://localhost:5000" -ForegroundColor Green
        Write-Host "  - Receipts Service: http://localhost:6000" -ForegroundColor Green
        Write-Host "  - Monitoring Dashboard: http://localhost:8080" -ForegroundColor Green
    } else {
        Write-Host "Failed to start services" -ForegroundColor Red
    }
}

# Function to stop services
function Stop-AllServices {
    Write-Host "Stopping services..." -ForegroundColor Blue
    docker-compose down
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Services stopped successfully" -ForegroundColor Green
    } else {
        Write-Host "Failed to stop services" -ForegroundColor Red
    }
}

# Function to view logs
function View-Logs {
    Write-Host "Viewing logs (press Ctrl+C to exit)..." -ForegroundColor Blue
    docker-compose logs -f
}

# Function to check status
function Check-Status {
    Write-Host "Checking service status..." -ForegroundColor Blue
    docker-compose ps
}

# Function to clean up
function Clean-Environment {
    Write-Host "Cleaning up containers and volumes..." -ForegroundColor Blue
    docker-compose down -v
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Cleanup completed successfully" -ForegroundColor Green
    } else {
        Write-Host "Cleanup failed" -ForegroundColor Red
    }
}

# Function to build services
function Build-Services {
    Write-Host "Building services..." -ForegroundColor Blue
    docker-compose build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Services built successfully" -ForegroundColor Green
    } else {
        Write-Host "Failed to build services" -ForegroundColor Red
    }
}

# Main script execution
Check-Docker
Check-EnvFile

# Process command line arguments
if ($args.Count -eq 0) {
    Show-Usage
    exit 0
}

switch ($args[0].ToLower()) {
    "start" {
        Check-DemoData
        Start-Services
    }
    "stop" {
        Stop-AllServices
    }
    "restart" {
        Stop-AllServices
        Start-Services
    }
    "logs" {
        View-Logs
    }
    "status" {
        Check-Status
    }
    "clean" {
        Clean-Environment
    }
    "build" {
        Build-Services
    }
    "demo" {
        Check-DemoData
        Start-Services -Demo
    }
    default {
        Write-Host "Unknown option: $($args[0])" -ForegroundColor Red
        Show-Usage
        exit 1
    }
}