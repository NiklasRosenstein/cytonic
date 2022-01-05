
""" Runtime decorators for representing server side APIs and other runtime internals. """

from ._authentication import authentication, AuthenticationAnnotation, AuthenticationMethod, BearerToken, BasicAuth
from ._endpoint import endpoint, EndpointAnnotation
from ._service import Endpoint, Service
from ._handler_mixin import Authorization, HandlerMixin
