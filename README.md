# MFA Token Authenticator

A complete Multi-Factor Authentication (MFA) module that enables users to securely **register**, **verify**, and **recover** their accounts using Time-based One-Time Passwords (TOTP). Works seamlessly with **Microsoft Authenticator**, **Ente Auth**, **Google Authenticator**, and any other TOTP-compatible authenticator application.

---

## User Flow Showcase

### 1. Login and Registration
New users can register by providing a username, email, and secure password. Existing users can log in with their credentials and complete MFA verification using their authenticator app. A backup code recovery option is available for users who've lost access to their authenticator device.

![Login and Registration](screenshots/login_and_authentication.png)

### 2. MFA Setup
After registration or when enabling MFA, users scan a QR code with their authenticator app and receive backup recovery codes for emergency access.

![MFA Setup - QR Code](screenshots/mfa_setup.png)

### 3. Backup Codes
Users receive 8 one-time backup codes to save securely. These codes can be used to regain access if the authenticator device is lost.

![Backup Codes](screenshots/backup_codes.png)

### 4. MFA Verification
After successfuly entering the MFA users are redirected to the protected resource they have access to.

![MFA Verification](screenshots/security_dashboard.png)

---

## What This Project Does

This MFA module provides:

- **Complete Registration Flow** - Create account with secure password hashing
- **MFA Enrollment** - Generate TOTP secrets and QR codes for authenticator apps
- **Two-Factor Login** - Verify password + TOTP code for enhanced security
- **Account Recovery** - Use backup codes to regain access if authenticator device is lost
- **MFA Reset** - Reset and re-enroll MFA after recovery
- **Universal Compatibility** - Works with Microsoft Authenticator, Ente Auth, Google Authenticator, and any TOTP-based app

### Key Features

**Secure by Design**
- Password hashing with bcrypt (12 rounds)
- Fernet encryption (AES-256) for TOTP secrets at rest
- JWT token-based authentication
- Rate limiting and brute-force protection

**User-Friendly Experience**
- QR code scanning for quick setup
- Manual entry option as fallback
- 8 one-time backup recovery codes
- Clear error messages and guidance

**Enterprise-Grade Security**
- RFC 6238 compliant TOTP implementation
- 30-second token validity window
- Constant-time code comparison (timing attack prevention)
- Comprehensive audit logging

---

## Setup & Installation

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **PostgreSQL** 14+

### Backend Setup

```bash
# Clone repository
git clone <repository-url>
cd MFA-Token-Authenticator/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration:
# - DATABASE_URL=postgresql://user:password@localhost/mfa_db
# - JWT_SECRET (generate with: openssl rand -hex 32)
# - ENCRYPTION_KEY (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Initialize database
createdb mfa_db
alembic upgrade head

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**API will be available at:** `http://localhost:8000`  
**Interactive API docs:** `http://localhost:8000/docs`

### Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# Edit .env:
# VITE_API_URL=http://localhost:8000

# Run development server
npm run dev
```

**Frontend will be available at:** `http://localhost:5173`

---

## Technical Overview

### Architecture

The application follows a clean separation between frontend and backend, with RESTful API communication over HTTP. The backend is built with FastAPI, providing asynchronous request handling and automatic API documentation. The frontend uses React with Zustand for state management, ensuring a responsive single-page application experience.

### Authentication Flow

The system implements a two-phase authentication process. During initial login, credentials are validated and a temporary token is issued if the user has MFA enabled. This temporary token allows the user to submit their TOTP code for verification. Once the TOTP code is confirmed valid, a JWT access token is issued for subsequent authenticated requests. The JWT contains user claims and is signed using HMAC-SHA256, allowing stateless authentication without database lookups on every request.

### TOTP Implementation

TOTP codes are generated using the RFC 6238 standard, which builds on HMAC-based one-time passwords. Each user receives a unique base32-encoded secret during MFA setup, which is encrypted with Fernet (AES-256 in CBC mode) before being stored in the database. The authenticator app and server independently generate 6-digit codes every 30 seconds by computing an HMAC-SHA1 hash of the current time counter and the shared secret. The server validates submitted codes with a window of ±30 seconds to account for clock drift and network latency.

