from pydantic import BeforeValidator
from typing import Tuple, Any, Annotated, Optional, TypeAlias
import yarl

def parse_authority(s: Any) -> Optional[Tuple[str, str, int]]:
  if not s or not isinstance(s, str):
    return None
  
  # Clean up parentheses
  clean_s = s.strip('()')
  
  # Split from the right once to grab the year
  parts = [p.strip() for p in clean_s.rsplit(',', 1)]
  if len(parts) < 2:
    return None
  
  name_part, year_str = parts[0], parts[1]
  
  # Further split the name part to separate Last Name and Initials
  # For 'Naumann, JA; Naumann, JF', we keep it as one "Author" string
  if ',' in name_part:
    # Just grab the last name and initials if possible, or keep as is
    name_split = [p.strip() for p in name_part.split(',', 1)]
    last_name = name_split[0]
    initials = name_split[1] if len(name_split) > 1 else ""
  else:
    last_name = name_part
    initials = ""
  
  return last_name, initials, int(year_str)

Authority: TypeAlias = Annotated[Tuple[str, str, int], BeforeValidator(parse_authority)]
URL: TypeAlias = Annotated[yarl.URL, BeforeValidator(lambda x: yarl.URL(x) if x is not None else None)]