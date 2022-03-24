
from cytonic.model import HttpPath


def test_parse_http_path():
  assert str(HttpPath('GET /foo/bar')) == 'GET /foo/bar'
  assert str(HttpPath('POST /foo/{bar:path}/spam')) == 'POST /foo/{bar:path}/spam'
  assert HttpPath('GET /foo/{bar}').parameters == {'bar': None}
  assert HttpPath('GET /foo/{bar}/{spam:path}').parameters == {'bar': None, 'spam': 'path'}
