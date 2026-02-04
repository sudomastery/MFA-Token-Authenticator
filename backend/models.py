from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class User(Base):
    """
    Create the User's table
    Stores user authentication credentials and basic info
    One user can have one MFA secret (one-to-one relationship)

    """

    __tablename__ = "users"

    #Primary key - unique indentifier for each user
    id = Column(Integer, primary_key=True, index=True)

    #Unique username not null
    username = Column(String(30), unique=True, nullable=False, index=True)

    email = Column(String(30), unique=True, nullable=False, index=True)

    password_hash = Column(String(255), nullable=False)

    #Is MFA enabled for the user
    mfa_enabled = Column(Boolean, default=False, nullable=False)

    #Timestamps track when user was created/updates


    #created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


    # Relationship - links to MFASecret table
    # user.mfa_secret gives you the MFA secret for this user
    # back_populates creates bidirectional relationship
    # cascade="all, delete-orphan" - delete MFA secret when user is deleted

    mfa_secret = relationship("MFASecret", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        """
        String representation of the User Object for debugging
        """
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

class MFASecret(Base):
    """
    This model stores TOTP secrets
    One to one relationship with User
    """
    __tablename__ = "mfa_secrets"

    #Primary Key
    id = Column(Integer, primary_key=True, index=True)

    #Foreign key - links to users table
    #user_id must match a valid user.id
    #unique=True enforces one to one (one user = one secret)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    secret_key = Column(String(255), nullable=False)

    #Is MFA active and verfie # Is MFA active and verified?
    # False during setup, True after first successful verification
    is_active = Column(Boolean, default=False, nullable=False)
    
    # When was MFA verified/activated?
    verified_at = Column(DateTime, nullable=True)
    
    # When was this secret created?
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationship - links back to User table
    # mfa_secret.user gives you the User object
    user = relationship("User", back_populates="mfa_secret")
    
    def __repr__(self):
        """String representation of MFASecret object (for debugging)"""
        return f"<MFASecret(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
