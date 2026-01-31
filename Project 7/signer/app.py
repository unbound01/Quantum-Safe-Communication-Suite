from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import os
import hashlib
import time
import requests
import logging
import uuid
from typing import Optional
from datetime import datetime
import PyPDF2
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="PQC PDF Signer", description="Quantum-Safe PDF Signing Service using ML-DSA (Dilithium)")

# Configuration
RECEIPTS_SERVICE_URL = os.environ.get("RECEIPTS_SERVICE_URL", "http://receipts:6000")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/tmp/signed_pdfs")

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Simulated PQC functions (in production, these would use liboqs)
def sign_with_dilithium(data: bytes) -> bytes:
    """Simulate signing data with Dilithium (ML-DSA)"""
    # In production: Would use liboqs to generate a Dilithium signature
    # For demo, simulate with a placeholder
    return f"DILITHIUM-SIGNATURE-{hashlib.sha256(data).hexdigest()[:16]}".encode()

def verify_dilithium_signature(data: bytes, signature: bytes) -> bool:
    """Simulate verifying a Dilithium signature"""
    # In production: Would use liboqs to verify the signature
    # For demo, regenerate the signature and compare
    expected_sig = f"DILITHIUM-SIGNATURE-{hashlib.sha256(data).hexdigest()[:16]}".encode()
    return signature == expected_sig

# PDF signing functions
def sign_pdf(pdf_data: bytes) -> tuple[bytes, bytes]:
    """Sign a PDF with Dilithium and return the signed PDF and signature"""
    # Calculate hash of the PDF
    pdf_hash = hashlib.sha256(pdf_data).digest()
    
    # Generate signature using Dilithium
    signature = sign_with_dilithium(pdf_data)
    
    # In a real implementation, we would embed the signature in the PDF
    # For this demo, we'll add a simple annotation with the signature
    try:
        # Read the PDF
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_data))
        pdf_writer = PyPDF2.PdfWriter()
        
        # Copy all pages
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            pdf_writer.add_page(page)
        
        # Add metadata with signature
        pdf_writer.add_metadata({
            "/PQC-Signature": signature.decode(),
            "/PQC-SignatureDate": datetime.now().isoformat(),
            "/PQC-Algorithm": "ML-DSA (Dilithium)"
        })
        
        # Write the signed PDF to a BytesIO object
        output_pdf = BytesIO()
        pdf_writer.write(output_pdf)
        output_pdf.seek(0)
        
        return output_pdf.getvalue(), signature
    except Exception as e:
        logger.error(f"Error signing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error signing PDF: {str(e)}")

def extract_signature_from_pdf(pdf_data: bytes) -> Optional[bytes]:
    """Extract the Dilithium signature from a signed PDF"""
    try:
        # Read the PDF
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_data))
        
        # Get the signature from metadata
        if "/PQC-Signature" in pdf_reader.metadata:
            return pdf_reader.metadata["/PQC-Signature"].encode()
        
        return None
    except Exception as e:
        logger.error(f"Error extracting signature: {e}")
        return None

def store_receipt(pdf_data: bytes, signature: bytes) -> str:
    """Store a receipt in the receipts service"""
    receipt_id = str(uuid.uuid4())
    
    try:
        # In production: Make an HTTP request to the receipts service
        # For demo, just log the receipt
        logger.info(f"Storing receipt {receipt_id} for PDF with signature: {signature[:20]}...")
        
        # Attempt to store in receipts service
        response = requests.post(
            f"{RECEIPTS_SERVICE_URL}/receipts",
            json={
                "id": receipt_id,
                "document_hash": hashlib.sha256(pdf_data).hexdigest(),
                "signature": signature.decode(),
                "timestamp": datetime.now().isoformat(),
                "type": "pdf_signing"
            },
            timeout=5
        )
        
        if response.status_code == 201:
            return receipt_id
        else:
            logger.warning(f"Failed to store receipt: {response.text}")
            return receipt_id
    except Exception as e:
        logger.error(f"Error storing receipt: {e}")
        return receipt_id

# API endpoints
@app.get("/")
async def root():
    return {"message": "PQC PDF Signer API", "status": "running"}

@app.post("/sign")
async def sign_pdf_endpoint(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Sign a PDF using Dilithium (ML-DSA)"""
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Read the PDF file
    pdf_data = await file.read()
    
    # Sign the PDF
    signed_pdf, signature = sign_pdf(pdf_data)
    
    # Generate output filename
    base_name = os.path.splitext(file.filename)[0]
    output_filename = f"{base_name}-signed.pdf"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Save the signed PDF
    with open(output_path, "wb") as f:
        f.write(signed_pdf)
    
    # Store receipt in background
    receipt_id = store_receipt(signed_pdf, signature)
    
    # Return the signed PDF
    return FileResponse(
        path=output_path,
        filename=output_filename,
        media_type="application/pdf",
        headers={
            "X-PQC-Signature": signature.decode(),
            "X-Receipt-ID": receipt_id
        }
    )

@app.post("/verify")
async def verify_pdf_endpoint(file: UploadFile = File(...)):
    """Verify a signed PDF"""
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Read the PDF file
    pdf_data = await file.read()
    
    # Extract the signature
    signature = extract_signature_from_pdf(pdf_data)
    if not signature:
        return JSONResponse(
            status_code=400,
            content={"verified": False, "error": "No signature found in the PDF"}
        )
    
    # Verify the signature
    is_valid = verify_dilithium_signature(pdf_data, signature)
    
    return {
        "verified": is_valid,
        "algorithm": "ML-DSA (Dilithium)",
        "signature": signature.decode()
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)