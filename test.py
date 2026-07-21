import os
import pandas as pd
from security_engine import (
    generate_or_load_key,
    scan_excel_for_sensitive_data,
    encrypt_file,
    decrypt_file
)

def run_full_test():
    file_name = "ministry_test.xlsx"
    encrypted_name = "ministry_test.enc"
    restored_name = "ministry_restored.xlsx"

    # 1. CREATE REAL EXCEL FILE FOR TESTING
    print("--- 1. CREATING TEST EXCEL FILE ---")
    data = {
        "CIN": ["01234567", "09876543"],
        "Nom": ["Ben Ali", "Gharbi"],
        "Prénom": ["Mohamed", "Sarra"],
        "Date_Naissance": ["15/04/1995", "22/10/2000"],
        "Lieu_Naissance": ["Tunis", "Sfax"],
        "Téléphone": ["21000111", "98123456"]
    }
    df = pd.DataFrame(data)
    df.to_excel(file_name, index=False)
    print(f"[+] Created real Excel file: '{file_name}'")

    # 2. LOAD AES-256 KEY
    print("\n--- 2. LOADING AES-256 KEY ---")
    key = generate_or_load_key()
    print(f"[+] Key loaded: {key[:8].hex()}... (256-bit)")

    # 3. SCAN FILE
    print("\n--- 3. SCANNING EXCEL FOR SENSITIVE DATA ---")
    has_sensitive, issues = scan_excel_for_sensitive_data(file_name)
    print(f"[+] Sensitive Data Detected: {has_sensitive}")
    for issue in issues:
        print(f"    - {issue}")

    # 4. ENCRYPT FILE
    print("\n--- 4. ENCRYPTING FILE (AES-256-GCM) ---")
    encrypt_file(file_name, encrypted_name, key)
    print(f"[+] Encrypted '{file_name}' -> '{encrypted_name}'")

    # 5. DECRYPT FILE
    print("\n--- 5. DECRYPTING FILE ---")
    decrypt_file(encrypted_name, restored_name, key)
    print(f"[+] Decrypted '{encrypted_name}' -> '{restored_name}'")

    print("\n==========================================")
    print("[SUCCESS] Test completed! Check your file explorer for:")
    print(f" 1. {file_name} (Original Excel)")
    print(f" 2. {encrypted_name} (Encrypted payload)")
    print(f" 3. {restored_name} (Decrypted Excel)")
    print("==========================================")

if __name__ == "__main__":
    run_full_test()