# -*- coding: utf-8 -*-
# Do not edit; this file was automatically generated with cytonic.codegen.python.


import abc
import dataclasses

from cytonic.description import authentication, endpoint, service
from cytonic.model import OAuth2Bearer
from cytonic.runtime import Credentials, NotFoundError


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
class UsersServiceBlocking(abc.ABC):
  " User management service. "

  @endpoint("GET /users/me")
  @abc.abstractmethod
  def me(self, auth: Credentials) -> User:
    pass

  @endpoint("GET /users/id/{user_id}")
  @abc.abstractmethod
  def get_user(self, auth: Credentials, user_id: str) -> User:
    pass


@service('Users')
@authentication(OAuth2Bearer())
class UsersServiceAsync(abc.ABC):
  " User management service. "

  @endpoint("GET /users/me")
  @abc.abstractmethod
  async def me(self, auth: Credentials) -> User:
    pass

  @endpoint("GET /users/id/{user_id}")
  @abc.abstractmethod
  async def get_user(self, auth: Credentials, user_id: str) -> User:
    pass
