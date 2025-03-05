from datetime import timedelta
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='./.env')

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
