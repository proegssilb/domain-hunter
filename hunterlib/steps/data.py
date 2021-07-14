from pydantic import BaseModel, constr, conint
from pydantic.dataclasses import dataclass


class ScoredWord(BaseModel):
    word: constr(strip_whitespace=True, to_lower=True, min_length=1, regex=r'\w*')
    score: conint(ge=1, le=10)


@dataclass
class WordCombo:
    concatenated: str
    source: tuple[ScoredWord]
    score: float

    def __init__(self, concated, source, score=None):
        self.concatenated = concated
        self.source = source
        self.score = score or self.score_words(source)

    @staticmethod
    def score_words(words: tuple[ScoredWord]):
        word_scores = tuple(w.score for w in words)
        num_words = len(words) + 1
        return sum(word_scores) / (10 ** num_words)