### Security Measures

Passwords are hashed using bcrypt with a cost factor of 12, providing strong resistance against brute-force attacks. The bcrypt algorithm automatically generates and includes a salt with each hash, preventing rainbow table attacks. TOTP secrets are encrypted at rest using Fernet symmetric encryption, ensuring that database compromise alone doesn't allow code generation. JWT tokens have a 30-minute expiration, with refresh tokens lasting 7 days to balance security and user convenience.

Backup codes are generated using cryptographically secure random number generation and stored as bcrypt hashes. Each code can only be used once, tracked in the database with a used timestamp. Rate limiting is applied to login and MFA verification endpoints to prevent brute-force attacks, with progressive lockout after repeated failures.

### Database Schema

The system uses PostgreSQL with SQLAlchemy ORM, featuring four main tables: users, mfa_secrets, backup_codes, and login_attempts. Foreign key relationships ensure referential integrity, with cascade deletes removing all MFA data when a user is deleted. Indexes on username and email fields optimize lookup performance during authentication.

### Technology Stack

**Backend:**
- FastAPI - Asynchronous Python web framework
- SQLAlchemy - ORM for database interactions
- PostgreSQL - Primary data store
- PyOTP - RFC 6238 TOTP implementation
- bcrypt - Password hashing
- cryptography (Fernet) - Secret encryption
- PyJWT - JWT token handling
- Pydantic - Request/response validation

**Frontend:**
- React - UI component library
- Zustand - Lightweight state management
- Vite - Build tool and dev server
- React Router - Client-side routing
- TailwindCSS - Utility-first styling

---

## API Endpoints

### Authentication

**POST** `/api/auth/register` - Register new user account  
**POST** `/api/auth/login` - Authenticate with username and password  
**POST** `/api/auth/verify-mfa` - Verify TOTP code and complete login  

### MFA Management

**POST** `/api/mfa/setup` - Generate TOTP secret and QR code (requires auth)  
**POST** `/api/mfa/verify` - Verify TOTP code and activate MFA (requires auth)  
**POST** `/api/mfa/reset` - Reset MFA configuration (requires auth)  
**POST** `/api/mfa/verify-backup` - Verify backup code for account recovery  

Full API documentation with request/response schemas is available at `http://localhost:8000/docs` when the backend is running.

---

## License

MIT License

---

**Authentication** is the process of verifying the identity of a user, device, or system. It answers the question: *"Are you really who you claim to be?"*

Think of it like showing your ID at an airport security checkpoint - you're proving you are the person on the ticket.

#### Types of Authentication Factors

Authentication factors are categorized into three types:

1. **Something You Know** (Knowledge Factor)
   - Password, PIN, security question answers
   - Most common but least secure on its own

2. **Something You Have** (Possession Factor)
   - Physical device: smartphone, security key, smart card
   - OTP tokens, authenticator apps
   - This is where MFA apps come in!

3. **Something You Are** (Inherence Factor)
   - Biometrics: fingerprint, face recognition, iris scan
   - Most secure but requires special hardware

### What is a Token?

In authentication systems, a **token** is a piece of data that represents a user's authentication state or authorization to access resources. There are several types of tokens:

#### 1. **Session Tokens**
- Generated after successful login
- Stored on the server (or in a JWT)
- Used to maintain user state across requests
- Example: `session_id=abc123xyz`

