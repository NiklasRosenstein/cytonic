
from cytonic.model import Datatype


def test_parse_datatype():
  assert Datatype.parse('string') == Datatype('string')
  assert Datatype.parse('list[string]') == Datatype('list', [Datatype('string')])
  assert Datatype.parse('list[map[string, set[optional[integer]]]]') == \
    Datatype('list', [
      Datatype('map', [
        Datatype('string'),
        Datatype('set', [
          Datatype('optional', [
            Datatype('integer')
          ])
        ])
      ])
    ])
