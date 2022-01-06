
import dataclasses


@dataclasses.dataclass
class AuthenticationConfig:

  #: The authentication method to use.
  type: str
