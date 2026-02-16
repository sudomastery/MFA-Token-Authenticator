# MFA Token Authenticator

A production-ready Multi-Factor Authentication (MFA) system implementing Time-based One-Time Passwords (TOTP) with full support for industry-standard authenticator applications including Microsoft Authenticator, Ente Auth, Google Authenticator, and any RFC 6238-compliant TOTP client.

---

## Overview

This project provides a complete MFA authentication solution with user registration, two-factor login, and account recovery capabilities. The system features a FastAPI backend with PostgreSQL database and a React frontend, implementing industry best practices for secure authentication.

### Screenshots

#### Login and Registration
Users authenticate with username and password credentials. MFA verification is required for accounts with two-factor authentication enabled. Account recovery via backup codes is supported for users who have lost access to their authenticator device.

![Login and Registration](screenshots/login_and_authentication.png)

#### MFA Setup
During enrollment, users scan a QR code with their authenticator application to establish the shared TOTP secret. Eight backup recovery codes are generated and displayed for secure storage.

![MFA Setup - QR Code](screenshots/mfa_setup.png)

#### Backup Codes
Single-use backup codes provide emergency account access when the primary authenticator device is unavailable.

![Backup Codes](screenshots/backup_codes.png)

#### Protected Resources
After successful MFA verification, users gain access to protected application resources and dashboard.

![MFA Verification](screenshots/security_dashboard.png)

---

## Features

### Authentication Capabilities
- User registration with email verification
- Password-based authentication with bcrypt hashing (12 rounds)
- TOTP-based two-factor authentication
- Backup code generation and verification
- MFA reset and re-enrollment
- JWT token-based session management (30-minute expiration)

### Security Implementation
- RFC 6238 compliant TOTP generation
- Fernet (AES-256) encryption for TOTP secrets at rest
- Constant-time comparison for token verification
- Rate limiting on authentication endpoints
- Brute-force protection with progressive lockout
- Secure random number generation for backup codes
- Password strength validation

### User Experience
- QR code generation for quick authenticator setup
- Manual secret entry as alternative to QR scanning
- Clear error messaging with security consideration
- Responsive design for mobile and desktop
- Persistent authentication state

---

## Installation

### Requirements

- Node.js 18.x or higher
- Python 3.11 or higher
- PostgreSQL 14.x or higher
- npm or yarn package manager

### Backend Configuration

```bash
# Clone the repository
git clone <repository-url>
cd MFA-Token-Authenticator/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `.env` with the following configuration:

```bash
DATABASE_URL=postgresql://user:password@localhost/mfa_db
JWT_SECRET=<generate-with-openssl-rand-hex-32>
ENCRYPTION_KEY=<generate-with-fernet>
```

Generate secure keys:
```bash
# JWT secret
openssl rand -hex 32

# Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Initialize the database:
```bash
createdb mfa_db
alembic upgrade head
```

Start the backend server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

### Frontend Configuration

```bash
cd ../frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
```

Edit `.env`:
```bash
VITE_API_URL=http://localhost:8000
```

Start the development server:
```bash
npm run dev
```

The application will be accessible at `http://localhost:5173`.

---

## Architecture

### System Design

The application implements a decoupled architecture with separate frontend and backend services communicating via REST API. The backend provides a comprehensive authentication API with automatic schema validation, while the frontend delivers a responsive single-page application.

**Backend Stack:**
- FastAPI for asynchronous HTTP request handling
- SQLAlchemy ORM for database abstraction
- PostgreSQL for persistent data storage
- Pydantic for request/response validation
- Alembic for database migrations

**Frontend Stack:**
- React 18 for component-based UI
- Zustand for client-side state management
- Vite for optimized build tooling
- React Router for client-side routing
- TailwindCSS for responsive styling

### Authentication Workflow

The system implements a multi-stage authentication process:

1. **Initial Authentication**: User credentials are validated against bcrypt password hashes stored in the database.

2. **MFA Challenge**: If MFA is enabled, a temporary token (10-minute expiration) is issued to authorize the TOTP verification request.

3. **TOTP Verification**: The user submits a 6-digit code from their authenticator. The server decrypts the stored TOTP secret, generates expected codes for the current time window (±30 seconds), and performs constant-time comparison.

