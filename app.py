import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from security_engine import (
    generate_or_load_key,
    scan_excel_for_sensitive_data,
    encrypt_file,
    decrypt_file
)
from database import init_db, get_db, log_transfer_event, fetch_all_logs
from auth import create_token, require_role

# ---------------------------------------------------------
# 1. FASTAPI SETUP
# ---------------------------------------------------------
app = FastAPI(
    title="CNI & Ministry Secure Transfer API",
    version="1.0.0"
)

# Initialize database gracefully on server startup
@app.on_event("startup")
def on_startup():
    try:
        init_db()
        print("[+] PostgreSQL database connected & tables initialized successfully.")
    except Exception as e:
        print(f"[!] Warning: Could not connect to PostgreSQL on startup: {e}")


# ---------------------------------------------------------
# 2. KEY INITIALIZATION & DIRECTORY CONFIGURATION
# ---------------------------------------------------------
AES_KEY = generate_or_load_key()

UPLOAD_DIR = "storage/temp_uploads"
ENCRYPTED_DIR = "storage/encrypted_files"
DECRYPTED_DIR = "storage/downloads"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ENCRYPTED_DIR, exist_ok=True)
os.makedirs(DECRYPTED_DIR, exist_ok=True)


# ---------------------------------------------------------
# 3. HEALTHCHECK & AUTH TEST ENDPOINTS
# ---------------------------------------------------------
@app.get("/")
def health_check():
    return {"status": "online", "message": "FastAPI REST Server is running."}


@app.get("/api/auth/token/{role}")
def get_test_token(role: str):
    """Generates a test JWT token for 'MINISTRY_OF_INTERIOR' or 'CNI'."""
    if role not in ["MINISTRY_OF_INTERIOR", "CNI"]:
        raise HTTPException(status_code=400, detail="Invalid role specified. Use 'MINISTRY_OF_INTERIOR' or 'CNI'.")
    token = create_token(role=role)
    return {"role": role, "access_token": token, "token_type": "bearer"}


@app.get("/api/admin/logs")
def get_audit_logs(db: Session = Depends(get_db)):
    """Retrieves all transfer audit records stored in PostgreSQL."""
    return fetch_all_logs(db)


# ---------------------------------------------------------
# 4. MINISTRY OF INTERIOR ENDPOINT (SCAN, ENCRYPT & LOG)
# ---------------------------------------------------------
@app.post("/api/interior/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor_role: str = Depends(require_role("MINISTRY_OF_INTERIOR"))
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed.")

    temp_path = os.path.join(UPLOAD_DIR, file.filename)
    encrypted_path = os.path.join(ENCRYPTED_DIR, f"{file.filename}.enc")

    # 1. Save incoming stream temporarily
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Run PII scanner
    has_sensitive, findings = scan_excel_for_sensitive_data(temp_path)

    # 3. Encrypt file with AES-256-GCM
    encrypt_file(temp_path, encrypted_path, AES_KEY)

    # 4. Remove plain text file
    if os.path.exists(temp_path):
        os.remove(temp_path)

    # 5. Write audit log entry to PostgreSQL
    log_transfer_event(
        db=db,
        filename=file.filename,
        actor_role=actor_role,
        action_type="UPLOAD_ENCRYPT",
        has_sensitive_data=has_sensitive
    )

    return {
        "status": "success",
        "filename": file.filename,
        "actor_role": actor_role,
        "contains_sensitive_data": has_sensitive,
        "scan_findings": findings,
        "message": "File scanned, encrypted, stored, and logged in database."
    }


# ---------------------------------------------------------
# 5. CNI ENDPOINT (DECRYPT, DOWNLOAD & LOG)
# ---------------------------------------------------------
@app.get("/api/cni/download/{file_name}")
async def download_file(
    file_name: str,
    db: Session = Depends(get_db),
    actor_role: str = Depends(require_role("CNI"))
):
    encrypted_path = os.path.join(ENCRYPTED_DIR, f"{file_name}.enc")
    restored_path = os.path.join(DECRYPTED_DIR, file_name)

    if not os.path.exists(encrypted_path):
        raise HTTPException(status_code=404, detail="Requested file not found in encrypted storage.")

    # 1. Decrypt file
    decrypt_file(encrypted_path, restored_path, AES_KEY)

    # 2. Write download audit record to PostgreSQL
    log_transfer_event(
        db=db,
        filename=file_name,
        actor_role=actor_role,
        action_type="DECRYPT_DOWNLOAD",
        has_sensitive_data=False
    )

    # 3. Stream restored file back to client
    return FileResponse(
        path=restored_path,
        filename=f"decrypted_{file_name}",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ---------------------------------------------------------
# 6. RUNNER
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("=== STARTING FASTAPI REST SERVER ===")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)