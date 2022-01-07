# -*- coding: utf-8 -*-

import dataclasses

from skye.api.runtime.auth import Credentials
from skye.api.runtime.auth import OAuth2Bearer
from skye.api.runtime.auth import authentication
from skye.api.runtime.endpoint import endpoint
from skye.api.runtime.exceptions import NotFoundError
from skye.api.runtime.service import service


@dataclasses.dataclass
class UserNotFoundError(NotFoundError):
  user_id: str

  def __post_init__(self):
    super().__init__()


@dataclasses.dataclass
class User:
  id: str
  email: str


@service('Users')
@authentication(OAuth2Bearer())
class UsersServiceAsync:
  " User management service. "

  @endpoint('GET /users/me')
  async def me(self, auth: Credentials) -> User:
    pass

  @endpoint('GET /users/id/{user_id}')
  async def get_user(self, auth: Credentials, user_id: str) -> User:
    pass
