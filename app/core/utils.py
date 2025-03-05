from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.core.config import SECRET_KEY, ALGORITHM, pwd_context, fake_users_db
from app.models.user import UserInDB

def verify_password(plain_password, hashed_password):
    """Verify if a given password matches the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str):
    """Retrieve user from the database."""
    user = db.get(username)
    if user:
        return UserInDB(**user)

def authenticate_user(fake_db, username: str, password: str):
    """Authenticate user by checking username and password."""
    user = get_user(fake_db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT token with an expiration time."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
