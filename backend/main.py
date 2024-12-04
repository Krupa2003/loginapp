from fastapi import FastAPI, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from backend import crud, models, schemas
from backend.database import SessionLocal, engine
from passlib.context import CryptContext
from backend.models import Base  # Ensure this import is here


# Create FastAPI app    
app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mount the static folder (for serving CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Templates for rendering HTML
templates = Jinja2Templates(directory="frontend/templates")

# Create the database tables
Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Login route
@app.post("/login")
async def login_user(
    username: str = Form(...), 
    password: str = Form(...), 
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    return await crud.login_user(username, password, email, db)

# Logout route
@app.get("/logout")
async def logout_user():
    # Logout by clearing the session cookie
    response = RedirectResponse(url="/")
    response.delete_cookie("username")
    return response

# Home route - Index Page
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    # Fetch users from the database
    users = db.query(models.User).all()
    return templates.TemplateResponse("index.html", {"request": request, "users": users, "username": request.cookies.get("username")})

# Register page route
@app.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Login page route
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Forgot Password page route
@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

# Password reset page route
@app.get("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

# Route to handle forgotten password (username form submission)
@app.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password(username: str = Form(...), db: Session = Depends(get_db), request: Request = None):
    db_user = db.query(models.User).filter(models.User.username == username).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # For now, let's just return a token (e.g., a simple "reset-link" for the demo)
    # In production, you would generate a real token and send it via email.
    token = "dummy_reset_token"  # You could generate a secure token here
    reset_link = f"/reset-password/{token}"  # The link the user will use to reset the password
    
    # Ensure that the 'request' object is passed properly in the context of templates
    return templates.TemplateResponse("forgot_password_success.html", {"request": request, "reset_link": reset_link})


# Route to handle password reset (submit new password)
@app.post("/reset-password/{token}")
async def reset_password(token: str, new_password: str = Form(...), confirm_password: str = Form(...), db: Session = Depends(get_db)):
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Find user by the token or simulate token processing (for simplicity, we skip actual token validation)
    db_user = db.query(models.User).filter(models.User.email == "user@example.com").first()  # Example: Find by email or token
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = pwd_context.hash(new_password)
    db_user.password = hashed_password
    db.commit()
    db.refresh(db_user)
    
    return {"message": "Password successfully reset"}

# Register route handling
@app.post("/register")
async def register_user(request: Request, db: Session = Depends(get_db)):
    # Get form data from the request
    form = await request.form()
    
    # Extract the necessary fields
    username = form.get("username")
    password = form.get("password")
    email = form.get("email")
    
    if not username or not password or not email:
        raise HTTPException(status_code=400, detail="Username, password, and email are required")
    
    # Hash the password securely
    hashed_password = pwd_context.hash(password)
    
    # Create the UserCreate schema with the form data
    user_create = schemas.UserCreate(username=username, password=hashed_password, email=email)
    
    # Check if the user already exists
    existing_user = crud.get_user_by_email(db, email=email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered")
    
    # Create the user in the database
    new_user = crud.create_user(db=db, user=user_create)
    
    # Return the newly created user (or some success message)
    return {"message": "User created successfully", "user": new_user}
@app.get("/users-data")
async def users_data(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return [{"id": user.id, "username": user.username} for user in users]
