
import dataclasses
import typing as t

from databind.core.annotations import union


@dataclasses.dataclass
class OAuth2Bearer:
  header_name: str | None = None

  def __repr__(self) -> str:
    if self.header_name:
      return f'{type(self).__name__}(header_name={self.header_name!r})'
    else:
      return f'{type(self).__name__}()'


@dataclasses.dataclass
class BasicAuth:

  def __repr__(self) -> str:
    return f'{type(self).__name__}()'


@dataclasses.dataclass
class NoAuth:

  def __repr__(self) -> str:
    return f'{type(self).__name__}()'


AuthenticationConfig = t.Annotated[
  OAuth2Bearer | BasicAuth | NoAuth,
  union({
    'oauth2_bearer': OAuth2Bearer,
    'basic': BasicAuth,
    'none': NoAuth,
  }, style=union.Style.flat)
]
