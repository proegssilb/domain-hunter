import logging
import re

from pydantic import BaseModel, conset, constr

from hunterlib.models import Bias, ScoreWeight


class NameGuppyConfig(BaseModel):
    enable: bool = False
    cache_loc: str = '~/.domain-hunter/cache/nameguppy'


class NamecheapConfig(BaseModel):
    enable: bool = True
    cache_loc: str = '~/.domain-hunter/cache/namecheap'


class RunConfig(BaseModel):
    word_list: conset(constr(min_length=1, to_lower=True), min_items=1) = set('a')
    tld_list: conset(constr(min_length=1, to_lower=True), min_items=1) = set('com')

    word_filters: set[re.Pattern] = {re.compile(r'\w{1,32}')}
    tld_filters: set[re.Pattern] = {re.compile(r'\w{1,5}')}
    domain_filters: set[re.Pattern] = {re.compile(r'.{1,32}')}

    word_biases: set[Bias] = set()
    tld_biases: set[Bias] = set()
    domain_biases: set[Bias] = set()

    score_weights: set[ScoreWeight] = set()

    name_guppy_conf: NameGuppyConfig
    namecheap_conf: NamecheapConfig

    class Config:
        arbitrary_types_allowed = True


class WordFilter(logging.Filter):
    def __init__(self, word=None, words=None):
        super().__init__()
        self.words = set()
        if word:
            self.words.add(word)
        if words:
            self.words.update(words)

    def filter(self, record: logging.LogRecord) -> bool:
        return getattr(record, 'word', None) in self.words or self.words.intersection(getattr(record, 'words', ()))
