from avilist import AviListShort, AviListExtended
from typing import Union
from pathlib import Path

def read_checklist(path: Union[str, Path]) -> Union[AviListShort, AviListExtended]:
  if isinstance(path, str):
    path = Path(path)
  
  if not path.exists():
    raise FileNotFoundError()
  
  elif not (path.is_file() and path.suffix.endswith('xlsx')):
    raise ValueError()
  
  if path.stem.endswith('-short'):
    return AviListShort.from_checklist(path)
  
  elif path.stem.endswith('-extended'):
    return AviListExtended.from_checklist(path)
  
  else:
    raise ValueError(path)

def read_parquet(path: Union[str, Path]) -> Union[AviListShort, AviListExtended]:
  if isinstance(path, str):
    path = Path(path)
  
  if not path.exists():
    raise FileNotFoundError()
  
  elif not (path.is_file() and path.suffix.endswith('parquet')):
    raise ValueError()
  
  if path.stem.endswith('-short'):
    return AviListShort.from_parquet(path)
  elif path.stem.endswith('-extended'):
    return AviListExtended.from_parquet(path)
  else:
    raise ValueError(path)