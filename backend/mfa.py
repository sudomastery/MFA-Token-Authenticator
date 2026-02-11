import pyotp
#Python One-Time Password Librart
import qrcode
from io import BytesIO
import base64
#import binary data as text for sending QR in JSON
from cryptography.fernet import Fernet
#Fernete: symmertic encryption AES-256
#Encrypt TOP secrets before database storage
from config import get_settings
#get access to the encryption key

settings= get_settings()

#initialize Fernet cipher with encryption key
cipher = Fernet(settings.encryption_key.encode())

#getting the encryptio key, and enconding to utf-8 byes

def generate_totp_secret() -> str:
    """
    Generate a new TOTP secret key for MFA.
    
    Returns:
        Base32 encoded TOTP secret
    
    Base 32 makes it more human readable
    """
    return pyotp.random_base32()

def encrypt_secret(secret: str) -> str:
    """
    Encrypt TOTP secret for database storage.
    
    Why encrypt?
    - TOTP secrets are sensitive (like passwords)
    - If database leaks, attackers can't generate valid codes
    - Uses AES-256 with Fernet (authenticated encryption)
    
    Args:
        secret: Plain Base32 TOTP secret
        
    Returns:
        Encrypted secret (Base64-encoded)
    """
    secret_bytes = secret.encode('utf-8')
    encrypted = cipher.encrypt(secret_bytes)
    return encrypted.decode('utf-8')

def decrypt_secret(encrypted_secret: str) -> str:
    """
    Decrypt TOTP secret from database.
    
    Args:
        encrypted_secret: Encrypted secret from database
        
    Returns:
        Decrypted Base32 TOTP secret
    """
    encrypted_bytes = encrypted_secret.encode('utf-8') 
    decrypted = cipher.decrypt(encrypted_bytes)
    return decrypted.decode('utf-8')

def generate_qr_code(secret: str, username: str, issuer: str = "MFA POC") -> str:
    """
    Generate QR code for authenticator apps.
    
    QR Code Format (URI):
    otpauth://totp/ISSUER:USERNAME?secret=SECRET&issuer=ISSUER
    
    Example:
    otpauth://totp/MFA%20Auth:john_doe?secret=JBSWY3DPEHPK3PXP&issuer=MFA%20Auth
    
    Args:
        secret: Base32 TOTP secret
        username: User's username (shown in authenticator app)
        issuer: App name (default: "MFA Auth")
        
    Returns:
        Base64-encoded PNG image (data URL for frontend)
    """

    #Create TOTP object
    totp = pyotp.TOTP(secret)

    #Generate provisioning URI
    uri = totp.provisioning_uri(
        name=username,
        issuer_name=issuer
    )
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,  # Size (1 = 21x21 modules)
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Low error correction
        box_size=10,  # Pixels per module
        border=4,  # Border size (minimum is 4)
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    # Generate image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to Base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # Return as data URL (ready for <img> tag)
    return f"data:image/png;base64,{img_str}"

def verify_totp_token(secret: str, token: str, window: int = 1) -> bool:
    """
    Verify a TOTP token.
    
    How TOTP works:
    1. Current Unix time / 30 seconds = counter
    2. HMAC-SHA1(secret, counter) = hash
    3. Extract 6 digits from hash = token
    
    Window parameter:
    - Allows ±30 seconds clock drift
    - window=1: accepts tokens from -30s, now, +30s
    - Prevents issues with unsynchronized clocks
    
    Args:
        secret: Base32 TOTP secret
        token: 6-digit code from user
        window: Number of time steps to check (default: 1)
        
    Returns:
        True if token is valid, False otherwise
    """
    totp = pyotp.TOTP(secret)

    # verify() checks current time ± window
    # Returns True if token matches any valid time window
    return totp.verify(token, valid_window=window)

#This is just for testing purposes
def get_current_totp(secret: str) -> str:
    """
    Generate the current TOTP token (for testing)

    Args:
        secret: Base32 TOTP secret
        
    Returns:
        Current 6-digit TOTP token

    """
    totp = pyotp.TOTP(secret)
    return totp.now()

