from enum import IntEnum
import json
from pydantic import BaseModel, parse_file_as


class Permission(IntEnum):
    ADMIN = 1
    USER = 2
    VIEWER = 3


class User(BaseModel):
    login: str
    password: str
    id: str
    permission: Permission


def load_data() -> (list[User], dict[str, User]):
    data = parse_file_as(list[User], "data.json")
    user_logins = {user.login: user for user in data}
    return data, user_logins


def save_data(data: list[User]):
    with open("data.json", 'w') as f:
        f.write(json.dumps([x.dict() for x in data]))
