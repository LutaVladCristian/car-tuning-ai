from pydantic import BaseModel


class FirebaseAuthRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    id: int
    firebase_uid: str
    email: str
    display_name: str | None

    model_config = {"from_attributes": True}
