# Unified Quantum-Safe Communication Suite

A comprehensive solution for quantum-resistant secure communications and document signing, designed for government and enterprise use.

## Overview

This project implements a suite of services that provide quantum-safe security for email communications and document signing. It is designed to protect against future threats from quantum computers, which could break current cryptographic algorithms like RSA and ECC using Shor's algorithm.

The system uses NIST-approved post-quantum cryptographic algorithms (ML-KEM768 and ML-DSA) that are resistant to attacks from quantum computers, ensuring long-term security for sensitive communications and documents. The solution is particularly valuable for:

- **Government Communications**: Secure transmission of classified information
- **Land Records**: Tamper-proof digital signing of property documents
- **Procurement Systems**: Secure tender document signing and verification
- **Legal Documents**: Court filings and evidence with Section 65B compliance
- **Financial Institutions**: Secure transactions with non-repudiation

## Key Components

1. **PQC Email Gateway** (Go) - TLS proxy with hybrid encryption (X25519 + ML-KEM768)
2. **PQC PDF Signer** (Python) - Quantum-safe document signing service using Dilithium (ML-DSA)
3. **Immutable Receipts Service** (Python) - Secure receipt storage with hash-chain for non-repudiation
4. **Monitoring Dashboard** (Python/Flask) - Real-time system monitoring and statistics

## Architecture

The system consists of the following components:

- **PQC Email Gateway**: A Go-based TLS proxy that sits in front of Postfix/Dovecot and enforces hybrid TLS (X25519 + ML-KEM768) and signs outgoing email headers with Dilithium (ML-DSA).
- **PQC PDF Signer**: A Python FastAPI service that signs and verifies PDFs using Dilithium (ML-DSA).
- **Immutable Receipts Service**: A Python FastAPI service that stores transaction receipts in a hash-chain using SQLite.
- **Monitoring Dashboard**: A Flask-based web application that provides real-time monitoring of all services, tracks statistics, and displays system health.

## Prerequisites

- Docker and Docker Compose
- Bash shell (for running demo scripts)
- OpenSSL (for TLS connections)
- curl (for API requests)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/quantum-safe-suite.git
cd quantum-safe-suite
```

### 2. Configure Environment

The system uses a `.env` file for configuration. A default one is provided, but you can customize it:

```bash
# Review and modify environment variables if needed
cat .env
```

### 3. Deploy the Services

Use the deployment script for easy setup:

```bash
chmod +x deploy.sh
./deploy.sh start    # Standard deployment
# OR
./deploy.sh demo     # Demo mode with optimized settings
```

This will start all services:
- PQC Email Gateway on port 2525
- PDF Signer on port 5000
- Receipts Service on port 6000
- Monitoring Dashboard on port 8080
- Postfix and Dovecot (internal network only)

Additional deployment commands:
```bash
./deploy.sh status   # Check service status
./deploy.sh logs     # View service logs
./deploy.sh restart  # Restart all services
./deploy.sh stop     # Stop all services
./deploy.sh clean    # Remove containers and volumes
```

### 4. Run Demo Scripts

The system comes with pre-configured demo data in the `demo-data` directory:
- `email_demo.txt` - Sample government email for secure transmission
- `land_record.pdf` - Sample land record document for signing
- `psu_tender.pdf` - Sample tender document for signing

#### Send a PQC-secured Email

```bash
chmod +x scripts/send_pqc_mail.sh
./scripts/send_pqc_mail.sh
```

This script will:
- Connect to the PQC Email Gateway using TLS
- Send the demo email with Dilithium signatures
- Display the negotiated TLS parameters and cipher suites
- Show the receipt ID for verification

#### Sign and Verify Land Records

```bash
chmod +x scripts/sign_pdf.sh
./scripts/sign_pdf.sh demo-data/land_record.pdf
```

This script will:
- Sign the land record PDF using quantum-resistant algorithms
- Verify the signature's integrity
- Generate a Section 65B Certificate for legal validity
- Store a receipt in the Immutable Receipts Service

#### Sign and Verify Tender Documents

```bash
chmod +x scripts/sign_pdf.sh
./scripts/sign_pdf.sh demo-data/psu_tender.pdf
```

This script will:
- Sign the tender document using the same quantum-resistant process
- Verify the signature and document integrity
- Generate a Section 65B Certificate
- Add the receipt to the immutable hash-chain

## Service Endpoints

### PQC Email Gateway

- SMTP: `localhost:2525`
- Health Check: `http://localhost:2525/health`

### PQC PDF Signer

- API: `http://localhost:5000`
- Sign PDF: `POST http://localhost:5000/sign`
- Verify PDF: `POST http://localhost:5000/verify`
- Health Check: `http://localhost:5000/health`
- Swagger UI: `http://localhost:5000/docs`

