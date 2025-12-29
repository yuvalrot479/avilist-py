import pytest
from pathlib import Path
from avilist import AviListShort, AviListExtended, read_parquet, read_checklist

# Configuration
DIRECTORY = Path.cwd() / 'data'
SHORT_VERSION = 'AviList-v2025-11Jun-short'
EXTENDED_VERSION = 'AviList-v2025-11Jun-extended'

@pytest.mark.parametrize("method, version, fn, arg", [
    ('fetch', 'extended', AviListExtended, None),
    ('fetch', 'short',    AviListShort,    None),
    ('xlsx',  'extended', read_checklist,  DIRECTORY / f'{EXTENDED_VERSION}.xlsx'),
    ('xlsx',  'short',    read_checklist,  DIRECTORY / f'{SHORT_VERSION}.xlsx'),
    ('pq',    'extended', read_parquet,    DIRECTORY / f'{EXTENDED_VERSION}.parquet'),
    ('pq',    'short',    read_parquet,    DIRECTORY / f'{SHORT_VERSION}.parquet'),
], ids=[
    "extended-fetch", "short-fetch", 
    "extended-xlsx", "short-xlsx", 
    "extended-parquet", "short-parquet"
])
def test_avilist_read_performance(benchmark, method, version, fn, arg):
    """
    Benchmarks the reading and iteration performance of AviList formats.
    """
    def run_test():
        # Handle both class instantiation and function calls
        al = fn(arg) if arg is not None else fn()
        
        # Exhaust the generator to measure full read/parse time
        count = 0
        for _ in al.find():
            count += 1
        return count

    # Run the benchmark
    item_count = benchmark(run_test)
    
    # Basic sanity check to ensure data was actually read
    assert item_count > 0