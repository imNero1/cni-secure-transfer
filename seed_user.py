from database import SessionLocal, init_db, User
from auth import hash_password

init_db()
db = SessionLocal()


username = "Samurai_69"
password = "partylike2023"   
role = "CNI"    
   
username = "interior"
password = "interior"
role = "MINISTRY_OF_INTERIOR"

user = db.query(User).filter(User.username == username).first()
if user:
    user.hashed_password = hash_password(password)
    print(f"[+] Password reset for '{username}'.")
else:
    user = User(username=username, hashed_password=hash_password(password), role=role)
    db.add(user)
    print(f"[+] Created user '{username}'.")

db.commit()
db.close()


