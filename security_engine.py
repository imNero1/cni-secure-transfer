import os
import re
import pandas as pd
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ---------------------------------------------------------
# 1. AES-256 KEY MANAGEMENT
# ---------------------------------------------------------
def generate_or_load_key(key_file="secret.key"):
    """
    Generates a 256-bit (32 bytes) AES key or loads an existing one from disk.
    """
    try:
        with open(key_file, "rb") as f:
            return f.read()
    except FileNotFoundError:
        # Generates a cryptographically secure 256-bit key
        key = AESGCM.generate_key(bit_length=256)
        with open(key_file, "wb") as f:
            f.write(key)
        return key


# ---------------------------------------------------------
# 2. SENSITIVE DATA SCANNER (Ministry of Interior / CNI Specific)
# ---------------------------------------------------------
def scan_excel_for_sensitive_data(file_path):
    """
    Scans every cell of an Excel file for sensitive citizen data:
    - Tunisian CIN (8 digits)
    - Phone numbers (8 digits starting with 2, 5, 7, 9)
    - Identity fields (Nom, Prénom, Date de naissance, Lieu de naissance, etc.)
    """
    df = pd.read_excel(file_path)
    
    # Regex patterns
    cin_pattern = re.compile(r'\b\d{8}\b')
    phone_pattern = re.compile(r'\b[2579]\d{7}\b')
    
    # Specific identity keywords for Interior/CNI records
    identity_keywords = [
        "cin", "nom", "prenom", "prénom", 
        "date_naissance", "date de naissance", 
        "lieu_naissance", "lieu de naissance",
        "adresse", "telephone", 
    ]
    
    detected_issues = []

    # 1. Check Column Headers
    for col_name in df.columns:
        col_str = str(col_name).strip().lower()
        if any(kw == col_str or kw in col_str for kw in identity_keywords):
            detected_issues.append(f"Header '{col_name}': Identity field column detected")

    # 2. Check Cell Content
    for row_idx, row in df.iterrows():
        for col_name, value in row.items():
            val_str = str(value).strip()
            
            # Check for CIN pattern (8 digits)
            if cin_pattern.search(val_str):
                detected_issues.append(f"Row {row_idx + 2}, Col '{col_name}': Potential CIN detected ({val_str})")

            # Check for Phone pattern
            elif phone_pattern.search(val_str):
                detected_issues.append(f"Row {row_idx + 2}, Col '{col_name}': Potential Phone Number detected ({val_str})")

    has_sensitive_data = len(detected_issues) > 0
    return has_sensitive_data, detected_issues


# ---------------------------------------------------------
# 3. AES-256-GCM ENCRYPTION & DECRYPTION
# ---------------------------------------------------------
def encrypt_file(file_path, output_path, key):
    """
    Encrypts raw binary file bytes using AES-256-GCM.
    Prepends a 12-byte random nonce to the ciphertext for integrity checking.
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit unique initialization vector (nonce)
    
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    
    # Encrypt file bytes
    encrypted_bytes = aesgcm.encrypt(nonce, file_bytes, associated_data=None)
    
    # Store Nonce + Encrypted Content together
    with open(output_path, "wb") as f:
        f.write(nonce + encrypted_bytes)


def decrypt_file(encrypted_file_path, output_path, key):
    """
    Decrypts an AES-256-GCM encrypted file back into original Excel format.
    Checks authentication tag automatically to verify file was not tampered with.
    """
    aesgcm = AESGCM(key)
    
    with open(encrypted_file_path, "rb") as f:
        encrypted_data = f.read()
    
    # Extract the 12-byte nonce from the beginning of the file payload
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    
    # Decrypt and verify integrity
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    
    with open(output_path, "wb") as f:
        f.write(decrypted_bytes)


# ---------------------------------------------------------
# 4. VERIFICATION TEST
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=== TESTING AES-256 SECURITY ENGINE ===")
    
    # 1. Load/Generate 256-bit Key
    key = generate_or_load_key()
    print(f"[+] AES-256 Key Loaded (Length: {len(key) * 8} bits)")

    # 2. Scan Excel File
    has_sensitive, issues = scan_excel_for_sensitive_data("test_input.xlsx")
    print(f"\n[+] Sensitive Data Found: {has_sensitive}")
    for issue in issues:
        print(f"    - {issue}")

    # 3. Encrypt File
    encrypt_file("test_input.xlsx", "encrypted_file.enc", key)
    print("\n[+] File encrypted with AES-256-GCM -> 'encrypted_file.enc'")

    # 4. Decrypt File
    decrypt_file("encrypted_file.enc", "restored_output.xlsx", key)
    print("[+] File decrypted & verified -> 'restored_output.xlsx'")