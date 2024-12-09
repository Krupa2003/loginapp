from fastapi import FastAPI, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter
from backend import crud, models, schemas
from backend.database import SessionLocal, engine
from passlib.context import CryptContext
from backend.models import Base  # Ensure this import is here

# Initialize FastAPI app
app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Templates
templates = Jinja2Templates(directory="frontend/templates")

# Create database tables
Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Prometheus metrics
user_login_counter = Counter(
    "user_logins_total", "Total number of user logins"
)
user_registration_counter = Counter(
    "user_registrations_total", "Total number of user registrations"
)
user_data_access_counter = Counter(
    "user_data_access_total", "Total number of user data retrievals"
)

# Instrumentator for FastAPI with custom metrics
instrumentator = Instrumentator()

# Add custom metrics to the instrumentator correctly
instrumentator.add(lambda info: user_login_counter)
instrumentator.add(lambda info: user_registration_counter)
instrumentator.add(lambda info: user_data_access_counter)

# Instrument FastAPI app and expose metrics
instrumentator.instrument(app).expose(app, endpoint="/metrics")

# Login route
@app.post("/login")
async def login_user(
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    user = await crud.login_user(username, password, email, db)
    
    if user:
        # Increment login count for the total logins (without username label)
        user_login_counter.inc()  # Increment total login count
    
    return {"message": "Login successful" if user else "Invalid credentials"}

# Logout route
@app.get("/logout")
async def logout_user():
    response = RedirectResponse(url="/")
    response.delete_cookie("username")
    return response

# Home route - Index Page
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "users": users, "username": request.cookies.get("username")}
    )

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
    token = "dummy_reset_token"
    reset_link = f"/reset-password/{token}"
    return templates.TemplateResponse("forgot_password_success.html", {"request": request, "reset_link": reset_link})

# Route to handle password reset
@app.post("/reset-password/{token}")
async def reset_password(token: str, new_password: str = Form(...), confirm_password: str = Form(...), db: Session = Depends(get_db)):
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    db_user = db.query(models.User).filter(models.User.email == "user@example.com").first()
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
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    email = form.get("email")
    if not username or not password or not email:
        raise HTTPException(status_code=400, detail="Username, password, and email are required")
    hashed_password = pwd_context.hash(password)
    user_create = schemas.UserCreate(username=username, password=hashed_password, email=email)
    existing_user = crud.get_user_by_email(db, email=email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered")
    new_user = crud.create_user(db=db, user=user_create)
    user_registration_counter.inc()  # Increment registration counter
    return {"message": "User created successfully", "user": new_user}

# User data retrieval route
@app.get("/users-data")
async def users_data(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    user_data_access_counter.inc()  # Increment user data access counter
    return [{"id": user.id, "username": user.username} for user in users]
