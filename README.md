# AviList Wrapper for Python

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![Pandas](https://img.shields.io/badge/data-Pandas-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Pydantic](https://img.shields.io/badge/validation-Pydantic-red)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intuitive, type-safe Python wrapper for the [AviList global bird checklist](https://www.avilist.org/checklist);  
Retrieve rich avian taxonomic data with ease via simple yet powerful querying.

## Disclaimer
This project is an open-source tool intended for research and educational purposes;  
This project is provided **AS IS** without any warranty;  
This project is not officially affiliated with nor endorsed by [AviList](https://www.avilist.org/about/);  
Users are responsible for adhering to the [AviList Terms of Reference](https://www.avilist.org/tor/).  

## Quickstart

### Installation
#### PIP
```bash
pip install avilist-py
```
#### PDM
```bash
pdm add avilist-py
```
#### Conda (currently not supported)
```bash
conda install avilist-py
```
### Basic usage example
```py
from avilist import AviListShort

al = AviListShort()

records = al.find(genus='corvus') # Generator of all records with genus "corvus"
first = next(gen) # If nothing found, this will raise StopIteration

for record in al.find(genus='acridotheres', epithet='tristis'):
  print(record.sequence)    # 26373
  print(record.common_name) # 'Common Myna'
  print(record.authority)   # ('Linnaeus', 'C', 1766)

```

## Loading data (in-memory)

By default, instantiating an `AviList` class will not load any data unto the object.  
Data will be loaded either when explicitly calling `.load()`, or implicitly by calling one of the querying functions (e.g. `.find()`).  
Data may completely removed from memory manually by calling `.unload()`.

## Reading from files

Even though fetching the files (8.7MB) is quite quick, you may read a local file to save some overhead;  You may do so with the supplied read utility functions.  

IMPORTANT - Ensure the file name and suffix were **NOT** modified after download / persitance; See example below for valid file names.

NOTE - Checklist files should only be read AS-IS, you may download them from the [official site](https://www.avilist.org/checklist), then load them manually.  

NOTE - Parquet files should only be read if they were persisted by an `AviList` class via `.persist()`; Do not try to load some random parquet file!

```py
from avilist import AviListShort, read_checklist, read_parquet

al = AviListShort() 
# Slowest - pulls remote data from avilist.org

al = read_checklist('/path/to/AviList-v2025-11Jun-short.xlsx') 
# Faster

al = read_parquet('path/to/AviList-v2025-11Jun-short.parquet') 
# Fastest!
```

## Record shape comparison by version

### Short version
```py
from avilist import AviListShort

al = AviListShort()

for record in al.find(genus='acrocephalus', epithet='melanopogon'):
  print(record)
```
```py
AviListShortRecord(
    scientific_name='Acrocephalus melanopogon',
    sequence=22252,
    taxon_rank='species',
    family='Acrocephalidae',
    order='Passeriformes',
    protonym=None,
    english_name_avilist='Moustached Warbler',
    authority=('Temminck', 'CJ', 1823),
    avibase_id='avibase-E1559C49',
    bibliographic_details="Nouveau recueil de planches coloriées d'oiseaux, pour servir de suite et de complément aux planches enluminées de Buffon livr.41, 
vol.3 pl.245 fig.2,text",
    decision_summary=None,
    extinct_or_possibly_extinct=False,
    family_english_name='Reed Warblers and Allies',
    iucn_red_list_category='LC',
    species_range=None
)
```

### Extended version
```py
from avilist import AviListExtended

al = AviListExtended()

for record in al.find(genus='acrocephalus', epithet='melanopogon'):
  print(record)
```
```py
AviListExtendedRecord(
    scientific_name='Acrocephalus melanopogon',
    sequence=22252,
    taxon_rank='species',
    family='Acrocephalidae',
    order='Passeriformes',
    protonym='Sylvia melanopogon',
    english_name_avilist='Moustached Warbler',
    authority=('Temminck', 'CJ', 1823),
    avibase_id='avibase-E1559C49',
    bibliographic_details="Nouveau recueil de planches coloriées d'oiseaux, pour servir de suite et de complément aux planches enluminées de Buffon livr.41, 
vol.3 pl.245 fig.2,text",
    decision_summary=None,
    extinct_or_possibly_extinct=False,
    family_english_name='Reed Warblers and Allies',
    iucn_red_list_category='LC',
    species_range=None,
    birdlife_datazone_url=URL('https://datazone.birdlife.org/species/factsheet/22714693'),
    birds_of_the_world_url=URL('https://birdsoftheworld.org/bow/species/mouwar1/'),
    english_name_birdlife_v9='Moustached Warbler',
    english_name_clements_v2024='Moustached Warbler',
    gender_of_genus=None,
    original_description_url=URL('https://www.biodiversitylibrary.org/item/112979#page/307/mode/1up'),
    proposal_number=None,
    species_code_cornell_lab='mouwar1',
    title_of_original_description=None,
    type_locality="'campagnes pres de Rome.",
    type_species_of_genus=None
)
```

### Lean records (compatible with both versions)
```py
from avilist import AviListShort, AviListExtended
import random

al = random.choice([AviListShort, AviListExtended])()
for record in al.find(genus='acrocephalus', epithet='melanopogon', lean=True):
  print(record)

```
```py
AviListLeanRecord(
    scientific_name='Acrocephalus melanopogon',
    sequence=22252,
    taxon_rank='species',
    family='Acrocephalidae',
    order='Passeriformes',
    protonym=None,
    english_name_avilist='Moustached Warbler'
)
```