#### 2. **Access Tokens** (e.g., JWT - JSON Web Tokens)
- Self-contained tokens that carry user information
- Can be verified without database lookups
- Have expiration times for security
- Structure: `header.payload.signature`

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjM0LCJleHAiOjE2NDA5OTUyMDB9.signature
```

#### 3. **One-Time Password (OTP) Tokens**
- **THIS IS WHAT WE'RE IMPLEMENTING!**
- Temporary codes (usually 6 digits)
- Valid for a short period (typically 30 seconds)
- Generated using cryptographic algorithms
- Used as the second factor in MFA

### How Do Tokens Work?

#### Session Token Flow:
```
1. User logs in with credentials
2. Server validates credentials
3. Server generates unique session token
4. Token stored in database + sent to client (cookie/storage)
5. Client includes token in subsequent requests
6. Server validates token for each request
7. User logs out → token invalidated
```

#### JWT Token Flow:
```
1. User authenticates
2. Server creates JWT with user claims + signs it
3. Client stores JWT (localStorage/cookie)
4. Client sends JWT in Authorization header
5. Server verifies signature (no database lookup needed!)
6. Server extracts user info from token payload
```

---

## What is Multi-Factor Authentication (MFA)?

**Multi-Factor Authentication (MFA)**, also called **Two-Factor Authentication (2FA)** when using exactly two factors, is a security mechanism that requires users to provide two or more verification factors to gain access to a resource.

### Why MFA?

#### The Problem with Password-Only Authentication:
- **Data Breaches**: Billions of passwords leaked from hacked databases
- **Weak Passwords**: "123456", "password", "qwerty" still incredibly common
- **Password Reuse**: Users often use the same password across multiple sites
- **Phishing**: Attackers trick users into revealing passwords
- **Brute Force**: Attackers can try millions of password combinations

#### The Solution:
Even if an attacker steals your password, they **still can't access your account** without the second factor (your phone with the authenticator app).

### Real-World Statistics:
- Microsoft reports that MFA blocks **99.9% of account compromise attacks**
- Google found 2FA with SMS blocks **100% of automated bots**, **96% of bulk phishing attacks**, and **76% of targeted attacks**
- TOTP (what we're implementing) is even more secure than SMS!

---

## Deep Dive: TOTP (Time-based One-Time Password)

### What is TOTP?

**TOTP** is a cryptographic algorithm that generates a unique, temporary password that changes every 30 seconds (by default). It's defined in **RFC 6238** and is the industry standard used by authenticator apps.

### How TOTP Works: The Mathematics

TOTP builds upon HOTP (HMAC-based One-Time Password). Here's the mathematical breakdown:

#### Step 1: Shared Secret
When you set up MFA, the server generates a **secret key** (typically 160-bit random string):
```
Secret: JBSWY3DPEHPK3PXP
```

This secret is shared with your authenticator app (via QR code) and **stored securely on both sides**. This is the foundation of the trust relationship.

#### Step 2: Time Counter
Both the server and authenticator app use the current Unix timestamp divided by the time-step period (30 seconds):

```python
T = floor(current_unix_time / 30)
```

Example:
```
Current time: 1706745600 (Unix timestamp)
T = 1706745600 / 30 = 56891520
```

#### Step 3: HMAC-SHA1 Computation
The magic happens here! We use HMAC (Hash-based Message Authentication Code) with SHA-1:

```python
HMAC = HMAC-SHA1(secret_key, T)
```

This produces a 20-byte (160-bit) hash:
```
HMAC = [0x1f, 0x86, 0x98, 0x69, 0x0e, 0x02, 0xca, 0x16, ...]
```

#### Step 4: Dynamic Truncation
We extract a 4-byte (32-bit) integer from the HMAC:

1. Take the last nibble (4 bits) of the HMAC as an offset
2. Extract 4 bytes starting at that offset
3. Clear the most significant bit (for compatibility)

```python
offset = HMAC[19] & 0x0F  # Last byte, lower 4 bits
code = ((HMAC[offset] & 0x7F) << 24) | 
       (HMAC[offset+1] << 16) | 
       (HMAC[offset+2] << 8) | 
       HMAC[offset+3]
```

#### Step 5: Generate the OTP
Finally, we take the modulo to get a 6-digit code:

```python
OTP = code % 1,000,000
# Pad with leading zeros if needed
OTP = str(OTP).zfill(6)
```

Result: `483726`

### Why This is Secure

1. **One-Way Function**: Given the OTP, you cannot reverse-engineer the secret
2. **Time-Bound**: Each code is only valid for 30 seconds
3. **No Network Required**: Your phone generates codes offline
4. **Shared Secret**: Only you and the server know the secret key
5. **Cryptographically Strong**: Uses industry-standard HMAC-SHA1/SHA256

### Clock Synchronization

**Critical Concept**: Both the server and client must have synchronized clocks!

- If clocks drift apart, codes won't match
- Servers typically accept codes from **±1 time window** (30 seconds before/after)
- This gives a **90-second window** of validity
- This tolerance accounts for clock skew and network delays

```python
# Server validates code for T-1, T, and T+1
current_time_slot = floor(current_unix_time / 30)
valid_time_slots = [current_time_slot - 1, current_time_slot, current_time_slot + 1]

