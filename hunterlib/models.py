import os
import os.path
import re
from collections.abc import Iterable
from typing import Callable, Any

from pydantic import BaseModel, constr, confloat


class ListSource:
    def __init__(self, kind: type, data: Iterable):
        self._data = data
        self._kind = kind

    def __iter__(self):
        return map(self._kind, self._data)


class FileSource:
    def __init__(self, kind: Callable[[str], Any], filename: str):
        self._kind = kind
        self._filename = os.path.join(os.getcwd(), filename)

    def __iter__(self):
        with open(self._filename, 'r') as f:
            for line_raw in f:
                yield self._kind(line_raw.strip())


Filter = re.compile


class Bias(BaseModel):
    pattern: constr(min_length=1)
    adjust: confloat(ge=-2, le=2)

    class Config:
        allow_mutation = False

    def __hash__(self):
        return hash((self.pattern, self.adjust))


class ScoreWeight(BaseModel):
    query: str
    adjust: float
