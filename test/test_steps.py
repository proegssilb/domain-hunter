import re
from itertools import islice

from hypothesis import given, strategies as st, assume
from hypothesis.strategies import composite

import env.env_config
import hunterlib.steps
import hunterlib.steps.chains
import hunterlib.steps.config
import hunterlib.steps.domains
from hunterlib.conf import RunConfig, NameGuppyConfig, NamecheapConfig
from hunterlib.models import Bias, FileSource
from hunterlib.steps.config import get_flattened_lists_and_files, mk_bias
from hunterlib.steps.data import ScoredWord, WordCombo
from hunterlib.wordlist import flatten

letters = 'abcdefghijklmnopqrstuvwxyz'


class DummyConfigModule:
    flatten_list_strings_lists = (
        ('a', 'b', 'c', 'd'),
        ('q', 'w', 'e', 'r')
    )
    flatten_list_bias_lists = (
        ('{"pattern": "asdf", "adjust": 1}', '{"pattern": "qwer", "adjust": -1}'),
        ('{"pattern": "zxcv", "adjust": 2}', '{"pattern": "brted", "adjust": -1}'),
    )


class TestFlattenedLists:

    def test_can_flatten_strings_in_lists(self):
        res = set(get_flattened_lists_and_files(DummyConfigModule, 'flatten_list_strings'))
        assert res == {'a', 'b', 'c', 'd', 'q', 'w', 'e', 'r'}

    def test_can_flatten_biases_in_lists(self):
        res = set(get_flattened_lists_and_files(DummyConfigModule, 'flatten_list_bias', Bias.parse_raw))
        assert res == {Bias(pattern='asdf', adjust=1), Bias(pattern='qwer', adjust=-1),
                       Bias(pattern='zxcv', adjust=2), Bias(pattern='brted', adjust=-1)}


@composite
def generate_config(draw, strings=st.text('abcdefghijklmnopqrstuvwxyz', min_size=1)):
    return RunConfig(
        word_list=draw(st.sets(strings, min_size=50, max_size=100_000)),
        tld_list=draw(st.sets(strings, min_size=5, max_size=1000)),

        word_filters={re.compile(r'\w{1,32}')},
        tld_filters={re.compile(r'\w{1,5}')},
        domain_filters={re.compile(r'.{1,32}')},

        word_biases=draw(st.sets(st.from_type(Bias), max_size=100)),
        tld_biases=draw(st.sets(st.from_type(Bias), max_size=100)),
        domain_biases=draw(st.sets(st.from_type(Bias), max_size=100)),

        name_guppy_conf=draw(st.from_type(NameGuppyConfig)),
        namecheap_conf=draw(st.from_type(NamecheapConfig))
    )


class TestAppInProgress:

    def test_load_config(self):
        conf = hunterlib.steps.config.load_config(env.env_config)
        assert len(conf.word_list) > 0
        assert len(conf.word_biases) > 0
        assert len(conf.word_filters) > 0
        assert len(conf.tld_list) > 0
        assert len(conf.tld_biases) > 0
        assert len(conf.tld_filters) > 0
        assert len(conf.domain_filters) > 0
        result = set(flatten([FileSource(mk_bias, fn) for fn in env.env_config.word_bias_files]))
        assert len(result) > 0

    def test_generate_chain(self):
        conf = hunterlib.steps.config.load_config(env.env_config)
        chain = hunterlib.steps.chains.generate_word_chain(conf)
        result = tuple(islice(chain, 0, 25))
        assert len(result) == 25
        assert all(w.concatenated != '' for w in result)

    def test_generate_tld(self):
        conf = hunterlib.steps.config.load_config(env.env_config)
        chain = hunterlib.steps.chains.generate_tld_chain(conf)
        result = tuple(islice(chain, 0, 10))
        assert len(result) == 10
        assert all(w.concatenated != '' for w in result)

    def test_generate_domains(self):
        conf = hunterlib.steps.config.load_config(env.env_config)
        word_chain = hunterlib.steps.chains.generate_word_chain(conf)
        tld_chain = hunterlib.steps.chains.generate_tld_chain(conf)
        domain_chain = hunterlib.steps.domains.generate_domains(conf, word_chain, tld_chain)
        result = tuple(islice(domain_chain, 0, 5))
        assert len(result) == 5
        assert all(w.domain != '' for w in result)

    @given(generate_config(), st.integers(5, 1000))
    def test_with_auto_config(self, config, result_count):
        word_chain = hunterlib.steps.chains.generate_word_chain(config)
        tld_chain = hunterlib.steps.chains.generate_tld_chain(config)
        domain_chain = hunterlib.steps.domains.generate_domains(config, word_chain, tld_chain)
        result = tuple(islice(domain_chain, 0, result_count))
        assert len(result) >= 1
        assert all(w.domain != '' for w in result)


