# MFA Token Authenticator

A full-stack multi-factor authentication (MFA) application with TOTP support.

## Project Structure

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **Frontend**: React + TypeScript + Vite + Zustand

## Features

- User registration and authentication
- TOTP-based MFA with QR code generation
- Backup codes for account recovery
- JWT token-based sessions
- Secure password hashing with bcrypt
- Encrypted MFA secrets using Fernet

## Setup

### Prerequisites

- Node.js & npm - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)
- Python 3.11+
- PostgreSQL 18+

### Backend Setup

```sh
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (create .env file)
# DATABASE_URL=postgresql://user:password@localhost/dbname
# SECRET_KEY=your-secret-key
# ALGORITHM=HS256
# ACCESS_TOKEN_EXPIRE_MINUTES=30

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```sh
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:8080`

## Technologies

### Backend
- FastAPI
- PostgreSQL
- SQLAlchemy ORM
- Pydantic v2
- PyOTP (TOTP)
- bcrypt (password hashing)
- Fernet (secret encryption)
- JWT tokens

### Frontend
- Vite
- TypeScript
- React
- Zustand (state management)
- shadcn-ui
- Tailwind CSS
- React Router

## API Endpoints

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login with MFA
- `POST /api/auth/mfa/setup` - Generate MFA QR code
- `POST /api/auth/mfa/verify` - Verify and activate MFA
- `POST /api/auth/mfa/verify-backup` - Verify backup code
- `POST /api/auth/mfa/reset` - Reset MFA
- `POST /api/auth/mfa/disable` - Disable MFA

## License

MIT

