from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, MFASecret
from schemas import UserRegister, UserLogin, Token, UserResponse
from auth import get_password_hash, verify_password, create_access_token, create_refresh_token
from datetime import datetime, timezone

# Create router with prefix and tags
router = APIRouter(
    prefix="/api/auth",  # All routes start with /api/auth
    tags=["Authentication"]  # Groups endpoints in API docs
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Process:
    1. Check if username/email already exists
    2. Hash the password
    3. Create user in database
    4. Return user data (without password!)
    
    Args:
        user_data: Validated registration data from request body
        db: Database session (injected by Depends)
        
    Returns:
        UserResponse: Created user data
        
    Raises:
        HTTPException 400: Username or email already exists
    """
    
    # Check if username already taken
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already taken
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        mfa_enabled=False,  # MFA disabled by default
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Add to database
    db.add(new_user)
    db.commit()  # Save to database
    db.refresh(new_user)  # Reload to get generated ID
    
    return new_user


@router.post("/login", response_model=Token)
def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login and receive JWT tokens.
    
    Process:
    1. Find user by username
    2. Verify password
    3. Check if MFA is enabled (for now, skip MFA)
    4. Generate access and refresh tokens
    5. Return tokens
    
    Args:
        user_credentials: Username and password
        db: Database session (injected by Depends)
        
    Returns:
        Token: Access token, refresh token, and token type
        
    Raises:
        HTTPException 401: Invalid credentials
    """
    
    # Find user by username
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}  # Standard auth header
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # TODO: If MFA enabled, require MFA token verification
    # For now, we'll skip MFA and just issue tokens
    
    # Create token payload
    token_data = {
        "sub": str(user.id),  # Subject: user ID
        "username": user.username,
        "mfa_enabled": user.mfa_enabled
    }
    
    # Generate tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }