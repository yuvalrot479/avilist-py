from pydantic import (
  BaseModel,
  ConfigDict,
  model_validator
)
from typing import (
  Any,
  Optional,
  TypedDict,
  Union,
)
import pandas as pd
from .aliases import *

# NOTE https://www.avilist.org/wp-content/uploads/2025/06/AviList_v2025_metadata_11Jun.pdf

class AviListQuery(TypedDict, total=False):
  order: str
  family: str
  family_english_name: str
  genus: str
  epithet: str
  subspecies: str
  scientific_name: str
  common_name: str
  protonym: str
  region: str

class AviListLeanRecord(BaseModel):
  model_config = ConfigDict(arbitrary_types_allowed=True)
  
  scientific_name: str
  sequence: int
  taxon_rank: str
  family: Optional[str] = None
  order: Optional[str] = None
  protonym: Optional[str] = None
  english_name_avilist: Optional[str] = None

  @property
  def common_name(self) -> Optional[str]:
    return self.english_name_avilist

  @property
  def genus(self) -> str:
    return self.scientific_name.split(' ')[0]
  
  @property
  def epithet(self) -> str:
    return self.scientific_name.split(' ')[1]
  
  @property
  def subspecies(self) -> Optional[str]:
    try:
      return self.scientific_name.split(' ')[-1]
    except IndexError:
      return None

  @property
  def binomial(self) -> str:
    return self.scientific_name

  @model_validator(mode='before')
  @classmethod
  def transform_and_clean(cls, data: Any) -> Any:
    if not isinstance(data, dict):
      return data
    return {k: (None if pd.isna(v) else v) for k, v in data.items()}

class AviListShortRecord(AviListLeanRecord):
  authority: Optional[Authority] = None
  avibase_id: Optional[str] = None
  bibliographic_details: Optional[str] = None
  decision_summary: Optional[str] = None
  extinct_or_possibly_extinct: Optional[Union[bool, str]] = None
  family_english_name: Optional[str] = None
  iucn_red_list_category: Optional[str] = None
  species_range: Optional[str] = None

class AviListExtendedRecord(AviListShortRecord):
  birdlife_datazone_url: Optional[URL] = None
  birds_of_the_world_url: Optional[URL] = None
  english_name_birdlife_v9: Optional[str] = None
  english_name_clements_v2024: Optional[str] = None
  gender_of_genus: Optional[str] = None
  original_description_url: Optional[URL] = None
  proposal_number: Optional[str] = None
  species_code_cornell_lab: Optional[str] = None
  title_of_original_description: Optional[str] = None
  type_locality: Optional[str] = None
  type_species_of_genus: Optional[str] = None

  @property
  def common_name(self) -> Optional[str]:
    return (
      self.english_name_avilist or 
      self.english_name_clements_v2024 or 
      self.english_name_birdlife_v9
    )