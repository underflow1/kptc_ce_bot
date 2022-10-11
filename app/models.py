from datetime import datetime, date
from dataclasses import dataclass, astuple, fields

@dataclass
class PhotoModel:
    __tablename__ = "photo"

    filename: str
    location: str
    user: str
    id: int = None
    created_at: datetime = datetime.now()

@dataclass
class LocationModel:
    __tablename__ = "location"

    name: str
    id: int = None
    created_at: datetime = datetime.now()

@dataclass
class UserModel:
    __tablename__ = "user"

    id: int = None
    user_id: str = None
    phone_number: str = None
