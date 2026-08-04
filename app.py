import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from security_engine import (
    generate_or_load_key,
    scan_excel_for_sensitive_data,
    encrypt_file,
    decrypt_file
)

# ---------------------------------------------------------
# 1. FASTAPI APPLICATION SETUP
# ---------------------------------------------------------
app = FastAPI(
    title="CNI & Ministry Secure Transfer",
    version="1.0.0"
)

# ---------------------------------------------------------
# 2. KEY INITIALIZATION & DIRECTORY CONFIGURATION
# ---------------------------------------------------------
# Load or generate 256-bit AES key for REST runtime
AES_KEY = generate_or_load_key()

# Define local file storage paths
UPLOAD_DIR = "storage/temp_uploads"
ENCRYPTED_DIR = "storage/encrypted_files"
DECRYPTED_DIR = "storage/downloads"


os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ENCRYPTED_DIR, exist_ok=True)
os.makedirs(DECRYPTED_DIR, exist_ok=True)


# ---------------------------------------------------------
# 3. HEALTHCHECK ENDPOINT
# ---------------------------------------------------------
@app.get("/")
def health_check():
    """
    Root endpoint to verify operational status of the REST API server.
    """
    return {"status": "online", "message": "FastAPI REST Server is running."}


# ---------------------------------------------------------
# 4. MINISTRY OF INTERIOR ENDPOINT (SCAN & ENCRYPT)
# ---------------------------------------------------------
@app.post("/api/interior/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Handles incoming file uploads from the Ministry of Interior:
    1- Validates file format (.xlsx, .xls)
    2- Saves stream to temporary disk storage
    3- Scans cell contents for sensitive citizen data (CIN / Phone)
    4- Encrypts payload with AES-256-GCM
    5- Removes unencrypted temporary file
    """
    # 1. Validate extension
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed.")

    temp_path = os.path.join(UPLOAD_DIR, file.filename)
    encrypted_path = os.path.join(ENCRYPTED_DIR, f"{file.filename}.enc")

    # 2. Save incoming stream temporarily
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Execute PII scanner logic
    has_sensitive, findings = scan_excel_for_sensitive_data(temp_path)

    # 4. Execute AES-256-GCM encryption logic
    encrypt_file(temp_path, encrypted_path, AES_KEY)

    # 5. Remove plain-text temporary file from disk
    if os.path.exists(temp_path):
        os.remove(temp_path)

    return {
        "status": "success",
        "filename": file.filename,
        "contains_sensitive_data": has_sensitive,
        "scan_findings": findings,
        "message": "File scanned, encrypted with AES-256-GCM, and stored."
    }


# ---------------------------------------------------------
# 5. CNI ENDPOINT (DECRYPT & DOWNLOAD)
# ---------------------------------------------------------
@app.get("/api/cni/download/{file_name}")
async def download_file(file_name: str):
    """
    Handles file retrieval requests for CNI:
    1- Verifies presence of requested encrypted file (.enc)
    2- Decrypts and validates authentication tag via AES-256-GCM
    3- Streams restored Excel document back to client
    """
    encrypted_path = os.path.join(ENCRYPTED_DIR, f"{file_name}.enc")
    restored_path = os.path.join(DECRYPTED_DIR, file_name)

    # 1. Verify encrypted target exists
    if not os.path.exists(encrypted_path):
        raise HTTPException(status_code=404, detail="Requested file not found in encrypted storage.")

    # 2. Execute AES-256-GCM decryption logic
    decrypt_file(encrypted_path, restored_path, AES_KEY)

    # 3. Stream restored Excel file over HTTP
    return FileResponse(
        path=restored_path,
        filename=f"decrypted_{file_name}",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ---------------------------------------------------------
# 6. STANDALONE REST API RUNNER
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("=== STARTING FASTAPI REST SERVER ===")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)