from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User, MFASecret
from schemas import UserRegister, UserLogin, Token, UserResponse, MFASetupResponse, MFAVerify
from auth import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_access_token
from mfa import generate_totp_secret, encrypt_secret, decrypt_secret, generate_qr_code, verify_totp_token
from datetime import datetime, timezone
import secrets
from typing import Optional

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

# ======================MFA Endpoints ============

def get_current_user(
        authorization: Optional[str] = Header(None),
        db: Session = Depends(get_db)     
                     
    ) -> User:
    """
    Helper function: Extract user from JWT token.

    Used by protected MFA endpoints to identify the user.

    YOU NEED TO CONTINUE BUILDING THIS FUNCTION
    """ 
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid or expired token"
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(
    authorization: str = Depends(lambda: None),  # extract manually for learning
    db: Session = Depends(get_db)
):
    """
    setup mfa for authenticated user

    Process:
    1. Verify the user is logged in (check JWT token)
    2. Generate random TOPP secret
    3. Create QR code for authenticator app
    4. Store encrypted secret in database (not verified yet)
    5. Return QR code and secret to user

    MFA is not active until user verifies with /mfa/verify

    Headers Required:
    Authorization: Bearer <access_token>
        
    Returns:
        MFASetupResponse: QR code, secret, backup codes
    """
    #implement a simpler version in production implement FASTAPI's OAuth2PasswordBearer

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="MFA setup endpoint not yet implemented"
    )

@router.post("/mfa/verify")
def verify_mfa(
    mfa_data: MFAVerify,
    authorization: str = Depends(lambda: None),
    db: Session = Depends(get_db)
):
    """
    Verify and activate MFA

    Process:
    1. get user;s pending MFA secret from the database
    2. Verify the 6 digits token from authenticator app
    2. if valid mark MFA as verfied and active
    4. Update user.mfa_enabled = True

    Headers Required:
        Authorization: Bearer <access_token>
        
    Request Body:
        {"token": "123456"}
        
    Returns:
        Success message
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="MFA verify endpoint - implementation next"
    )

@router.post("/mfa/disable")
def disable_mfa(
    mfa_data: MFAVerify,
    authorization: str = Depends(lambda: None),
    db: Session = Depends(get_db)
):
    """
   Disable MFA for authenticated user

   Process:
   1. Verify user's current MFA token (prove they have access)
   2. Delete MFA secret from database
   3. Set user.mfa_enabled = False

   Headers Required:
        Authorization: Bearer <access_token>
        
    Request Body:
        {"token": "123456"}  # Current valid token required
        
    Returns:
        Success message
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="MFA disable endpoint - implementation next"
    )
