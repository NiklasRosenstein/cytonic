
import dataclasses
import typing as t
from pathlib import Path

from ._module import ModuleConfig, load_module


@dataclasses.dataclass
class Project:

  modules: dict[str, ModuleConfig] = dataclasses.field(default_factory=dict)

  def add(self, module_name: str, config: ModuleConfig | dict[str, t.Any] | str | Path) -> None:
    if not isinstance(config, ModuleConfig):
      config = load_module(config)
    if module_name in self.modules:
      raise ValueError(f'module {module_name!r} already in project')
    self.modules[module_name] = config
