"""Authenticated-caller type shared by the API layer (deps) and the services. Not a response model."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    name: str
    email: str
    role: str  # student | faculty | hod | iqac (from the database, never from the token)
    dept_code: str
