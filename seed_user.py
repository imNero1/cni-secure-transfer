from database import SessionLocal, init_db, User
from auth import hash_password

init_db()
db = SessionLocal()

username = "Samurai_69"
password = "partylike2023"   
role = "CNI"              

existing = db.query(User).filter(User.username == username).first()
if existing:
    print(f"[!] User '{username}' already exists.")
else:
    user = User(username=username, hashed_password=hash_password(password), role=role)
    db.add(user)
    db.commit()
    print(f"[+] Created user '{username}' with role '{role}'.")

db.close()