
import dataclasses
import typing as t
from pathlib import Path

import databind.json
import yaml

from ._auth import AuthenticationConfig
from ._endpoint import EndpointConfig
from ._error import ErrorConfig
from ._type import TypeConfig


@dataclasses.dataclass
class ModuleConfig:

  #: The name of the service; this is used in several places in the generated code.
  name: str

  # Docstring for the service.
  docs: str | None = None

  #: The endpoints in the service.
  endpoints: dict[str, EndpointConfig] = dataclasses.field(default_factory=dict)

  #: A definition of types for this service.
  types: dict[str, TypeConfig] = dataclasses.field(default_factory=dict)

  #: Definition of error types.
  errors: dict[str, ErrorConfig] = dataclasses.field(default_factory=dict)

  #: Authentication configuration.
  auth: AuthenticationConfig | None = None


def load_module(config: dict[str, t.Any] | str | Path, filename: str | None = None) -> ModuleConfig:
  """ Loads a module configuration from a nested structure, YAML string or YAML file. """

  if isinstance(config, Path):
    return load_module(config.read_text(), filename=str(config))
  elif isinstance(config, str):
    return load_module(yaml.safe_load(config), filename=filename)

  return databind.json.load(config, ModuleConfig, filename=filename)
