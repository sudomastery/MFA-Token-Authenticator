import bcrypt
# bcrypt: Modern password hashing library (replaces passlib)
# Uses Blowfish cipher with adaptive cost factor

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from typing import Optional, Dict, Any
from config import get_settings

settings = get_settings()


def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    
    How bcrypt works:
    1. Generates a random salt (unique per password)
    2. Combines password + salt
    3. Runs through bcrypt algorithm 2^12 times (cost factor = 12)
    4. Returns: $2b$12$[salt][hash]
    
    Args:
        password: Plain-text password from user
        
    Returns:
        Hashed password string (safe to store in database)
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt with cost factor 12 (2^12 = 4096 iterations)
    #Playing with bycrypt og value was 12
    salt = bcrypt.gensalt(rounds=12)
    
    # Hash the password
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string for database storage
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Process:
    1. Extracts salt from stored hash
    2. Hashes the plain_password with same salt
    3. Uses constant-time comparison (prevents timing attacks)
    
    Args:
        plain_password: Password user entered during login
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    # Convert both to bytes
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    # Verify using bcrypt's checkpw (constant-time comparison)
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    JWT Structure: header.payload.signature
    - Header: {"alg": "HS256", "typ": "JWT"}
    - Payload: Your data + expiration time
    - Signature: HMAC-SHA256(header + payload, SECRET_KEY)
    
    Args:
        data: Dictionary of claims to encode (e.g., {"sub": "user_id"})
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    #set the expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        #Default: 30 minutes
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    #add standard JWT claims
    to_encode.update({
        "exp": expire, #expiration time
        "iat": datetime.now(timezone.utc)
    })

    #encode and sign the token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,  #secret key for singing
        algorithm=settings.jwt_algorithm #hs256

    )
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token

    Validation checks:
    1. signature is valid (token was not tampered with)
    2. Token hasnt expired
    3. Token structure is correct

    
 
    """
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        #Token is invalid, expired or tamprered with
        return None

def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a longer lived refresh token

    Refresh tokens:
    - used to get new access tokens wuthout re-login
    - longer expiratiion 7 days compared vs 30 minutes
    - should be stored securely (httpOnly cookies)
    """
    return create_access_token(data, expires_delta=timedelta(days=7))