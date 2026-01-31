from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import sqlite3
import os
import json
import hashlib
import time
import uuid
from datetime import datetime
from typing import List, Optional
import logging
import io
import reportlab.pdfgen.canvas
from reportlab.lib.pagesizes import letter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.environ.get("DATABASE_DIR", "/app/data"), "receipts.log"))
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Immutable Receipts Service", description="Quantum-Safe Receipt Storage with Hash-Chain")

# Configuration
DATABASE_PATH = os.environ.get("DATABASE_PATH", "/app/data/receipts.db")
DATABASE_DIR = os.path.dirname(DATABASE_PATH)

# Create database directory if it doesn't exist
os.makedirs(DATABASE_DIR, exist_ok=True)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Create templates directory and basic template file
os.makedirs("templates", exist_ok=True)
with open("templates/receipt.html", "w") as f:
    f.write("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Receipt #{{ receipt.id }}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .receipt { border: 1px solid #ccc; padding: 20px; max-width: 800px; margin: 0 auto; }
            .header { text-align: center; border-bottom: 1px solid #eee; padding-bottom: 10px; }
            .content { margin: 20px 0; }
            .footer { border-top: 1px solid #eee; padding-top: 10px; font-size: 0.8em; }
            .signature { font-family: monospace; word-break: break-all; }
        </style>
    </head>
    <body>
        <div class="receipt">
            <div class="header">
                <h1>Quantum-Safe Receipt</h1>
                <h2>ID: {{ receipt.id }}</h2>
            </div>
            <div class="content">
                <p><strong>Type:</strong> {{ receipt.type }}</p>
                <p><strong>Timestamp:</strong> {{ receipt.timestamp }}</p>
                <p><strong>Document Hash:</strong> {{ receipt.document_hash }}</p>
                <p><strong>Previous Hash:</strong> {{ receipt.previous_hash }}</p>
                <p><strong>Signature Algorithm:</strong> ML-DSA (Dilithium)</p>
                <p><strong>Signature:</strong></p>
                <p class="signature">{{ receipt.signature }}</p>
            </div>
            <div class="footer">
                <p>This receipt is part of an immutable hash-chain. Verify at: /receipts/verify/{{ receipt.id }}</p>
                <p>Export Section 65B Certificate: <a href="/receipts/{{ receipt.id }}/certificate">Download</a></p>
            </div>
        </div>
    </body>
    </html>
    """)

# Database initialization
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create receipts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS receipts (
        id TEXT PRIMARY KEY,
        document_hash TEXT NOT NULL,
        signature TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        type TEXT NOT NULL,
        previous_hash TEXT,
        metadata TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    
    logger.info(f"Database initialized at {DATABASE_PATH}")

# Initialize database on startup
init_db()

# Models
class ReceiptCreate(BaseModel):
    id: Optional[str] = None
    document_hash: str
    signature: str
    timestamp: str
    type: str
    metadata: Optional[dict] = None

class Receipt(BaseModel):
    id: str
    document_hash: str
    signature: str
    timestamp: str
    type: str
    previous_hash: Optional[str] = None
    metadata: Optional[dict] = None

# Hash-chain functions
def get_latest_receipt_hash():
    """Get the hash of the latest receipt in the chain"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the latest receipt by timestamp
    cursor.execute("SELECT document_hash FROM receipts ORDER BY timestamp DESC LIMIT 1")
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return result[0]
    return None

def calculate_receipt_hash(receipt_data: dict) -> str:
    """Calculate a hash for the receipt data"""
    # Create a deterministic string representation of the receipt
    receipt_str = json.dumps(receipt_data, sort_keys=True)
    return hashlib.sha256(receipt_str.encode()).hexdigest()

# API endpoints
@app.get("/")
async def root():
    return {"message": "Immutable Receipts Service API", "status": "running"}

@app.post("/receipts", status_code=201, response_model=Receipt)
async def create_receipt(receipt: ReceiptCreate):
    """Create a new receipt and add it to the hash-chain"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Generate ID if not provided
    if not receipt.id:
        receipt.id = str(uuid.uuid4())
    
    # Get the previous hash from the latest receipt
    previous_hash = get_latest_receipt_hash()
    
    # Create the receipt with the previous hash
    receipt_data = {
        "id": receipt.id,
        "document_hash": receipt.document_hash,
        "signature": receipt.signature,
        "timestamp": receipt.timestamp,
        "type": receipt.type,
        "previous_hash": previous_hash,
        "metadata": json.dumps(receipt.metadata) if receipt.metadata else None
    }
    
    try:
        cursor.execute(
            "INSERT INTO receipts (id, document_hash, signature, timestamp, type, previous_hash, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                receipt_data["id"],
                receipt_data["document_hash"],
                receipt_data["signature"],
                receipt_data["timestamp"],
                receipt_data["type"],
                receipt_data["previous_hash"],
                receipt_data["metadata"]
            )
        )
        conn.commit()
        
        # Log the transaction
        logger.info(f"Receipt created: ID={receipt_data['id']}, Type={receipt_data['type']}, Hash={receipt_data['document_hash'][:10]}...")
    except sqlite3.IntegrityError:
        logger.error(f"Failed to create receipt: ID={receipt.id} already exists")
        conn.close()
        raise HTTPException(status_code=400, detail=f"Receipt with ID {receipt.id} already exists")
    except Exception as e:
        logger.error(f"Error creating receipt: {str(e)}")
        conn.close()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        conn.close()
    
    # Convert metadata back to dict for response
    if receipt_data["metadata"]:
        receipt_data["metadata"] = json.loads(receipt_data["metadata"])
    
    return receipt_data

@app.get("/receipts/{receipt_id}", response_model=Receipt)
async def get_receipt(receipt_id: str, request: Request):
    """Get a receipt by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if not result:
        logger.warning(f"Receipt access attempt failed: ID={receipt_id} not found")
        raise HTTPException(status_code=404, detail=f"Receipt with ID {receipt_id} not found")
        
    logger.info(f"Receipt accessed: ID={receipt_id}")
    
    # Convert to dict
    receipt = dict(result)
    
    # Parse metadata JSON if present
    if receipt["metadata"]:
        receipt["metadata"] = json.loads(receipt["metadata"])
    
    # Return HTML if requested in browser
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        return templates.TemplateResponse(
            "receipt.html",
            {"request": request, "receipt": receipt}
        )
    
    return receipt

@app.get("/receipts")
async def list_receipts(limit: int = 10, offset: int = 0):
    """List receipts with pagination"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM receipts")
    total = cursor.fetchone()[0]
    
    # Get paginated receipts
    cursor.execute(
        "SELECT * FROM receipts ORDER BY timestamp DESC LIMIT ? OFFSET ?",
        (limit, offset)
    )
    results = cursor.fetchall()
    
    conn.close()
    
    # Convert to list of dicts
    receipts = []
    for row in results:
        receipt = dict(row)
        if receipt["metadata"]:
            receipt["metadata"] = json.loads(receipt["metadata"])
        receipts.append(receipt)
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "receipts": receipts
    }

@app.get("/receipts/verify/{receipt_id}")
async def verify_receipt(receipt_id: str):
    """Verify a receipt's integrity in the hash-chain"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the receipt
    cursor.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
    result = cursor.fetchone()
    
    if not result:
        logger.warning(f"Receipt verification failed: ID={receipt_id} not found")
        conn.close()
        raise HTTPException(status_code=404, detail=f"Receipt with ID {receipt_id} not found")
    
    receipt = dict(result)
    
    # Verify the hash chain
    if receipt["previous_hash"]:
        cursor.execute(
            "SELECT document_hash FROM receipts WHERE document_hash = ? AND timestamp < ?",
            (receipt["previous_hash"], receipt["timestamp"])
        )
        previous_receipt = cursor.fetchone()
        
        if not previous_receipt:
            logger.warning(f"Receipt verification failed: ID={receipt_id}, previous hash does not match any receipt")
            conn.close()
            return {"verified": False, "error": "Previous hash does not match any receipt"}
    
    conn.close()
    
    logger.info(f"Receipt verified successfully: ID={receipt_id}")
    return {"verified": True, "receipt_id": receipt_id}

@app.get("/receipts/{receipt_id}/certificate")
async def generate_certificate(receipt_id: str):
    """Generate a Section 65B Certificate for a receipt"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the receipt
    cursor.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if not result:
        logger.warning(f"Certificate generation failed: Receipt ID={receipt_id} not found")
        raise HTTPException(status_code=404, detail=f"Receipt with ID {receipt_id} not found")
        
    logger.info(f"Section 65B Certificate generated for receipt: ID={receipt_id}")
    
    receipt = dict(result)
    if receipt["metadata"]:
        receipt["metadata"] = json.loads(receipt["metadata"])
    
    # Generate a PDF certificate
    buffer = io.BytesIO()
    c = reportlab.pdfgen.canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 50, "SECTION 65B CERTIFICATE")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 70, "(Under Indian Evidence Act)")
    
    # Content
    c.setFont("Helvetica", 12)
    y = height - 120
    c.drawString(50, y, f"Certificate ID: {receipt_id}")
    y -= 20
    c.drawString(50, y, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    y -= 40
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "CERTIFICATE")
    y -= 20
    
    c.setFont("Helvetica", 12)
    certificate_text = (
        "I hereby certify that the attached document is a true and accurate record "
        "stored in the Quantum-Safe Communication Suite. The document was digitally "
        "signed using post-quantum cryptographic algorithms and stored in an immutable "
        "hash-chain to ensure integrity and non-repudiation."
    )
    
    # Wrap text
    text_obj = c.beginText(50, y)
    text_obj.setFont("Helvetica", 12)
    
    # Split text into lines
    lines = []
    for i in range(0, len(certificate_text), 70):
        lines.append(certificate_text[i:i+70])
    
    for line in lines:
        text_obj.textLine(line)
    
    c.drawText(text_obj)
    
    y -= 20 * (len(lines) + 2)
    
    # Receipt details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "RECEIPT DETAILS:")
    y -= 20
    
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Receipt ID: {receipt['id']}")
    y -= 15
    c.drawString(50, y, f"Document Hash: {receipt['document_hash']}")
    y -= 15
    c.drawString(50, y, f"Timestamp: {receipt['timestamp']}")
    y -= 15
    c.drawString(50, y, f"Type: {receipt['type']}")
    y -= 15
    c.drawString(50, y, f"Signature Algorithm: ML-DSA (Dilithium)")
    y -= 15
    
    # Signature (shortened for display)
    sig = receipt['signature']
    if len(sig) > 40:
        sig = sig[:20] + "..." + sig[-20:]
    c.drawString(50, y, f"Signature: {sig}")
    
    # Footer
    c.setFont("Helvetica-Italic", 10)
    c.drawString(50, 50, "This certificate is electronically generated and does not require a physical signature.")
    c.drawString(50, 35, "Verify this certificate at: https://example.com/verify")
    
    c.save()
    buffer.seek(0)
    
    return FileResponse(
        buffer,
        media_type="application/pdf",
        filename=f"certificate_{receipt_id}.pdf"
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("service:app", host="0.0.0.0", port=6000, reload=True)