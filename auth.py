"""
Authentication helper functions.
Handles user login, registration, and session management using bcrypt.
"""
from sqlalchemy.orm import Session
from core.models import User
import bcrypt

# Simple global state for currently logged-in user
CURRENT_USER_ID = None

def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.
    """
    # bcrypt requires bytes
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8') # Store as string

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a password against a hash.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """
    Attempts to log in a user.
    Returns the User object if successful, None otherwise.
    """
    global CURRENT_USER_ID
    user = db.query(User).filter(User.email == email).first()
    
    if user and verify_password(password, user.password_hash):
        CURRENT_USER_ID = user.id
        return user
    return None

def create_user(db: Session, name: str, email: str, password: str) -> User | None:
    """
    Registers a new user.
    Returns the new User object if successful, None if email exists.
    """
    if db.query(User).filter(User.email == email).first():
        return None # Email taken
    
    hashed = hash_password(password)
    new_user = User(name=name, email=email, password_hash=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def logout():
    """
    Logs out the current user.
    """
    global CURRENT_USER_ID
    CURRENT_USER_ID = None

def get_current_user(db: Session) -> User | None:
    """
    Returns the currently logged-in user.
    """
    if CURRENT_USER_ID is None:
        return None
    return db.query(User).filter(User.id == CURRENT_USER_ID).first()
