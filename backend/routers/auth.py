from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User, MFASecret, BackupCode
from schemas import UserRegister, UserLogin, Token, UserResponse, MFASetupResponse, MFAVerify
from auth import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_access_token
from mfa import generate_totp_secret, encrypt_secret, decrypt_secret, generate_qr_code, verify_totp_token
from datetime import datetime, timezone
import secrets
import bcrypt
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
        # Check if user has incomplete MFA setup (registered but never completed MFA)
        if not existing_user.mfa_enabled:
            incomplete_secret = db.query(MFASecret).filter(
                MFASecret.user_id == existing_user.id,
                MFASecret.is_active == False
            ).first()
            if incomplete_secret:
                # User is in limbo state - has incomplete MFA setup
                # Allow them to try again by directing them to complete MFA
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already registered with incomplete MFA setup. Please login to complete MFA setup."
                )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already taken
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        # Check for incomplete MFA setup on email too
        if not existing_email.mfa_enabled:
            incomplete_secret = db.query(MFASecret).filter(
                MFASecret.user_id == existing_email.id,
                MFASecret.is_active == False
            ).first()
            if incomplete_secret:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered with incomplete MFA setup. Please login to complete MFA setup."
                )
        
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

        # Check if MFA is enabled
    if user.mfa_enabled:
        # MFA is enabled - token is required
        if not user_credentials.mfa_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA token required. Please provide mfa_token in request body.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user's MFA secret
        mfa_secret = db.query(MFASecret).filter(
            MFASecret.user_id == user.id,
            MFASecret.is_active == True
        ).first()
        
        if not mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MFA configuration error. Please contact support."
            )
        
        # Decrypt and verify MFA token
        decrypted_secret = decrypt_secret(mfa_secret.secret_key)
        if not verify_totp_token(decrypted_secret, user_credentials.mfa_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    # Create token payload
    token_data = {
        "sub": str(user.id),  # Subject: user ID
        "username": user.username,
        "mfa_enabled": user.mfa_enabled
    }
    
    # Generate tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    # Check if user has incomplete MFA setup (secret exists but not active)
    incomplete_mfa = False
    if not user.mfa_enabled:
        incomplete_secret = db.query(MFASecret).filter(
            MFASecret.user_id == user.id,
            MFASecret.is_active == False
        ).first()
        if incomplete_secret:
            incomplete_mfa = True
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "mfa_enabled": user.mfa_enabled,
            "incomplete_mfa": incomplete_mfa
        }
    }

# ======================MFA Endpoints ============

