
import dataclasses

from skye.api.runtime.service import service
from skye.api.runtime.endpoint import endpoint
from skye.api.runtime.auth import authentication, Credentials, OAuth2BearerAuthenticationMethod
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
@authentication(OAuth2BearerAuthenticationMethod())
class UsersServiceAsync:

  @endpoint('GET /users/me')
  async def me(self, auth: Credentials) -> User:
    raise NotImplementedError('UserServiceAsync.me()')

  @endpoint('GET /users/id/{id_}')
  async def get_user(self, auth: Credentials, id_: str) -> User:
    raise NotImplementedError('UserServiceAsync.get_user()')