for time_slot in valid_time_slots:
    expected_code = generate_totp(secret, time_slot)
    if user_code == expected_code:
        return True
```

---

## The Complete MFA Flow

### Phase 1: User Registration

```
┌─────────┐                                    ┌─────────┐
│  User   │                                    │ Server  │
└────┬────┘                                    └────┬────┘
     │                                              │
     │  1. POST /register                           │
     │  { username, email, password }               │
     │─────────────────────────────────────────────>│
     │                                              │
     │                    2. Hash password (bcrypt) │
     │                    3. Store user in database │
     │                                              │
     │  4. 201 Created                              │
     │  { user_id, username, email }                │
     │<─────────────────────────────────────────────│
     │                                              │
```

### Phase 2: MFA Setup (Enrollment)

This is where the magic happens! The user enables MFA on their account.

```
┌─────────┐                                    ┌─────────┐                    ┌──────────────┐
│  User   │                                    │ Server  │                    │ Authenticator│
└────┬────┘                                    └────┬────┘                    │     App      │
     │                                              │                         └──────┬───────┘
     │  1. POST /mfa/setup                          │                                │
     │  { user_id } + session_token                 │                                │
     │─────────────────────────────────────────────>│                                │
     │                                              │                                │
     │                    2. Generate random secret │                                │
     │                       (e.g., JBSWY3DPEHPK3PXP)│                               │
     │                                              │                                │
     │                    3. Generate QR code data: │                                │
     │                       otpauth://totp/AppName:│                                │
     │                       user@email?secret=... │                                │
     │                                              │                                │
     │                    4. Store secret in DB     │                                │
     │                       (encrypted, marked as  │                                │
     │                        pending verification) │                                │
     │                                              │                                │
     │  5. 200 OK                                   │                                │
     │  { secret, qr_code_url, manual_entry_key }   │                                │
     │<─────────────────────────────────────────────│                                │
     │                                              │                                │
     │  6. Display QR code on screen                │                                │
     │                                              │                                │
     │  7. Open authenticator app                   │                                │
     │─────────────────────────────────────────────────────────────────────────────>│
     │                                              │                                │
     │  8. Scan QR code                             │                                │
     │─────────────────────────────────────────────────────────────────────────────>│
     │                                              │                                │
     │                                              │  9. Extract secret from QR     │
     │                                              │  10. Store secret locally      │
     │                                              │  11. Start generating codes    │
     │                                              │                                │
     │  12. Show first 6-digit code (e.g., 483726)  │                                │
     │<─────────────────────────────────────────────────────────────────────────────│
     │                                              │                                │
     │  13. POST /mfa/verify-setup                  │                                │
     │  { user_id, code: "483726" }                 │                                │
     │─────────────────────────────────────────────>│                                │
     │                                              │                                │
     │                    14. Compute expected code │                                │
     │                        using stored secret   │                                │
     │                    15. Compare codes         │                                │
     │                    16. Mark MFA as active    │                                │
     │                    17. Generate backup codes │                                │
     │                                              │                                │
     │  18. 200 OK                                  │                                │
     │  { status: "enabled",                        │                                │
     │    backup_codes: ["12345678", ...] }         │                                │
     │<─────────────────────────────────────────────│                                │
     │                                              │                                │
     │  19. Display backup codes to user            │                                │
     │      (user should save these!)               │                                │
     │                                              │                                │