### Immutable Receipts Service

- API: `http://localhost:6000`
- View Receipt: `http://localhost:6000/receipts/{id}`
- List Receipts: `http://localhost:6000/receipts`
- Generate Certificate: `http://localhost:6000/receipts/{id}/certificate`
- Verify Receipt: `http://localhost:6000/receipts/verify/{id}`
- Health Check: `http://localhost:6000/health`
- Swagger UI: `http://localhost:6000/docs`

### Monitoring Dashboard

- Web UI: `http://localhost:8080`
- Statistics API: `http://localhost:8080/api/stats`
- Health Check: `http://localhost:8080/api/health`

## Implementation Notes

- This implementation uses simulated PQC functions for demonstration purposes.
- In a production environment, you would use liboqs and oqs-openssl for actual quantum-safe cryptography.
- The services are designed to be modular and can be deployed independently.
- The monitoring dashboard provides real-time statistics and health checks for all services.

## SIH Demo and Presentation

### Demo Script

A comprehensive demo script is available in `demo_script.md` with the following sections:

1. **Introduction**: Overview of quantum computing threats and our solution
2. **System Deployment**: Step-by-step deployment process
3. **Demo 1**: Quantum-safe email transmission
4. **Demo 2**: Land record signing with quantum-resistant algorithms
5. **Demo 3**: PSU tender document signing and verification
6. **Monitoring Dashboard**: Real-time system statistics and health monitoring
7. **Scalability and Cloud Deployment**: Options for scaling the solution
8. **Conclusion**: Summary of benefits and future roadmap
9. **Q&A**: Anticipated questions and prepared answers

### Presentation Materials

The `presentation_and_backup.md` file contains:

1. **PowerPoint Outline**: Slide structure for the SIH presentation
2. **Backup Strategy**: Contingency plans for demo failures
   - Pre-demo preparations (screenshots, videos, pre-signed documents)
   - Network fallback plans
   - Presentation contingencies
   - Emergency fallback procedures

## Cloud Deployment

The system can be deployed to any cloud provider that supports Docker containers:

1. **AWS**: Use ECS or EKS with ECR for container registry
2. **Azure**: Use AKS with ACR for container registry
3. **GCP**: Use GKE with GCR for container registry

For production deployments, consider:

- Using managed database services instead of SQLite
- Setting up proper TLS certificates for all services
- Implementing proper authentication and authorization
- Setting up monitoring and alerting using cloud provider tools

## Security Considerations

- The system uses post-quantum cryptography to protect against quantum computing attacks.
- ML-KEM768 provides 192 bits of security, resistant to Grover's algorithm.
- ML-DSA signatures ensure non-repudiation and integrity of documents and emails.
- The immutable receipts service ensures that signed documents cannot be tampered with.
- All services implement health checks and proper error handling.
- The system is designed to be compliant with Section 65B of the Indian Evidence Act.
- The monitoring dashboard provides real-time visibility into system health and security status.

## Technical Details

### Cryptographic Algorithms

- **ML-KEM768**: Module-Lattice-based Key Encapsulation Mechanism with 768-bit security
  - Resistant to quantum attacks using Shor's algorithm
  - Provides 192 bits of security (NIST Level 3)
  - Used for secure key exchange in TLS connections

- **ML-DSA**: Module-Lattice-based Digital Signature Algorithm
  - Quantum-resistant digital signatures
  - Used for signing emails and PDF documents
  - Provides non-repudiation and integrity verification

### Email Security

- Hybrid TLS implementation combining classical (X25519) and post-quantum (ML-KEM768) algorithms
- Email headers signed with ML-DSA for integrity and authenticity
- Receipts generated for all email transactions

### Document Security

- PDFs signed with ML-DSA signatures
- Section 65B certificates generated automatically
- Immutable hash-chain ensures document integrity over time
- All operations logged and monitored

## License

MIT

## Benefits and Impact

- **Future-Proof Security**: Protection against both classical and quantum computing threats
- **Regulatory Compliance**: Meets Section 65B requirements for digital evidence
- **Transparency**: Real-time monitoring and auditing capabilities
- **Scalability**: Containerized architecture for easy deployment and scaling
- **Interoperability**: Works with existing systems through standard protocols
- **Cost-Effective**: Open-source components reduce implementation costs

## Conclusion

The Unified Quantum-Safe Communication Suite provides a comprehensive solution for organizations looking to protect their communications and documents against current and future threats. By implementing post-quantum cryptography today, organizations can ensure their sensitive data remains secure even in the era of quantum computing.