import pandas as pd
from pathlib import Path
from typing import Union, Optional
from io import BytesIO
import requests
import re
from typing import (
  Unpack,
  List,
  Dict,
  Any,
 )
from functools import partial, wraps
from .schemas import *
from warnings import warn
from abc import ABC, abstractmethod

def ensure_loaded(func):
  @wraps(func)
  def wrapper(self, *args, **kwargs):
    if self._df is None:
      warn(f"Data was not loaded yet; Automatically invoking .load() for {func.__name__}")
      self.load()
    return func(self, *args, **kwargs)
  return wrapper

CHECKLIST_URL = 'https://www.avilist.org/checklist'
UPLOADS_URL = 'https://www.avilist.org/wp-content/uploads'
COLUMN_REMAPPING = {
  'avibaseid': 'avibase_id',
  'range': 'species_range',
}
COLUMN_DTYPES = {
  "sequence": "int64",
  "taxon_rank": "category",  # Limited options: genus, species, etc.
  "order": "string",
  "family": "string",
  "family_english_name": "string",
  "scientific_name": "string",
  "authority": "string",
  "bibliographic_details": "string",
  "english_name_avilist": "string",
  "english_name_clements_v2024": "string",
  "english_name_birdlife_v9": "string",
  "proposal_number": "string",   # Force string to handle "N-70"
  "decision_summary": "string",
  "species_range": "string",
  "extinct_or_possibly_extinct": "boolean", # Typically Yes/No or True/False
  "iucn_red_list_category": "category",     # LC, VU, EN, etc.
  "birdlife_datazone_url": "string",
  "species_code_cornell_lab": "string",
  "birds_of_the_world_url": "string",
  "avibase_id": "string",
  "gender_of_genus": "string",
  "type_species_of_genus": "string",
  "type_locality": "string",
  "title_of_original_description": "string",
  "original_description_url": "string",
  "protonym": "string",
  "binomial_helper": "string"
}

class AviList(ABC):
  _version: str
  _df_promise: partial[pd.DataFrame]
  _df: Optional[pd.DataFrame] = None

  @classmethod
  def _process_raw_df(cls, df: pd.DataFrame):
    """Process a raw DataFrame:
    - Apply uniform column naming scheme (snake case)
    - ...

    :param df: _description_
    :return: _description_
    """
    # Rename columns
    df.columns = [
      re.sub(r'[\W_]+', '_', col.strip().lower()).strip('_') 
      for col in df.columns
    ]
    df = df.rename(columns=COLUMN_REMAPPING)

    for col, dtype in COLUMN_DTYPES.items():
      if col in df.columns:
        if dtype == "boolean":
          # Handle Excel-specific boolean quirks
          df[col] = df[col].map({'Yes': True, 'No': False}).fillna(False)
        else:
          df[col] = df[col].astype(dtype) # type: ignore
    
    
    f = lambda x: " ".join(x.split()[:2]).lower() if isinstance(x, str) else None
    df['binomial_helper'] = (
        df['scientific_name']
        .str.split()
        .str[:2]
        .str.join(' ')
        .str.lower()
        .astype('string')
    )
    
    return df

  @classmethod
  def _fetch_from_avilist(cls, resource: str) -> pd.DataFrame:
    url = f'{UPLOADS_URL}/{resource}'
    headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    
    df =  pd.read_excel(BytesIO(resp.content))
    df = cls._process_raw_df(df)
    return df

  @classmethod
  def _load_xlsx(cls, data: Union[Path, BytesIO]):
    df = pd.read_excel(data)
    df = cls._process_raw_df(df)
    return df

  def load(self) -> None:
    self._df = self._df_promise()

  def unload(self) -> None:
    self._df = None

  def persist(self) -> None:
    if self._df is not None:
      file_name = f'{self._version}.parquet'
      # df = self._df
      # object_cols = df.select_dtypes(include=['object']).columns
      df = self._df
      self._df.to_parquet(
        file_name,
        engine='pyarrow',
        index=False,
        compression='snappy'
      )
  
  @abstractmethod
  def _build_query_set(self, **kwargs) -> pd.DataFrame: ...

  @classmethod
  @abstractmethod
  def from_parquet(cls, path: Path): ...

  @classmethod
  @abstractmethod
  def from_checklist(cls, path: Path): ...

