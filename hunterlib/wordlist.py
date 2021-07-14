from collections.abc import Iterable

from nltk.corpus import wordnet as wn
from nltk.corpus.reader import Synset
from pydantic import BaseModel

"""Utilities for generating and interacting with word lists."""


def synset_to_str(s: Synset) -> str:
    return s.lemma_names()[0]


def words(syn: str) -> Iterable[str]:
    """Convert a wordnet synset reference to a list of possible synsets"""
    base: Synset = wn.synset(syn)
    tree = base.tree(lambda s: s.hyponyms())
    return {synset_to_str(s) for s in flatten(tree)}


class PartOfSpeech:
    ADJECTIVE = {synset_to_str(s) for s in wn.all_synsets('a')}
    NOUN = {synset_to_str(s) for s in wn.all_synsets('n')}
    ADVERB = {synset_to_str(s) for s in wn.all_synsets('r')}
    VERB = {synset_to_str(s) for s in wn.all_synsets('v')}


def flatten(items: Iterable, f=lambda i: True) -> Iterable:
    """
    Recursively flattens an arbitrary mess of lists, tuples, and generators into a single layer of iterable.

    >>> list(flatten([1,2,3,4]))
    [1, 2, 3, 4]
    >>> list(flatten(('a', 'bd', 'c', [1,2,3,4])))
    ['a', 'bd', 'c', 1, 2, 3, 4]
    """
    for el in items:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes, BaseModel, dict)):
            yield from flatten(el)
        elif f(el):
            yield el
