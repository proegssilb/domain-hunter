from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict

from pydantic import BaseModel
from pydantic import confloat
from pydantic import constr


class ScoredWord(BaseModel):
    word: constr(strip_whitespace=True, to_lower=True, min_length=1, regex=r"\w*")
    score: confloat(ge=-10, le=10)


@dataclass
class WordCombo:
    concatenated: str
    source: tuple[ScoredWord]
    score: float

    def __init__(self, concatenated, source, score=None):
        self.concatenated = concatenated
        self.source = source
        self.score = score or self.score_words(source)

    @staticmethod
    def score_words(words: tuple[ScoredWord]):
        word_scores = tuple(w.score + 20 for w in words)
        num_words = len(words) + 1
        return sum(word_scores) / (10 ** num_words)

    def words(self):
        return tuple(sw.word for sw in self.source)


@dataclass(init=True, repr=True)
class Domain:
    domain: str
    words: tuple[ScoredWord]
    tld: ScoredWord
    score: float = field(init=False)
    plugin_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        self.score = WordCombo.score_words(self.words + (self.tld,)) * 100

    def as_words(self):
        return tuple(sw.word for sw in self.words)
