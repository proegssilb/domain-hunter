from typing import Iterable

from hunterlib.conf import RunConfig
from hunterlib.steps.data import WordCombo


def generate_domains(config: RunConfig, word_chain: Iterable[WordCombo], tld_chain: Iterable[WordCombo]):
    # sourcery skip: hoist-statement-from-loop
    filters = config.domain_filters
    biases = config.domain_biases
    tld_iterable = tuple(tld_chain)
    processed_words = False
    for wc in word_chain:
        processed_words = True
        processed_domains = False
        for tld in tld_iterable:
            processed_domains = True
            data = '.'.join([wc.concatenated, tld.concatenated])
            source = wc.source + tld.source
            if all(f.match(data) for f in filters):
                rv = WordCombo(data, source)
                bias = sum(b.adjust for b in biases if b.pattern in data)
                rv.score += bias
                yield rv
        else:
            if not processed_domains:
                raise ValueError('Given tld_chain had no objects. Check config')
    else:
        if not processed_words:
            raise ValueError('Given word_chain had no objects. Check config')
