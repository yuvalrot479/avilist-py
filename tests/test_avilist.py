import pytest
from avilist import AviListExtended

@pytest.fixture
def client():
  """Fixture to initialize the AviList client once per test session."""
  return AviListExtended()

@pytest.mark.parametrize("filters", [
  {"genus": "corvus"},
  {"genus": "corvus", "epithet": "corone"},
  {"genus": "corvus", "epithet": "corone", "subspecies": "orientalis"}
])
def test_find_taxonomic_combinations(client, filters):
  limit = 5
  results = list(client.find(limit=limit, **filters))
  
  assert len(results) > 0
  assert len(results) <= limit

  for record in results:
    for key, val in filters.items():
      actual = getattr(record, key)
      assert actual is not None
      assert actual.lower() == val.lower()
