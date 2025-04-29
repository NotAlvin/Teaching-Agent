# type: ignore
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app_be.models.db_models import User
from app_be.models.schemas import UserCreate, UserUpdate
from app_be.services.security import get_password_hash


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email"""
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get a list of users with pagination"""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        is_active=True,
        created_at=datetime.now(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user: UserUpdate) -> User:
    """Update a user's information"""
    db_user = get_user(db, user_id)

    update_data = user.dict(exclude_unset=True)

    # Hash the password if it's being updated
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def deactivate_user(db: Session, user_id: int) -> User:
    """Deactivate a user (soft delete)"""
    db_user = get_user(db, user_id)
    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    return db_user
