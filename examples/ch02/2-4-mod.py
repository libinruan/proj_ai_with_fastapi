from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base  # Updated import
from typing import List
from pydantic import BaseModel, EmailStr, ConfigDict  # Added ConfigDict
import uvicorn
from contextlib import asynccontextmanager  # Added for lifespan

# Create SQLite in-memory database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Use file-based for persistence
# For in-memory database: "sqlite:///:memory:"

# Create a file-based SQLite database (sqlite:///./test.db) not an in-memory database.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This line imports the declarative_base function from SQLAlchemy, which is used
# to create a base class for declarative models. Models in Python web frameworks
# (Django, Flask) are classes that define data structure and behavior, database
# abstractions that eliminate the need for raw SQL, and blueprints for
# application entities (users, posts, products).
Base = declarative_base()

# SQLAlchemy Models
# 1. Bidirectional Relationship: It establishes a two-way (bidirectional) relationship between the UserModel and MessageModel classes.
# 2. One-to-Many Relationship: It defines that one user can have many messages. This is a common database pattern where a parent entity (user) can have multiple child entities (messages).
# 3. Attribute Creation: It creates a virtual attribute called "messages" on each UserModel instance, which will contain a collection of all the MessageModel instances associated with that user.
# 4. Back Reference: The back_populates="user" parameter creates a matching reference in the other direction. It means that each MessageModel instance will have a "user" attribute that refers back to its parent UserModel.
class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    
    # Create a two-way relationship with MessageModel
    messages = relationship("MessageModel", back_populates="user")

class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationship with UserModel
    user = relationship("UserModel", back_populates="messages")

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models for request/response
class Message(BaseModel):
    id: int
    content: str
    
    # Updated from orm_mode to from_attributes
    # It's because we want to use the new Pydantic v2 feature
    # that allows us to create models from attributes instead of ORM instances.
    model_config = ConfigDict(from_attributes=True)

class User(BaseModel):
    id: int
    email: str
    name: str
    
    # Updated from orm_mode to from_attributes
    model_config = ConfigDict(from_attributes=True)  
    # By using ConfigDict(from_attributes=True) in your Pydantic model, you can
    # directly convert Python objects—such as ORM objects from SQLAlchemy—into
    # Pydantic models, not just dictionaries. This works because Pydantic will
    # read the attributes from the object (by using from_attributes=True), not
    # just from a dictionary, making serialization and validation much easier
    # when working with database models.

class UserWithMessages(User):
    messages: List[Message] = []
    
    # FastAPI automatically converts the SQLAlchemy model to the Pydantic model, which
    # tells Pydantic to read attributes directly from the object
    model_config = ConfigDict(from_attributes=True)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Add some sample data for testing
def add_sample_data(db: Session):
    # Check if data already exists
    if db.query(UserModel).count() > 0:
        return
    
    # Create sample users
    user1 = UserModel(email="john@example.com", name="John Doe")
    user2 = UserModel(email="jane@example.com", name="Jane Smith")
    db.add(user1)
    db.add(user2)
    db.commit()
    
    # Create sample messages
    message1 = MessageModel(content="Hello, this is my first message", user_id=user1.id)
    message2 = MessageModel(content="Another message from me", user_id=user1.id)
    message3 = MessageModel(content="Hi there, I'm Jane", user_id=user2.id)
    db.add(message1)
    db.add(message2)
    db.add(message3)
    db.commit()

# Replace on_event with lifespan. The lifespan context manager is used to manage
# application-level resources that need proper setup and cleanup. For
# tenant-level or request-level resource management, you would use dependencies
# (like the get_db() function in your code).
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database with sample data
    db = SessionLocal()
    add_sample_data(db)
    db.close()
    # Everything before yield is startup code, everything after is shutdown
    # code.  After executing the startup code, the function pauses at yield and
    # the application runs normally
    yield  # App runs normally while paused here.
    
    # Shutdown code: runs once when app stops. Clean up resources if needed
    pass

app = FastAPI(lifespan=lifespan)

# Routes
@app.get("/")
def root():
    return {"message": "User Messages API"}

# Note on the respnose_model:
# response_model=UserWithMessages is specified in the decorator for the endpoint. This tells FastAPI to:
# 1. Use the UserWithMessages Pydantic model to validate and serialize the response data
# 2. Generate OpenAPI documentation based on this model
# 3. Automatically convert the SQLAlchemy model instance (user) to the Pydantic model (UserWithMessages)
# - The UserWithMessages model extends the User model and includes a messages field that contains a list of Message objects, which matches the relationship structure defined in your SQLAlchemy models.
@app.get("/users/{email}/messages", response_model=List[Message])
def get_user_messages(email: str, db: Session = Depends(get_db)):
    # Find the user by email
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with email {email} not found")
    
    # Get the user's messages
    messages = db.query(MessageModel).filter(MessageModel.user_id == user.id).all()
    return messages  # FastAPI converts MessageModel instances (SQLAlchemy objects) to Message Pydantic models (List[Message])

@app.get("/users", response_model=List[User])
def get_users(db: Session = Depends(get_db)):
    users = db.query(UserModel).all()
    return users

# 1. When you query a user with their messages using get_user_with_messages(), SQLAlchemy automatically loads all the messages associated with that user.
# 2. The "UserWithMessages" Pydantic model includes a messages field that matches this relationship structure.
# 3. In the database, this relationship is physically implemented through the "user_id" foreign key in the messages table, which references the id column in the users table.
@app.get("/users/{email}", response_model=UserWithMessages)
def get_user_with_messages(email: str, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == email).first()  # retrieves a UserModel with its relationships
    if not user:
        raise HTTPException(status_code=404, detail=f"User with email {email} not found")
    return user  #* FastAPI converts UserModel (a SQLAlchemy model) to UserWithMessages (the Pydantic model), which is a JSON response that matches the structure defined in the Pydantic model, UserWithMessages.


if __name__ == "__main__":
    """
    Access the API endpoints using a web browser or tools like curl/Postman:
    - Root endpoint:
        http://localhost:8000/
    - List all users:
        http://localhost:8000/users
    - Get a specific user with their messages:
        http://localhost:8000/users/john@example.com
    - Get only a user's messages:
        http://localhost:8000/users/john@example.com/messages
    Or use the Swagger UI for interactive testing:
        http://localhost:8000/docs

    To reset the database:
        rm test.db
        python 2-4-mod.py

    Swith to an in-memory databaase:
        SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"  # In-memory database

    Testing with curl
    - Get the root endpoint
        curl http://localhost:8000/
    - List all users
        curl http://localhost:8000/users
    - Get a specific user with messages
        curl http://localhost:8000/users/john@example.com
    - Get only a user's messages
        curl http://localhost:8000/users/john@example.com/messages
    """
    uvicorn.run("2-4-mod:app", host="0.0.0.0", port=8000, reload=True)