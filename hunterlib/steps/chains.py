import logging
import re
from dataclasses import dataclass
from heapq import heappush, heappop
from typing import Iterable, TypeVar, Callable

from hunterlib.conf import RunConfig
from hunterlib.models import Bias
from hunterlib.steps.data import ScoredWord, WordCombo

logger = logging.getLogger("domain-hunter.chains")


def generate_word_chain(config: RunConfig) -> Iterable[WordCombo]:
    filters = config.word_filters
    word_list = config.word_list
    biases = config.word_biases

    word_list = set(filter_chain(filters, word_list, lambda x: x))

    chain = generate_chain(word_list, biases, 10)
    return filter_chain(filters, chain, lambda wc: wc.concatenated)


def process_word(biases, word: str) -> ScoredWord:
    matching_biases = [b for b in biases if b.pattern in word]
    score = 3 + sum(b.adjust for b in matching_biases)
    score = score - len(word) / 100
    log_msg = "Generated score for word."
    logger.debug(
        log_msg,
        extra={
            "word": word,
            "score": score,
            "biases": matching_biases,
        },
    )
    return ScoredWord(word=word, score=score)


T = TypeVar("T")


def generate_chain(
    source_list: set[str], biases: set[Bias], max_repeat: int
) -> Iterable[WordCombo]:
    biased: list[ScoredWord] = [process_word(biases, w) for w in source_list]
    biased.sort(key=lambda t: t.score, reverse=True)
    biased: tuple[ScoredWord] = tuple(biased)

    return search_combos(biased, max_repeat)


@dataclass(order=True)
class QueueNode:
    score: float
    data: tuple[int]

    def __init__(self, data: tuple[int], score: float):
        self.data = data
        self.score = -1 * score


def search_combos(source: tuple[ScoredWord], max_repeat: int) -> Iterable[WordCombo]:
    def get_words(indexes: tuple[int]) -> tuple[ScoredWord]:
        rv: list[ScoredWord] = list()
        for i in indexes:
            rv.append(source[i])
        return tuple(rv)

    if len(source) == 0:
        return ()
    if len(source) == 1:
        sw = source[0]
        yield WordCombo(sw.word, (sw,))
    else:
        heap = []
        starter_node = QueueNode((0,), source[0].score)
        heappush(heap, starter_node)

        while len(heap) > 0:
            next_node = heappop(heap)
            words = get_words(next_node.data)
            log_msg = "Yielding words from search_combos"
            logger.debug(
                log_msg, extra={"words": str(words), "priority": next_node.score}
            )
            yield WordCombo("".join(w.word for w in words), words)
            last_index = next_node.data[-1]
            if len(next_node.data) < max_repeat and next_node.data[-1] + 1 < len(
                source
            ):
                future_add = next_node.data + (last_index + 1,)
                score = WordCombo.score_words(get_words(future_add))
                heappush(heap, QueueNode(future_add, score))
            if last_index + 1 < len(source):
                future_iterate = next_node.data[:-1] + (last_index + 1,)
                score = WordCombo.score_words(get_words(future_iterate))
                heappush(heap, QueueNode(future_iterate, score))


def filter_chain(
    filter_pattern: set[re.Pattern], chain: Iterable[T], conversion: Callable[[T], str]
) -> Iterable[T]:
    # This is a filter and a map with extra steps. The imperative version is easier to debug.
    for item in chain:
        data = conversion(item)
        if all(p.match(data) for p in filter_pattern):
            logger.debug(
                "Word matched all filters",
                extra={"word": data, "filters": filter_pattern},
            )
            yield item
        else:
            logger.debug(
                "Word discarded via filters",
                extra={"word": str(data), "filters": filter_pattern},
            )


def generate_tld_chain(config: RunConfig):
    biases = config.tld_biases
    word_list = config.tld_list
    filters = config.tld_filters

    filtered_list = set(filter_chain(filters, word_list, lambda x: x))
    raw_chain = generate_chain(filtered_list, biases, 1)
    return filter_chain(filters, raw_chain, lambda wc: wc.concatenated)