class TestChains:
    @given(st.sets(st.text(letters, min_size=1), min_size=1), st.sets(st.from_type(Bias)), st.integers(1, 10))
    def test_does_not_explode(self, words, biases, max_repeat):
        result_iter = hunterlib.steps.chains.generate_chain(words, biases, max_repeat)
        result = tuple(islice(result_iter, 0, 50))
        assert len(result) >= 1

    @given(st.sets(st.text(letters, min_size=1), min_size=1), st.sets(st.from_type(Bias)), st.integers(1, 10))
    def test_output_sorted(self, words, biases, max_repeat):
        result_iter = hunterlib.steps.chains.generate_chain(words, biases, max_repeat)
        result = list(islice(result_iter, 0, 50))
        assert sorted(result, key=lambda wc: wc.score, reverse=True) == result


class TestSearchCombos:
    @given(st.lists(st.from_type(ScoredWord)), st.integers(1))
    def test_does_not_explode(self, words: list[ScoredWord], depth: int):
        words = tuple(words)
        tuple(islice(hunterlib.steps.chains.search_combos(words, depth), 0, 5))

    @given(st.lists(st.from_type(ScoredWord), min_size=1), st.integers(1, 10))
    def test_yields_output(self, words: list[ScoredWord], depth: int):
        words.sort(key=lambda sw: sw.score, reverse=True)
        words = tuple(words)
        result = list(islice(hunterlib.steps.chains.search_combos(words, depth), 0, 500))
        assert len(result) >= 1
        assert sorted(result, key=lambda wc: wc.score, reverse=True) == result

    @given(st.lists(st.from_type(ScoredWord), min_size=1, max_size=400))
    def test_yields_all_words_from_input(self, words: list[ScoredWord]):
        words.sort(key=lambda sw: sw.score, reverse=True)
        words = tuple(words)
        result = list(islice(hunterlib.steps.chains.search_combos(words, 1), 0, 500))
        assert len(words) == len(result)


class TestDataClasses:
    @given(st.from_type(ScoredWord), st.integers(min_value=1, max_value=100), st.integers(min_value=1, max_value=100))
    def test_score_function_decreases_with_word_count(self, word: ScoredWord, count_a: int, count_b: int):
        assume(count_a < count_b)
        tup_a = (word,) * count_a
        tup_b = (word,) * count_b
        assert WordCombo.score_words(tup_a) >= WordCombo.score_words(tup_b)

    @given(st.lists(st.from_type(ScoredWord), min_size=1), st.lists(st.from_type(ScoredWord), min_size=1))
    def test_adding_words_never_improves_score(self, words_a, words_b):
        assume(len(words_a) < len(words_b))
        scores_a = [w.score for w in words_a]
        for (i, score) in enumerate(sorted(scores_a, reverse=True)):
            words_a[i].score = score

        scores_b = [w.score for w in words_b]
        for (i, score) in enumerate(sorted(scores_b, reverse=True)):
            words_b[i].score = score

        words_a: tuple[ScoredWord] = tuple(words_a)
        words_b: tuple[ScoredWord] = words_a + tuple(words_b)
        assert WordCombo.score_words(words_a) >= WordCombo.score_words(words_b)