4. **Session Establishment**: Upon successful verification, a JWT access token is issued with a 30-minute expiration and a refresh token with a 7-day expiration.

### TOTP Protocol Implementation

The system adheres to RFC 6238 for Time-based One-Time Password generation:

- **Secret Generation**: 160-bit (32-character base32) cryptographically random secrets are generated using PyOTP.
- **Code Generation**: 6-digit codes are produced by truncating HMAC-SHA1(secret, time_counter) where time_counter = floor(unix_timestamp / 30).
- **Validation Window**: Codes are accepted within a ±30 second window to accommodate clock skew.
- **Secret Storage**: TOTP secrets are encrypted using Fernet (AES-256-CBC) before database storage.

### Security Architecture

**Password Security:**
- Passwords are hashed using bcrypt with a cost factor of 12 (2^12 iterations).
- Each hash includes a unique salt generated by the bcrypt algorithm.
- Verification uses constant-time comparison to prevent timing attacks.

**Token Security:**
- JWT tokens are signed using HMAC-SHA256 with a server-side secret.
- Tokens include expiration claims (exp) and issued-at timestamps (iat).
- Token validation occurs on every protected endpoint request.

**Backup Code Security:**
- Eight 8-character hexadecimal codes are generated using cryptographically secure random number generation.
- Codes are hashed with bcrypt (cost factor 12) before database storage.
- Each code is single-use and marked as consumed after verification.

**Rate Limiting:**
- Login endpoint: 5 attempts per minute per IP address.
- MFA verification: 3 attempts per minute per IP address.
- Progressive lockout after repeated authentication failures.

### Database Schema

The relational schema consists of four primary tables:

**users**
- Primary user account information
- Indexed columns: username, email
- Stores bcrypt password hash and MFA status flag

**mfa_secrets**
- One-to-one relationship with users
- Stores Fernet-encrypted TOTP secret
- Tracks activation status and verification timestamp

**backup_codes**
- One-to-many relationship with users
- Stores bcrypt hashes of backup codes
- Tracks usage status and consumption timestamp

**login_attempts**
- Audit log of authentication attempts
- Records timestamp, IP address, and success status
- Used for rate limiting and security monitoring

Foreign key constraints ensure referential integrity with cascade deletion for user-related data.

---

## API Reference

### Authentication Endpoints

#### POST /api/auth/register

Register a new user account.

**Request Body:**
```json
{
  "username": "string (3-50 characters)",
  "email": "string (valid email format)",
  "password": "string (minimum 8 characters, must include uppercase and digit)"
}
```

**Response:** 201 Created
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "mfa_enabled": false,
  "created_at": "2026-02-16T10:30:00Z"
}
```

#### POST /api/auth/login

Authenticate user credentials.

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "mfa_token": "string (optional, required if MFA enabled)"
}
```

**Response:** 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "mfa_enabled": true
  }
}
```

### MFA Management Endpoints

#### POST /api/mfa/setup

Generate TOTP secret and QR code for MFA enrollment. Requires valid JWT token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** 200 OK
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAA...",
  "manual_entry_key": "JBSW-Y3DP-EHPK-3PXP",
  "otpauth_url": "otpauth://totp/MFAApp:john@example.com?secret=..."
}
```

#### POST /api/mfa/verify

Activate MFA after scanning QR code. Requires valid JWT token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "token": "123456"
}
```

**Response:** 200 OK
```json
{
  "status": "enabled",
  "backup_codes": [
    "A3F7B2E1",
    "F91C4D8A",
    "2B7E6C1F",
    "8D4A1E5C",
    "C6B2F9A3",
    "E8D1C4B7",
    "5A3E9F2D",
    "D7C3A6E8"
  ],
  "message": "MFA enabled successfully"
}
```

#### POST /api/mfa/reset

Reset MFA configuration. Requires valid JWT token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** 200 OK
```json
{
  "status": "disabled",
  "message": "MFA configuration has been reset"
}
```

#### POST /api/mfa/verify-backup

Verify backup code for account recovery.

**Request Body:**
```json
{
  "username": "johndoe",
  "backup_code": "A3F7B2E1"
}
```

**Response:** 200 OK
```json
{
  "message": "Backup code verified",
  "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

Complete API documentation with request/response schemas and example requests is available via the interactive Swagger UI at `http://localhost:8000/docs`.

---

## License

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
