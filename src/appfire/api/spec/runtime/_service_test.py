
from ._authentication import authentication
from ._endpoint import endpoint
from ._service import Service


@authentication('oauth2_bearer')
class ATestService:

  @authentication('basic')
  @authentication('none')
  @endpoint('GET /test/me')
  def a_test_endpoint(self) -> None:
    ...


def test_a_test_service():
  service = Service.from_class(ATestService)
  from ._authentication import OAuth2BearerAuthenticationMethod, BasicAuthenticationMethod, NoAuthenticationMethod
  from ._service import Endpoint
  assert service.authentication_methods == [OAuth2BearerAuthenticationMethod()]
  assert service.endpoints == [Endpoint(
    name='a_test_endpoint',
    method='GET',
    path='/test/me',
    authentication_methods=[BasicAuthenticationMethod(), NoAuthenticationMethod()],
  )]
