
from ._endpoint import Path


def test_parse_path():
  assert str(Path('/foo/bar')) == '/foo/bar'
  assert str(Path('/foo/{bar:path}/spam')) == '/foo/{bar:path}/spam'
  assert Path('/foo/{bar}').parameters == {'bar': None}
  assert Path('/foo/{bar}/{spam:path}').parameters == {'bar': None, 'spam': 'path'}