def get_current_user(
        authorization: Optional[str] = Header(None),
        db: Session = Depends(get_db)     
                     
    ) -> User:
    """
    FastApi Dependency: Extract and validate user from Authorization header

    Used by protected MFA endpoints to identify the user.

    How Authorization headers work:
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
                   ↑      ↑
                  scheme  token
    
    Process:
    1. Check Authorization header exists
    2. Verify format is "Bearer <token>"
    3. Extract token part
    4. Decode and validate JWT
    5. Find user in database
    6. Return user object
    
    Args:
        authorization: Authorization header (auto-extracted by FastAPI)
        db: Database session (injected)
        
    Returns:
        User object if valid token
        
    Raises:
        HTTPException 401: Missing, invalid, or expired token
        HTTPException 404: User not found
    """ 

    # Check if authorization header was provided
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing", 
            headers={"WWW-Authenticate": "Bearer"}

        )
    
    #split "bearer token" into parts
    parts = authorization.split()

    #Validate format: exactly 2 parts, first is 'Bearer'
    if len(parts) !=2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )
    #Extract token (second part)
    token = parts[1]

    #Decode JWT token
    payload = decode_access_token(token)
    if not payload:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    #Extract user ID from token payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid token payload: missing user ID", 
            headers={"WWW-Authenticate": "Bearer"}
        )
    #Find user in database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Setup MFA for authenticated user.
    
    Process:
    1. User must be logged in (JWT validated by get_current_user dependency)
    2. Generate random TOTP secret (Base32 encoded)
    3. Encrypt secret before storing in database
    4. Create QR code for authenticator apps
    5. Generate 8 backup codes for emergency access
    6. Store encrypted secret in database (not active yet)
    7. Return secret, QR code, and backup codes
    
    Note: MFA is NOT active until user verifies with POST /mfa/verify
    This prevents users from locking themselves out if they make mistakes.
    
    Headers Required:
        Authorization: Bearer <access_token>
        
    Returns:
        MFASetupResponse: {
            secret: "JBSWY3DPEHPK3PXP",  # Base32 TOTP secret
            qr_code: "data:image/png;base64,...",  # QR code image
            backup_codes: ["A1B2C3D4", ...]  # 8 emergency codes
        }

    """
    # Step 1: Generate TOTP secret
    totp_secret = generate_totp_secret()

    #Step 2: Encrypt for database storage
    encrypted_secret = encrypt_secret(totp_secret)

    #step 3: Generate the QR code
    # Format: otpauth://totp/MFA%20Auth:username?secret=XXX&issuer=MFA%20Auth
    qr_code = generate_qr_code(totp_secret, current_user.username)

    #Step 4: Generate backup codes
    # secrets.token_hex(4) = 8 random hex characters
    # Use .upper() to make them easier to read 
    backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]

    #step 5: Check is user already has MFA secret
    existing_mfa = db.query(MFASecret).filter(
        MFASecret.user_id == current_user.id
    ).first()

    if existing_mfa:
        #User is resetting MFA for example device is lost
        # Update existing record
        existing_mfa.secret_key = encrypted_secret
        existing_mfa.is_active = False  # Not active until verified
        existing_mfa.verified_at = None  # Clear previous verification
        existing_mfa.created_at = datetime.now(timezone.utc)  # New timestamp
        
        # Delete old backup codes
        db.query(BackupCode).filter(BackupCode.user_id == current_user.id).delete()
    else:
        #First time MFA Setup - create new record
        new_mfa = MFASecret(
            user_id=current_user.id,
            secret_key=encrypted_secret,
            is_active=False,  # Not active until verified
            verified_at=None,
            created_at=datetime.now(timezone.utc)

        )
        db.add(new_mfa)
    
    # Store hashed backup codes in database
    for code in backup_codes:
        # Hash backup code like a password
        code_hash = bcrypt.hashpw(code.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
        backup_code_record = BackupCode(
            user_id=current_user.id,
            code_hash=code_hash,
            used=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(backup_code_record)
    
    # Save to database
    db.commit()

    # Return setup data
    # This is the only time backup codes are shown unencrypted
    # User must save them now

    return {
        "secret": totp_secret,  # Show once! User should save this
        "qr_code": qr_code,     # Base64 image for scanning
        "backup_codes": backup_codes  # Emergency codes - save these!
    }




@router.post("/mfa/verify")
def verify_mfa(
    mfa_data: MFAVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify and activate MFA.
    
    This is the critical step that actually enables MFA. User must prove
    they successfully set up their authenticator app by providing a valid code.
    
    Process:
    1. Get user's pending MFA secret from database
    2. Decrypt the secret (it's stored encrypted)
    3. Verify the 6-digit token from authenticator app
    4. If valid, mark MFA as verified and active
    5. Update user.mfa_enabled = True
    
    Why this two-step process (setup → verify)?
    - Prevents users from locking themselves out
    - Confirms they saved the secret or scanned QR correctly
    - Best practice for MFA implementation
    
    Headers Required:
        Authorization: Bearer <access_token>
        
    Request Body:
        {"token": "123456"}  # 6-digit code from authenticator app
        
    Returns:
        {"message": "MFA enabled successfully", "mfa_enabled": true}
        
    Raises:
        HTTPException 400: No MFA setup found (must call /mfa/setup first)
        HTTPException 401: Invalid token (wrong code or expired)
    """
    # Debug logging
    print(f"DEBUG: Received MFA verify request for user {current_user.username}")
    print(f"DEBUG: Token received: '{mfa_data.token}' (type: {type(mfa_data.token)}, length: {len(mfa_data.token)})")
    
    # Ensure token is string and clean
    token = str(mfa_data.token).strip()
    print(f"DEBUG: Cleaned token: '{token}' (length: {len(token)})")
    
    # Validate token format
    if len(token) != 6 or not token.isdigit():
        print(f"DEBUG: Token validation failed - not 6 digits")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA token must be exactly 6 digits"
        )
    
    mfa_secret = db.query(MFASecret).filter(
        MFASecret.user_id == current_user.id
    ).first()
    
    if not mfa_secret:
        print(f"DEBUG: No MFA secret found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not set up. Please call POST /api/auth/mfa/setup first"
        )

    print(f"DEBUG: Found MFA secret, is_active={mfa_secret.is_active}")
    
    # Step 2: Decrypt the secret
    try:
        decrypted_secret = decrypt_secret(mfa_secret.secret_key)
        print(f"DEBUG: Successfully decrypted secret")
    except Exception as e:
        print(f"DEBUG: Failed to decrypt secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt MFA secret"
        )
    
    # Step 3: Verify the token
    print(f"DEBUG: Verifying TOTP token...")
    if not verify_totp_token(decrypted_secret, token):
        print(f"DEBUG: TOTP verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA token. Please check your authenticator app and try again."
        )
    
    print(f"DEBUG: TOTP verification successful!")
    
    # Step 4: Activate MFA
    # Mark secret as active and verified
    mfa_secret.is_active = True
    mfa_secret.verified_at = datetime.now(timezone.utc)

    # Enable MFA for user account
    current_user.mfa_enabled = True
    current_user.updated_at = datetime.now(timezone.utc)

    # Save changes
    try:
        db.commit()
        print(f"DEBUG: Successfully committed MFA activation for user {current_user.username}")
    except Exception as e:
        print(f"DEBUG: Failed to commit: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save MFA activation"
        )

    # Success response
    return {
        "message": "MFA enabled successfully",
        "mfa_enabled": True
    }


