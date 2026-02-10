"""
Pydantic are like email contracts:
Input validation: Reject invalid data before it reaches your database
Output serialization: Format data consistently in responses
Documentation: FastAPI auto-generates API docs from these schemas
Type safety: Catch bugs at development time
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


# ============= User Registration =============

class UserRegister(BaseModel):
    """
    Schema for user registration requests.
    
    Validates:
    - Username: 3-30 characters, alphanumeric + underscores
    - Email: Valid email format
    - Password: Minimum 8 characters (will add strength check)
    """
    username: str = Field(
        ...,  # Required field (ellipsis means no default)
        min_length=3,
        max_length=30,
        pattern="^[a-zA-Z0-9_]+$",  # Alphanumeric and underscores only
        examples=["john_doe"]
    )
    email: EmailStr = Field(
        ...,
        examples=["john@example.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        examples=["SecurePass123!"]
    )
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength.
        
        Requirements:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        
        Args:
            v: Password value
            
        Returns:
            Password if valid
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


# ============= User Login =============

class UserLogin(BaseModel):
    """
    Schema for user login requests.
    
    Can login with either username or email + password.

    # If MFA is enabled, also requires mfa_token
    """
    username: str = Field(
        ...,
        examples=["john_doe"]
    )
    password: str = Field(
        ...,
        examples=["SecurePass123!"]
    )

    mfa_token: Optional[str] = Field(
        None,
        min_length=6,
        max_length=6,
        pattern="^[0-9]{6}$",
        description="6-digit MFA token (required if MFA is enabled)",
        examples=["123456"]
    )


# ============= Token Responses =============

class Token(BaseModel):
    """
    Schema for JWT token responses.
    
    Returned after successful login.
    """
    access_token: str = Field(
        ...,
        description="JWT access token (30 min expiration)"
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token (7 day expiration)"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer' for JWT)"
    )


class TokenRefresh(BaseModel):
    """
    Schema for token refresh requests.
    """
    refresh_token: str = Field(
        ...,
        description="The refresh token from login"
    )


# ============= User Responses =============

class UserResponse(BaseModel):
    """
    Schema for user data in responses.
    
    Note: Never include password_hash in responses!
    """
    id: int
    username: str
    email: str
    mfa_enabled: bool
    created_at: datetime
    
    class Config:
        """
        Pydantic configuration.
        
        from_attributes=True: Allows creating schema from ORM models
        Previously called: orm_mode=True (Pydantic v1)
        """
        from_attributes = True


# ============= MFA Setup =============

class MFASetupResponse(BaseModel):
    """
    Schema for MFA setup responses.
    
    Contains QR code and backup codes.
    """
    secret: str = Field(
        ...,
        description="Base32-encoded TOTP secret (show once, user should save)"
    )
    qr_code: str = Field(
        ...,
        description="Base64-encoded QR code image (data URL)"
    )
    backup_codes: list[str] = Field(
        ...,
        description="One-time backup codes (8 codes, show once)"
    )


class MFAVerify(BaseModel):
    """
    Schema for MFA verification requests.
    
    Used during login and initial MFA setup.
    """
    token: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern="^[0-9]{6}$",  # Exactly 6 digits
        examples=["123456"]
    )


class MFAStatus(BaseModel):
    """
    Schema for checking MFA status.
    """
    mfa_enabled: bool
    mfa_verified: bool


# ============= Generic Responses =============

class MessageResponse(BaseModel):
    """
    Schema for simple message responses.
    
    Used for success/error messages.
    """
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """
    Schema for error responses.
    
    Follows FastAPI's HTTPException format.
    """
    detail: str


"""
NOTES

# User sends:
{
    "username": "john_doe",
    "email": "john@example.com", 
    "password": "weakpass"
}

# Pydantic process:
# 1. Check username: length OK? pattern OK? ✓
# 2. Check email: valid email format? ✓
# 3. Check password: length OK? ✓
# 4. Run @field_validator for password:
#    - validate_password_strength(UserRegister, "weakpass")
#    - No uppercase? Raise ValueError ✗
# 5. Return error to user: "Password must contain uppercase"

"""