```

**Key Points:**
- The **secret** is the most critical piece - it's shared ONCE during setup
- QR code is just a convenient way to transfer the secret to the app
- **Manual entry** option allows users to type the secret if QR scanning fails
- **Backup codes** are single-use codes for emergency access (if you lose your phone)

### Phase 3: Login with MFA

Now when the user logs in, they need BOTH password AND the current TOTP code:

```
┌─────────┐                                    ┌─────────┐                    ┌──────────────┐
│  User   │                                    │ Server  │                    │ Authenticator│
└────┬────┘                                    └────┬────┘                    │     App      │
     │                                              │                         └──────┬───────┘
     │  1. POST /login                              │                                │
     │  { username, password }                      │                                │
     │─────────────────────────────────────────────>│                                │
     │                                              │                                │
     │                    2. Verify password hash   │                                │
     │                    3. Check if MFA enabled   │                                │
     │                                              │                                │
     │  4. 200 OK (but NOT authenticated yet!)      │                                │
     │  { requires_mfa: true,                       │                                │
     │    temp_token: "xyz...",                     │                                │
     │    user_id: 1234 }                           │                                │
     │<─────────────────────────────────────────────│                                │
     │                                              │                                │
     │  5. Show "Enter MFA Code" screen             │                                │
     │                                              │                                │
     │  6. Open authenticator app                   │                                │
     │─────────────────────────────────────────────────────────────────────────────>│
     │                                              │                                │
     │                                              │  7. Compute current time slot  │
     │                                              │     T = floor(time / 30)       │
     │                                              │  8. Generate TOTP code         │
     │                                              │     using stored secret        │
     │                                              │                                │
     │  9. Display current code (e.g., 729513)      │                                │
     │     [Code refreshes every 30 seconds]        │                                │
     │<─────────────────────────────────────────────────────────────────────────────│
     │                                              │                                │
     │  10. User types code into login form         │                                │
     │                                              │                                │
     │  11. POST /mfa/verify                        │                                │
     │  { temp_token, code: "729513" }              │                                │
     │─────────────────────────────────────────────>│                                │
     │                                              │                                │
     │                    12. Validate temp_token   │                                │
     │                    13. Retrieve user's secret│                                │
     │                    14. Compute expected codes│                                │
     │                        for T-1, T, T+1       │                                │
     │                    15. Compare with user code│                                │
     │                    16. ✓ Code matches!       │                                │
     │                    17. Create session/JWT    │                                │
     │                    18. Mark login successful │                                │
     │                                              │                                │
     │  19. 200 OK                                  │                                │
     │  { access_token: "jwt...",                   │                                │
     │    user: { id, username, email } }           │                                │
     │<─────────────────────────────────────────────│                                │
     │                                              │                                │
     │  20. Redirect to dashboard                   │                                │
     │      User is now fully authenticated! 🎉     │                                │
     │                                              │                                │
