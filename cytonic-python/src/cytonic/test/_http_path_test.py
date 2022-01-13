
from cytonic.model import HttpPath


def test_parse_http_path():
  assert str(HttpPath('/foo/bar')) == '/foo/bar'
  assert str(HttpPath('/foo/{bar:path}/spam')) == '/foo/{bar:path}/spam'
  assert HttpPath('/foo/{bar}').parameters == {'bar': None}
  assert HttpPath('/foo/{bar}/{spam:path}').parameters == {'bar': None, 'spam': 'path'}
