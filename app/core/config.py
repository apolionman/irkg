from datetime import timedelta
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='./.env')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Bearer Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mock database (Replace with real database)
fake_users_db = {
    "admin_dgx": {
        "username": "admin_dgx",
        "full_name": "I am Prepaire DGX",
        "email": "info@dgx.com",
        "hashed_password": pwd_context.hash("password123"),
        "disabled": False,
    }
}

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@app.get("/protected-route")
def protected_route(username: str = Depends(verify_token)):
    return {"message": f"Hello, {username}! You're authorized."}