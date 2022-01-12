
import dataclasses
import typing as t

from nr.util.singleton import NotSet

from cytonic.description import (
  authentication, endpoint, service, ArgumentDescription, EndpointDescription, ServiceDescription
)
from cytonic.model import OAuth2Bearer, BasicAuth, NoAuth, ParamKind, HttpPath
from cytonic.runtime import Credentials


@dataclasses.dataclass
class User:
  id: str
  name: str
  age: int


@dataclasses.dataclass
class UserAttrs:
  name: str
  age: int


@service('ATest')
@authentication(OAuth2Bearer())
class ATestService:

  @authentication(BasicAuth())
  @authentication(NoAuth())
  @endpoint('GET /users/{id}')
  def get_user(self, auth: Credentials, id: str) -> User:
    ...

  @endpoint('POST /users/{id}')
  def update_user(self, auth: Credentials, id: str, attrs: UserAttrs) -> None:
    ...

  @endpoint('GET /users')
  def get_users(self, auth: Credentials, search_text: str | None = None) -> None:
    ...


def test_a_test_service():
  service = ServiceDescription.from_class(ATestService)
  assert service.name == 'ATest'
  assert service.authentication_methods == [OAuth2Bearer()]
  assert service.endpoints == [
    EndpointDescription(
      name='get_user',
      method='GET',
      path=HttpPath('/users/{id}'),
      args={
        'auth': ArgumentDescription(ParamKind.auth, NotSet.Value, None, Credentials),
        'id': ArgumentDescription(ParamKind.path, NotSet.Value, None, str),
      },
      return_type=User,
      authentication_methods=[BasicAuth(), NoAuth()],
      async_=False,
    ),
    EndpointDescription(
      name='get_users',
      method='GET',
      path=HttpPath('/users'),
      args={
        'auth': ArgumentDescription(ParamKind.auth, NotSet.Value, None, Credentials),
        'search_text': ArgumentDescription(ParamKind.query, None, None, t.Optional[str]),
      },
      return_type=None,
      authentication_methods=[],
      async_=False,
    ),
    EndpointDescription(
      name='update_user',
      method='POST',
      path=HttpPath('/users/{id}'),
      args={
        'auth': ArgumentDescription(ParamKind.auth, NotSet.Value, None, Credentials),
        'id': ArgumentDescription(ParamKind.path, NotSet.Value, None, str),
        'attrs': ArgumentDescription(ParamKind.body, NotSet.Value, None, UserAttrs),
      },
      return_type=None,
      authentication_methods=[],
      async_=False,
    ),
  ]
