import logging
from dataclasses import dataclass, field
from heapq import heappush, heappop
from itertools import chain, repeat
from typing import Iterable, List

from hunterlib.conf import RunConfig
from hunterlib.models import Bias
from hunterlib.steps.chains import filter_chain
from hunterlib.steps.data import WordCombo, Domain

logger = logging.getLogger('domain-hunter.domains')


@dataclass(init=True, eq=True, order=True)
class QueueNode:
    word_index: int = field(compare=False)
    tld_index: int = field(compare=False)
    domain: Domain = field(compare=False)
    score: float = field(init=False)

    def __post_init__(self):
        self.score = -1 * self.domain.score


def generate_domains(config: RunConfig, word_chain: Iterable[WordCombo], tld_chain: Iterable[WordCombo]):
    biases = config.domain_biases
    filters = config.domain_filters

    raw_chain = domain_combos(word_chain, tld_chain, biases)
    return filter_chain(filters, raw_chain, lambda d: d.domain)


def domain_combos(word_chain: Iterable[WordCombo], tld_chain: Iterable[WordCombo], biases: set[Bias]):
    def mk_domain(word_list: List[WordCombo], tld_list: tuple[WordCombo], word_idx: int, tld_idx: int) -> QueueNode:
        word = word_list[word_idx]
        tld = tld_list[tld_idx]
        domain_str = word.concatenated + '.' + tld.concatenated
        domain = Domain(domain_str, word.source, tld)
        for bias in biases:
            if bias.pattern in domain.domain:
                domain.score += bias.adjust
        return QueueNode(word_idx, tld_idx, domain)

    word_buffer = []
    words = iter(chain(word_chain, repeat(None)))
    tlds = tuple(tld_chain)
    if not tlds:
        raise ValueError("Given tld_chain had no objects. Check config.")
    queue: List[QueueNode] = []
    next_word = next(words)
    if next_word is not None:
        logger.debug('Doing initial domain word append',
                     extra={'words': next_word.words()})
        word_buffer.append(next_word)
    else:
        raise ValueError('Given tld_chain had no objects. Check config.')
    for i in range(len(tlds)):
        node = mk_domain(word_buffer, tlds, 0, i)
        heappush(queue, node)

    while len(queue) > 0:
        current_node = heappop(queue)
        logger.debug('Outputting domain', extra={
            'words': current_node.domain.as_words(),
            'domain_score': current_node.domain.score,
        })
        yield current_node.domain
        # Make sure that if there's going to be a next word, it's available.
        if current_node.word_index + 1 == len(word_buffer):
            next_word = next(words)
            if next_word is not None:
                logger.debug('Queueing up next word',
                             extra={'words': next_word.words(), 'buffer_len': len(word_buffer)})
                word_buffer.append(next_word)
        # Add the next word if we can
        if current_node.word_index + 1 < len(word_buffer):
            child_1 = mk_domain(
                word_buffer, tlds, current_node.word_index + 1, current_node.tld_index)
            heappush(queue, child_1)