```

### Important Security Details

#### Temporary Token
The `temp_token` returned after password verification:
- Is short-lived (5-10 minutes)
- Cannot be used to access protected resources
- Only valid for MFA verification
- Prevents replay attacks

#### Rate Limiting
```python
# Server implements rate limiting:
- Max 5 MFA attempts per temp_token
- Max 10 failed attempts per user per hour
- Account lockout after excessive failures
- IP-based rate limiting for API endpoints
```

#### Code Reuse Prevention
```python
# Server tracks used codes:
- Each valid code can only be used ONCE
- Store used codes with timestamps
- Prevent replay attacks within the 90-second window
```

---

## Technical Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontend (React)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Login Page   │  │ MFA Setup    │  │  Protected Dashboard     │  │
│  │              │  │ Page         │  │                          │  │
│  │ - Username   │  │ - QR Display │  │  - User Profile          │  │
│  │ - Password   │  │ - Code Input │  │  - Settings              │  │
│  │ - MFA Input  │  │ - Backup     │  │  - MFA Management        │  │
│  │              │  │   Codes      │  │                          │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘  │
│         │                  │                     │                  │
│         └──────────────────┴─────────────────────┘                  │
│                            │                                        │
│                   ┌────────▼────────┐                               │
│                   │  Axios HTTP     │                               │
│                   │  Client         │                               │
│                   └────────┬────────┘                               │
└────────────────────────────┼─────────────────────────────────────────┘
                             │
                             │ HTTPS (REST API)
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│                      Backend (FastAPI)                               │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                      API Endpoints                             │  │
│  │                                                                 │  │
│  │  /api/auth/register       - Create new user account            │  │
│  │  /api/auth/login          - Verify password (step 1)           │  │
│  │  /api/auth/verify-mfa     - Verify TOTP code (step 2)          │  │
│  │  /api/mfa/setup           - Generate secret & QR code          │  │
│  │  /api/mfa/verify-setup    - Confirm MFA setup                  │  │
│  │  /api/mfa/disable         - Disable MFA                        │  │
│  │  /api/user/profile        - Get user data (protected)          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                   Business Logic Layer                         │  │
│  │                                                                 │  │
│  │  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐  │  │
│  │  │ Auth Service    │  │ MFA Service  │  │  User Service    │  │  │
│  │  │                 │  │              │  │                  │  │  │
│  │  │ - Password hash │  │ - TOTP gen   │  │  - CRUD ops      │  │  │
│  │  │ - JWT create    │  │ - QR create  │  │  - Validation    │  │  │
│  │  │ - Token verify  │  │ - Code verify│  │  - Queries       │  │  │
│  │  └─────────────────┘  └──────────────┘  └──────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                   Security Layer                               │  │
│  │                                                                 │  │
│  │  - Password hashing (bcrypt)                                   │  │
│  │  - JWT token management                                        │  │
│  │  - Rate limiting                                               │  │
│  │  - Input validation                                            │  │
│  │  - Secret encryption (at rest)                                 │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                             │                                        │
└─────────────────────────────┼──────────────────────────────────────────┘
                              │
                              │ SQL Queries
                              │
┌─────────────────────────────▼──────────────────────────────────────────┐
│                      PostgreSQL Database                               │
│                                                                         │
│  ┌─────────────────────┐  ┌──────────────────────────────────────┐    │
│  │   users             │  │   mfa_secrets                        │    │
│  ├─────────────────────┤  ├──────────────────────────────────────┤    │
│  │ id (PK)             │  │ id (PK)                              │    │
│  │ username (unique)   │  │ user_id (FK) → users.id              │    │
│  │ email (unique)      │  │ secret_key (encrypted)               │    │
│  │ password_hash       │  │ is_active (boolean)                  │    │
│  │ mfa_enabled         │  │ verified_at (timestamp)              │    │
│  │ created_at          │  │ created_at                           │    │
│  │ updated_at          │  └──────────────────────────────────────┘    │
│  └─────────────────────┘                                              │
│                                                                        │
│  ┌──────────────────────────────────┐  ┌─────────────────────────┐   │
│  │   backup_codes                   │  │   login_attempts        │   │
│  ├──────────────────────────────────┤  ├─────────────────────────┤   │
│  │ id (PK)                          │  │ id (PK)                 │   │
│  │ user_id (FK) → users.id          │  │ user_id (FK)            │   │
│  │ code_hash                        │  │ ip_address              │   │
│  │ used (boolean)                   │  │ success (boolean)       │   │
│  │ created_at                       │  │ attempted_at            │   │
│  └──────────────────────────────────┘  └─────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MFA secrets table
CREATE TABLE mfa_secrets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    secret_key VARCHAR(255) NOT NULL,  -- Encrypted
    is_active BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Backup codes for emergency access
CREATE TABLE backup_codes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    code_hash VARCHAR(255) NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Login attempts for security monitoring
CREATE TABLE login_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    ip_address VARCHAR(45),
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(100),
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Used TOTP codes to prevent replay attacks
CREATE TABLE used_totp_codes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    code_hash VARCHAR(255) NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_mfa_secrets_user_id ON mfa_secrets(user_id);
CREATE INDEX idx_login_attempts_user_id ON login_attempts(user_id);
CREATE INDEX idx_used_totp_codes_user_id ON used_totp_codes(user_id);
```

---

## Security Considerations

### 1. Secret Storage

**Problem**: The TOTP secret is like a master key. If leaked, an attacker can generate valid codes.

**Solution**:
```python
# Encrypt secrets at rest using AES-256
from cryptography.fernet import Fernet

# Generate encryption key (store in environment variable)
encryption_key = Fernet.generate_key()
cipher = Fernet(encryption_key)

# Encrypt before storing
encrypted_secret = cipher.encrypt(secret.encode())
db.save(encrypted_secret)

# Decrypt when needed
decrypted_secret = cipher.decrypt(encrypted_secret).decode()
```

