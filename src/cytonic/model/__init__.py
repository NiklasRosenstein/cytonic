
""" Defines the data model for the YAML configuration. """

from ._endpoint import ParamKind, ArgumentConfig, EndpointConfig
from ._error import ErrorConfig
from ._http_path import HttpPath
from ._module import ModuleConfig
from ._project import Project
from ._type import TypeConfig, FieldConfig, ValueConfig
from ._auth import AuthenticationConfig, Oauth2Bearer, BasicAuth, NoAuth