@router.post("/mfa/disable")
def disable_mfa(
    mfa_data: MFAVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disable MFA for authenticated user.
    
    Security-critical endpoint: Requires valid MFA token to disable.
    This prevents attackers who steal JWT tokens from disabling MFA.
    
    Process:
    1. Verify user has MFA enabled
    2. Get MFA secret from database
    3. Verify current MFA token (prove they have authenticator access)
    4. Delete MFA secret from database
    5. Set user.mfa_enabled = False
    
    Why require MFA token to disable?
    - Prevents unauthorized disabling if JWT is stolen
    - User must have physical access to authenticator
    - Defense-in-depth security principle
    
    Headers Required:
        Authorization: Bearer <access_token>
        
    Request Body:
        {"token": "123456"}  # Current valid token required
        
    Returns:
        {"message": "MFA disabled successfully", "mfa_enabled": false}
        
    Raises:
        HTTPException 400: MFA not enabled for this account
        HTTPException 401: Invalid token (wrong code)
    """
    # Step 1: Check if MFA is enabled
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account"
        )
    
    # Step 2: Get user's MFA secret
    mfa_secret = db.query(MFASecret).filter(
        MFASecret.user_id == current_user.id
    ).first()
    
    if not mfa_secret:
        # Edge case: user.mfa_enabled is True but no secret exists
        # This shouldn't happen, but handle gracefully
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA secret not found"
        )
    
    # Step 3: Decrypt and verify token
    # User must prove they have access to authenticator
    decrypted_secret = decrypt_secret(mfa_secret.secret_key)
    
    if not verify_totp_token(decrypted_secret, mfa_data.token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA token. Cannot disable MFA without valid token."
        )
    
    # Step 4: Disable MFA
    # Delete the secret from database
    db.delete(mfa_secret)
    
    # Update user record
    current_user.mfa_enabled = False
    current_user.updated_at = datetime.now(timezone.utc)
    
    # Save changes
    db.commit()
    
    # Success response
    return {
        "message": "MFA disabled successfully",
        "mfa_enabled": False
    }

@router.post("/mfa/verify-backup")
def verify_backup_code(
    backup_code: str,
    username: str,
    db: Session = Depends(get_db)
):
    """
    Verify backup code for MFA recovery.
    
    Used when user loses access to authenticator app.
    Each backup code can only be used once.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    backup_codes = db.query(BackupCode).filter(
        BackupCode.user_id == user.id,
        BackupCode.used == False
    ).all()
    
    if not backup_codes:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid backup codes available"
        )
    
    code_matched = False
    matched_code = None
    
    for stored_code in backup_codes:
        if bcrypt.checkpw(backup_code.encode('utf-8'), stored_code.code_hash.encode('utf-8')):
            code_matched = True
            matched_code = stored_code
            break
    
    if not code_matched:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid backup code")
    
    matched_code.used = True
    matched_code.used_at = datetime.now(timezone.utc)
    db.commit()
    
    temp_token = create_access_token(user_id=user.id, username=user.username, mfa_enabled=user.mfa_enabled, expires_minutes=10)
    
    return {
        "message": "Backup code verified successfully",
        "temp_token": temp_token,
        "user": {"username": user.username, "email": user.email}
    }


@router.post("/mfa/reset")
def reset_mfa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Reset MFA after backup code verification."""
    mfa_secret = db.query(MFASecret).filter(MFASecret.user_id == current_user.id).first()
    if mfa_secret:
        db.delete(mfa_secret)
    
    db.query(BackupCode).filter(BackupCode.user_id == current_user.id).delete()
    current_user.mfa_enabled = False
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"message": "MFA reset successfully. Please set up MFA again.", "mfa_enabled": False}
