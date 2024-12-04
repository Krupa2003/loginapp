from sqlalchemy.orm import Session
from backend import models, schemas
from passlib.context import CryptContext
from fastapi import HTTPException

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

# Function to get a user by email
def get_user_by_email(db: Session, email: str):
    """Retrieve a user by their email."""
    return db.query(models.User).filter(models.User.email == email).first()

# Function to get a user by username
def get_user_by_username(db: Session, username: str):
    """Retrieve a user by their username."""
    return db.query(models.User).filter(models.User.username == username).first()

# Create a new user
def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user in the database."""
    db_user = models.User(username=user.username, password=user.password, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Register a new user
async def register_user(user: schemas.UserCreate, db: Session):
    """Register a new user."""
    # Check if the username or email is already taken
    db_user = get_user_by_username(db, user.username)
    db_email = get_user_by_email(db, user.email)

    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password before storing it
    hashed_password = hash_password(user.password)
    
    # Create the new user object and save to DB
    db_user = models.User(username=user.username, password=hashed_password, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# Login functionality
async def login_user(username: str, password: str, email: str, db: Session):
    """Login an existing user by username or email."""
    # Query the database for a user matching the username or email
    db_user = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == email)
    ).first()

    if not db_user or not verify_password(password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {"username": db_user.username, "email": db_user.email, "message": "Login successful"}
