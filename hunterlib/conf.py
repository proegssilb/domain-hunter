import re

from pydantic import BaseModel

from hunterlib.models import Bias, ScoreWeight


class NameGuppyConfig(BaseModel):
    enable: bool = False
    cache_loc: str = '~/.domain-hunter/cache/nameguppy'


class NamecheapConfig(BaseModel):
    enable: bool = True
    cache_loc: str = '~/.domain-hunter/cache/namecheap'


class RunConfig(BaseModel):
    word_list: set[str] = set()
    tld_list: set[str] = set()

    word_filters: set[re.Pattern] = set()
    tld_filters: set[re.Pattern] = set()
    domain_filters: set[re.Pattern] = set()

    word_biases: set[Bias] = set()
    tld_biases: set[Bias] = set()
    domain_biases: set[Bias] = set()

    score_weights: set[ScoreWeight] = set()

    name_guppy_conf: NameGuppyConfig
    namecheap_conf: NamecheapConfig

    class Config:
        arbitrary_types_allowed = True
