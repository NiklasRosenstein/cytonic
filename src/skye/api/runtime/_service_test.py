
import dataclasses
from nr.pylang.utils.singletons import NotSet
from ._authentication import authentication
from ._endpoint import endpoint, Path, ParamKind
from ._service import Argument, Service


@dataclasses.dataclass
class User:
  id: str
  name: str
  age: int


@dataclasses.dataclass
class UserAttrs:
  name: str
  age: int


@authentication('oauth2_bearer')
class ATestService:

  @authentication('basic')
  @authentication('none')
  @endpoint('GET /users/{id}')
  def get_user(self, id: str) -> User:
    ...

  @endpoint('POST /users/{id}')
  def update_user(self, id: str, attrs: UserAttrs) -> None:
    ...


def test_a_test_service():
  service = Service.from_class(ATestService)
  from ._authentication import OAuth2BearerAuthenticationMethod, BasicAuthenticationMethod, NoAuthenticationMethod
  from ._service import Endpoint
  assert service.authentication_methods == [OAuth2BearerAuthenticationMethod()]
  assert service.endpoints == [
    Endpoint(
      name='get_user',
      method='GET',
      path=Path('/users/{id}'),
      args={'id': Argument(ParamKind.path, NotSet.Value, None, str)},
      return_type=User,
      authentication_methods=[BasicAuthenticationMethod(), NoAuthenticationMethod()],
    ),
    Endpoint(
      name='update_user',
      method='POST',
      path=Path('/users/{id}'),
      args={
        'id': Argument(ParamKind.path, NotSet.Value, None, str),
        'attrs': Argument(ParamKind.body, NotSet.Value, None, UserAttrs),
      },
      return_type=None,
      authentication_methods=[],
    ),
  ]
