import re
from typing import Iterable

from hunterlib.conf import RunConfig, NameGuppyConfig, NamecheapConfig
from hunterlib.models import Bias, FileSource
from hunterlib.wordlist import flatten


def mk_bias(o):
    if isinstance(o, str):
        if '{' in o:
            return Bias.parse_raw(o)
        else:
            w, adj = o.split(',')
            return Bias(pattern=w, adjust=adj)
    elif isinstance(o, dict):
        return Bias.parse_obj(o)
    elif isinstance(o, Bias):
        return o
    else:
        raise ValueError(f'Cannot convert value to bias: {repr(o)}')


def load_config(config_module) -> RunConfig:
    # Do domain stuff first, we re-use it to try to keep items down
    domain_filters = get_flattened_lists_and_files(config_module, 'domain_filter', re.compile)
    domain_biases = get_flattened_lists_and_files(config_module, 'domain_bias', mk_bias)

    # Now for the rest....
    word_sources = get_flattened_lists_and_files(config_module, 'word_source')
    word_filters = set(flatten([
        get_flattened_lists_and_files(config_module, 'word_filter', re.compile),
        domain_filters,
    ]))
    word_biases = get_flattened_lists_and_files(config_module, 'word_bias', mk_bias)

    tld_sources = get_flattened_lists_and_files(config_module, 'tld_source')
    tld_filters = set(flatten([
        get_flattened_lists_and_files(config_module, 'tld_filter', re.compile),
        domain_filters,
    ]))
    tld_biases = get_flattened_lists_and_files(config_module, 'tld_bias', mk_bias)

    # Extra bits of config
    guppy = NameGuppyConfig(
        enable=getattr(config_module, 'use_nameguppy'),
        cache_loc=getattr(config_module, 'nameguppy_cache')
    )

    cheap = NamecheapConfig(
        enable=getattr(config_module, 'use_namecheap'),
        cache_loc=getattr(config_module, 'namecheap_cache')
    )

    return RunConfig(
        word_list=word_sources,
        tld_list=tld_sources,

        word_filters=word_filters,
        tld_filters=tld_filters,
        domain_filters=domain_filters,

        word_biases=word_biases,
        tld_biases=tld_biases,
        domain_biases=domain_biases,

        name_guppy_conf=guppy,
        namecheap_conf=cheap,
    )


def get_flattened_lists_and_files(config_module, setting_base: str, kind=None) -> Iterable:
    kind = kind or str
    data = flatten([
        getattr(config_module, f'{setting_base}_lists', ()),
        (FileSource(kind, fn) for fn in getattr(config_module, f'{setting_base}_files', ())),
    ])
    return set(map(kind, data))