### 2. Password Hashing

**Never store plain passwords!** Use bcrypt with a high cost factor:

```python
import bcrypt

# Hashing (during registration)
password = "user_password"
salt = bcrypt.gensalt(rounds=12)  # Cost factor of 12
password_hash = bcrypt.hashpw(password.encode(), salt)

# Verification (during login)
is_valid = bcrypt.checkpw(password.encode(), stored_hash)
```

### 3. JWT Token Security

```python
# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET")  # Strong random secret
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 3600  # 1 hour

# Token payload
payload = {
    "user_id": user.id,
    "username": user.username,
    "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION),
    "iat": datetime.utcnow(),  # Issued at
    "jti": str(uuid.uuid4())   # Unique token ID (for revocation)
}
```

### 4. Rate Limiting

Prevent brute-force attacks:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")  # Max 5 attempts per minute per IP
async def login(request: Request, credentials: LoginSchema):
    pass

@app.post("/api/auth/verify-mfa")
@limiter.limit("3/minute")  # Max 3 MFA attempts per minute
async def verify_mfa(request: Request, data: MFAVerifySchema):
    pass
```

### 5. HTTPS Enforcement

**CRITICAL**: Always use HTTPS in production!

```python
# FastAPI configuration
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if not DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)
```

### 6. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only!
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 7. Input Validation

```python
from pydantic import BaseModel, EmailStr, Field, validator

class RegisterSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digits')
        return v
```

### 8. Protection Against Timing Attacks

When comparing codes, use constant-time comparison:

```python
import hmac

def verify_code(user_code: str, expected_code: str) -> bool:
    # NOT secure: if user_code == expected_code
    # Secure (constant-time):
    return hmac.compare_digest(user_code, expected_code)
```

---

## Technologies & Stack

### Frontend

#### React 18+
- **Why**: Component-based architecture, large ecosystem, excellent for SPAs
- **Purpose**: Build interactive UI components for login, MFA setup, and dashboard

#### Vite
- **Why**: Lightning-fast development server, optimized builds, better than Create React App
- **Purpose**: Build tool and dev server

#### TailwindCSS
- **Why**: Utility-first CSS, rapid UI development, small bundle size
- **Purpose**: Styling and responsive design

#### React Router
- **Why**: Standard routing library for React
- **Purpose**: Client-side routing (login, dashboard, setup pages)

#### Axios
- **Why**: Promise-based HTTP client, better error handling than fetch
- **Purpose**: API communication with backend

#### QR Code Display
- **Why**: User-friendly way to transfer secret to authenticator app
- **Purpose**: Display QR codes during MFA setup

### Backend

#### Python 3.11+
- **Why**: Great ecosystem for cryptography, well-documented libraries
- **Purpose**: Core backend language

#### FastAPI
- **Why**: 
  - Blazingly fast (based on Starlette & Pydantic)
  - Automatic API documentation (Swagger UI)
  - Type hints and validation
  - Async support
  - Modern Python framework
- **Purpose**: REST API server

#### PostgreSQL
- **Why**:
  - ACID compliance (critical for auth data)
  - Robust and reliable
  - Excellent for relational data
  - Better than MySQL for complex queries
- **Purpose**: Primary database for users, secrets, and audit logs

#### SQLAlchemy
- **Why**: Powerful ORM, supports migrations with Alembic
- **Purpose**: Database ORM and query builder

#### PyOTP
- **Why**: Pure Python TOTP/HOTP implementation, RFC 6238 compliant
- **Purpose**: Generate and verify TOTP codes

```python
import pyotp

# Generate secret
secret = pyotp.random_base32()

# Generate TOTP URI for QR code
totp = pyotp.TOTP(secret)
uri = totp.provisioning_uri(
    name=user.email,
    issuer_name="MFA Token Authenticator"
)

