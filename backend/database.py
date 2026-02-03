from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend import models
from config import get_settings


#Get settings instance
settings = get_settings()

#create the database engine
#The engine is the starting point for SQLAlachemy -  it manages DB connections
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug #log sql queries when DEBUG=True
)

#Session factory - creates database sessions
SessionLocal = sessionmaker(
    autocommit=False, #control when to save
    authflush=False, #control when to send to db
    bind=engine #bind to the engine

)

#create the model base class
#all db models will inherit from this
Base = declarative_base()


def get_db():
    """
    creates a new database session
    yields it to the faastapi endpoint
    automatically closes it even if error occurs

    Usage in FastAPI:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
    """

    db = SessionLocal()
    try:
        yield db # give the session to the endpoint
    finally:
        db.close() # close even if error occurs

def init_db():
    """
    Initialize the database by creating all tables.
    
    This will:
    1. Import all models (so Base knows about them)
    2. Create tables that don't exist yet
    3. Skip tables that already exist (won't overwrite data)
    
    Called when starting the app for the first time.
    """
    import models
    #create all tables
    Base.metadata.create_all(bind=engine)

