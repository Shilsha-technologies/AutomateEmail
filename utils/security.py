# utils/security.py
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.db import get_db

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY").encode()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
fernet = Fernet(ENCRYPTION_KEY)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/employee/login") 
bearer_scheme = HTTPBearer()



# password

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# JWT

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# Encrypt/decrypt OAuth tokens

def encrypt_token(data: str) -> str:
    return fernet.encrypt(data.encode()).decode()

def decrypt_token(data: str) -> str:
    return fernet.decrypt(data.encode()).decode()


# ── Employee auth guard       
def get_current_employee(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    from models.employee import Employee, TokenBlacklist

    token = credentials.credentials  

    if db.query(TokenBlacklist).filter_by(token=token).first():
        raise HTTPException(status_code=401, detail="Token has been invalidated. Please login again.")

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("role") is None:
        raise HTTPException(status_code=401, detail="Employee login required")

    employee_id = payload.get("employee_id") or payload.get("sub")
    if employee_id is None:
        raise HTTPException(status_code=401, detail="Invalid employee token")

    employee = db.query(Employee).filter(Employee.id == int(employee_id)).first()
    if not employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    if not employee.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    return {
        "sub": str(employee.id),
        "employee_id": employee.id,
        "employee_email": employee.email,
        "name": employee.name,
        "role": employee.user_type,
        "session_id": payload.get("session_id"),
        "login_at": payload.get("login_at"),
    }