# Verify code
is_valid = totp.verify(user_code, valid_window=1)  # ±30 seconds
```

#### QRCode
- **Why**: Generate QR codes for easy secret transfer
- **Purpose**: Create QR codes for authenticator app setup

```python
import qrcode
import io

qr = qrcode.make(uri)
buffer = io.BytesIO()
qr.save(buffer, format='PNG')
qr_base64 = base64.b64encode(buffer.getvalue()).decode()
```

#### Passlib + Bcrypt
- **Why**: Industry-standard password hashing
- **Purpose**: Secure password storage

#### PyJWT
- **Why**: Create and verify JSON Web Tokens
- **Purpose**: Session management and API authentication

#### Pydantic
- **Why**: Data validation using Python type hints
- **Purpose**: Request/response validation, settings management

#### CORS Middleware
- **Why**: Allow frontend to communicate with backend
- **Purpose**: Cross-origin resource sharing

---

## API Endpoints
# Edit .env with your configuration:
# - DATABASE_URL
# - JWT_SECRET (generate with: openssl rand -hex 32)
# - ENCRYPTION_KEY (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Initialize database
createdb mfa_auth_db
alembic upgrade head

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: `http://localhost:8000`  
API docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# Edit .env:
# VITE_API_URL=http://localhost:8000

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

---

## API Documentation

### Authentication Endpoints

#### POST `/api/auth/register`
Register a new user account.

**Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response (201):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "mfa_enabled": false,
  "created_at": "2026-01-21T10:30:00Z"
}
```

#### POST `/api/auth/login`
First step of login - verify password.

**Request:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response (200) - MFA Enabled:**
```json
{
  "requires_mfa": true,
  "temp_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Please enter your MFA code"
}
```

**Response (200) - MFA Disabled:**
```json
{
  "requires_mfa": false,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

#### POST `/api/auth/verify-mfa`
Second step of login - verify TOTP code.

**Request:**
```json
{
  "temp_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "code": "123456"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

### MFA Management Endpoints

#### POST `/api/mfa/setup`
Generate MFA secret and QR code.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAA...",
  "manual_entry_key": "JBSW-Y3DP-EHPK-3PXP",
  "otpauth_url": "otpauth://totp/MFAApp:john@example.com?secret=JBSWY3DPEHPK3PXP&issuer=MFAApp"
}
```

#### POST `/api/mfa/verify-setup`
Verify TOTP code to activate MFA.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "code": "123456"
}
```

**Response (200):**
```json
{
  "status": "enabled",
  "backup_codes": [
    "12345678",
    "23456789",
    "34567890",
    "45678901",
    "56789012"
  ],
  "message": "MFA enabled successfully. Save your backup codes!"
}
```

#### DELETE `/api/mfa/disable`
Disable MFA for user account.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "status": "disabled",
  "message": "MFA has been disabled"
}
```

---

## Learning Resources

### Official Documentation
- [RFC 6238 - TOTP](https://datatracker.ietf.org/doc/html/rfc6238)
- [RFC 4226 - HOTP](https://datatracker.ietf.org/doc/html/rfc4226)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PyOTP Documentation](https://pyauth.github.io/pyotp/)

### Security Best Practices
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [NIST Digital Identity Guidelines](https://pages.nist.gov/800-63-3/)

### Understanding TOTP
- [How TOTP Works (Illustrated)](https://www.freecodecamp.org/news/how-time-based-one-time-passwords-work-and-why-you-should-use-them/)
- [TOTP Algorithm Visualization](https://rootprojects.org/authenticator/)

### Video Tutorials
- [Two-Factor Authentication Explained](https://www.youtube.com/watch?v=ZXFYT6RsR0Y)
- [How Authenticator Apps Work](https://www.youtube.com/watch?v=VOYxF12K1vE)

---

## Contributing

This is a learning project! Feel free to:
- Experiment with the code
- Try different authentication flows
- Implement additional security features
- Improve the UI/UX

---

## License

MIT License - Feel free to use this for learning purposes!

---

## Acknowledgments

Built to understand the inner workings of Multi-Factor Authentication and modern authentication systems. Special thanks to the open-source community for the amazing tools and libraries that make projects like this possible.

---

**Happy Learning! 🚀🔐**