class AviListShort(AviList):
  def __init__(self):
    self._version = 'AviList-v2025-11Jun-short'
    self._df_promise = partial(self._fetch_from_avilist, f'/2025/06/{self._version}.xlsx')

  @classmethod
  def from_parquet(cls, path: Path):
    if not path.suffix.endswith('parquet'):
      raise ValueError(path)
    
    elif not (path.stem.startswith('AviList-') and path.stem.endswith('-short')):
      raise ValueError(path)
    
    o = cls()
    o._version = path.stem
    o._df_promise = partial(pd.read_parquet, path)
    return o

  @classmethod
  def from_checklist(cls, path: Path):
    if not path.suffix.endswith('xlsx'):
      raise ValueError(
        f'Invalid file type ({path.suffix}); Ensure the file name was NOT modified after download: {CHECKLIST_URL}'
      )
    elif not path.stem.endswith('-short'):
      raise ValueError(
        f'Unexpected .xlsx file name; Ensure the file name was NOT modified after download: {CHECKLIST_URL}'
      )
    
    o = cls()
    o._df_promise = partial(cls._load_xlsx, path)
    
    return o

  def _build_query_set(self, **kwargs) -> pd.DataFrame:
    if self._df is None:
      raise RuntimeError()
    
    df = self._df

    # 1. Historical & Taxonomic Binomial Search
    if genus := kwargs.get('genus'):
      mask = df['scientific_name'].str.lower().str.startswith(genus.lower())
      df = df[mask]
    
    if epithet := kwargs.get('epithet'):
      # Search for the epithet (usually the 2nd word)
      mask = df['scientific_name'].str.lower().str.contains(epithet.lower())
      df = df[mask]

    if subspecies := kwargs.get('subspecies'):
      mask1 = df['scientific_name'].str.lower().str.contains(subspecies.lower())
      mask2 = df['taxon_rank'].str.lower() == 'subspecies'
      df = df[mask1 & mask2]

    # 2. Common Name Search
    if common_name := kwargs.get('common_name'):
        cn_lower = common_name.lower()
        cn_mask = df['english_name_avilist'].str.lower() == cn_lower
        df = df[cn_mask]

    # 3. Direct Mappings
    direct_mappings = {"order": "order", "family": "family", "family_english_name": "family_english_name"}
    for query_key, col_name in direct_mappings.items():
        if (v := kwargs.get(query_key)) is not None:
            df = df[df[col_name].str.lower() == v.lower()]
    
    if species_range := kwargs.get('species_range'):
       df = df[df['species_range'].fillna('').str.contains(species_range, case=False)]

    return df
  
  @ensure_loaded
  def find(self, lean: bool = False, limit: Optional[int] = None, **kwargs: Unpack[AviListQuery]):
    df = self._build_query_set(**kwargs)
    records = df.to_dict('records')
    
    if limit:
       records = records[:limit]
    
    for record in records:
      if lean:
        yield AviListLeanRecord.model_validate(record)
      else:
        yield AviListShortRecord.model_validate(record)

class AviListExtended(AviList):
  def __init__(self):
    self._version = 'AviList-v2025-11Jun-extended'
    self._df_promise = partial(self._fetch_from_avilist, f'/2025/06/{self._version}.xlsx')

  @classmethod
  def from_parquet(cls, path: Path):
    if not path.suffix.endswith('parquet'):
      raise ValueError(path)
    
    elif not (path.stem.startswith('AviList-') and path.stem.endswith('-extended')):
      raise ValueError(path)
    
    o = cls()
    o._version = path.stem
    o._df_promise = partial(pd.read_parquet, path)
    return o

  @classmethod
  def from_checklist(cls, path: Path):
    if not path.suffix.endswith('xlsx'):
      raise ValueError(
        'Invalid file suffix; Ensure the file name was NOT modified after download: https://www.avilist.org/checklist'
      )
    elif not path.stem.endswith('-extended'):
      raise ValueError(
        'Invalid .xlsx file name; Ensure the file name was NOT modified after download: https://www.avilist.org/checklist'
      )
    
    o = cls()
    o._df_promise = partial(cls._load_xlsx, path)
    
    return o

  def _build_query_set(self, **kwargs) -> pd.DataFrame:
    if self._df is None:
      raise RuntimeError()
    
    df = self._df

    # 1. Historical & Taxonomic Binomial Search
    if genus := kwargs.get('genus'):
      mask = df['scientific_name'].str.lower().str.startswith(genus.lower())
      df = df[mask]
    
    if epithet := kwargs.get('epithet'):
      # Search for the epithet (usually the 2nd word)
      mask = df['scientific_name'].str.lower().str.contains(epithet.lower())
      df = df[mask]

    if subspecies := kwargs.get('subspecies'):
      mask1 = df['scientific_name'].str.lower().str.contains(subspecies.lower())
      mask2 = df['taxon_rank'].str.lower() == 'subspecies'
      df = df[mask1 & mask2]

    # 2. Common Name Search
    if common_name := kwargs.get('common_name'):
        cn_lower = common_name.lower()
        cn_mask = (
            df['english_name_avilist'].str.lower() == cn_lower) | \
            (df['english_name_clements_v2024'].str.lower() == cn_lower) | \
            (df['english_name_birdlife_v9'].str.lower() == cn_lower)
        df = df[cn_mask]

    # 3. Direct Mappings
    direct_mappings = {"order": "order", "family": "family", "family_english_name": "family_english_name"}
    for query_key, col_name in direct_mappings.items():
        if (v := kwargs.get(query_key)) is not None:
            df = df[df[col_name].str.lower() == v.lower()]
    
    if species_range := kwargs.get('species_range'):
       df = df[df['species_range'].fillna('').str.contains(species_range, case=False)]

    return df

  @ensure_loaded
  def find(self, lean: bool = False, limit: Optional[int] = None, **kwargs: Unpack[AviListQuery]):
    df = self._build_query_set(**kwargs)
    records = df.to_dict('records')
    
    if limit:
       records = records[:limit]
    
    for record in records:
      if lean:
        yield AviListLeanRecord.model_validate(record)
      else:
        yield AviListExtendedRecord.model_validate(record)

  @ensure_loaded
  def enrich_species_list(self, records: List[Dict[str, Any]]) -> Union[List[AviListExtendedRecord], List[AviListShortRecord]]:
    if self._df is None:
      raise RuntimeError('DataFrame not loaded; Call .load() before calling this function')

    if not records:
      return []
    input_df = pd.DataFrame.from_records([
      {
        'scientific_name': r['scientific_name'],
        'probability': r['threshold'],
      }
      for r in records
    ])
    merged_df = pd.merge(
      input_df,
      self._df,
      on='scientific_name',
      how='inner',
    )
    merged_df = merged_df.sort_values(by='probability', ascending=False)
    return [
      AviListExtendedRecord.model_validate(r)
      for r in merged_df.to_dict('records')
    ]