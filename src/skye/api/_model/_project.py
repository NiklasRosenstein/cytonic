
import typing as t
from pathlib import Path
  
from ._module import ModuleConfig, load_module


class Project:

  def __init__(self) -> None:
    self._modules: dict[str, ModuleConfig] = {}

  def add(self, module_name: str, config: ModuleConfig | dict[str, t.Any] | str | Path) -> None:
    if not isinstance(config, ModuleConfig):
      config = load_module(config)
    if module_name in self._modules:
      raise ValueError(f'module {module_name!r} already in project')
    self._modules[module_name] = config
