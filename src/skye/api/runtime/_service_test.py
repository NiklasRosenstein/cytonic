
import dataclasses

from nr.pylang.utils.singletons import NotSet

from .auth import Basic, Credentials, NoAuthenticationMethod, OAuth2Bearer, authentication
from .endpoint import ParamKind, Path, endpoint
from .service import Argument, Service


@dataclasses.dataclass
class User:
  id: str
  name: str
  age: int


@dataclasses.dataclass
class UserAttrs:
  name: str
  age: int


@authentication(OAuth2Bearer())
class ATestService:

  @authentication(Basic())
  @authentication(None)
  @endpoint('GET /users/{id}')
  def get_user(self, auth: Credentials, id: str) -> User:
    ...

  @endpoint('POST /users/{id}')
  def update_user(self, auth: Credentials, id: str, attrs: UserAttrs) -> None:
    ...


def test_a_test_service():
  service = Service.from_class(ATestService)
  from .service import Endpoint
  assert service.authentication_methods == [OAuth2Bearer()]
  assert service.endpoints == [
    Endpoint(
      name='get_user',
      method='GET',
      path=Path('/users/{id}'),
      args={
        'auth': Argument(ParamKind.auth, NotSet.Value, None, Credentials),
        'id': Argument(ParamKind.path, NotSet.Value, None, str),
      },
      return_type=User,
      authentication_methods=[Basic(), NoAuthenticationMethod()],
    ),
    Endpoint(
      name='update_user',
      method='POST',
      path=Path('/users/{id}'),
      args={
        'auth': Argument(ParamKind.auth, NotSet.Value, None, Credentials),
        'id': Argument(ParamKind.path, NotSet.Value, None, str),
        'attrs': Argument(ParamKind.body, NotSet.Value, None, UserAttrs),
      },
      return_type=None,
      authentication_methods=[],
    ),
  ]
