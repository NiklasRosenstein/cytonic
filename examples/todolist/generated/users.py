
import dataclasses
import datetime

from skye.api.runtime import authentication, endpoint, args, query, service, Credentials
from skye.api.runtime.exceptions import NotFoundError


@dataclasses.dataclass
class UserNotFound(NotFoundError):
  ERROR_NAME = 'Users:UserNotFound'
  user_id: str

  def __post_init__(self) -> None:
    super().__init__()


@dataclasses.dataclass
class User:
  id: str
  email: str


@service('Users')
@authentication('oauth2_bearer')
class UsersServiceAsync:

  @endpoint('GET /users/me')
  async def me(self, auth: Credentials) -> User:
    raise NotImplementedError('UserServiceAsync.me()')

  @endpoint('GET /users/id/{id_}')
  async def get_user(self, auth: Credentials, id_: str) -> User:
    raise NotImplementedError('UserServiceAsync.get_user()')
