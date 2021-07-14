from typing import Iterable

from hunterlib.conf import RunConfig
from hunterlib.steps.data import WordCombo


def generate_domains(config: RunConfig, word_chain: Iterable[WordCombo], tld_chain: Iterable[WordCombo]):
    filters = config.domain_filters
    biases = config.domain_biases
    for wc in word_chain:
        for tld in tld_chain:
            data = '.'.join([wc.concatenated, tld.concatenated])
            source = wc.source + tld.source
            if all(f.match(data) for f in filters):
                rv = WordCombo(data, source)
                bias = sum(b.adjust for b in biases if b.pattern in data)
                rv.score += bias
                yield rv
