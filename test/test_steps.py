from itertools import islice

from hypothesis import given, strategies as st, assume

import env.env_config
import hunterlib.steps
import hunterlib.steps.chains
import hunterlib.steps.config
import hunterlib.steps.domains
from hunterlib.models import Bias, FileSource
from hunterlib.steps.config import get_flattened_lists_and_files, mk_bias
from hunterlib.steps.data import ScoredWord, WordCombo
from hunterlib.wordlist import flatten


class DummyConfigModule:
    flatten_list_strings_lists = (
        ('a', 'b', 'c', 'd'),
        ('q', 'w', 'e', 'r')
    )
    flatten_list_bias_lists = (
        ('{"pattern": "asdf", "adjust": 1}', '{"pattern": "qwer", "adjust": -1}'),
        ('{"pattern": "zxcv", "adjust": 3}', '{"pattern": "brted", "adjust": -1}'),
    )


class TestFlattenedLists:

    def test_can_flatten_strings_in_lists(self):
        res = set(get_flattened_lists_and_files(DummyConfigModule, 'flatten_list_strings'))
        assert res == {'a', 'b', 'c', 'd', 'q', 'w', 'e', 'r'}

    def test_can_flatten_biases_in_lists(self):
        res = set(get_flattened_lists_and_files(DummyConfigModule, 'flatten_list_bias', Bias.parse_raw))
        assert res == {Bias(pattern='asdf', adjust=1), Bias(pattern='qwer', adjust=-1),
                       Bias(pattern='zxcv', adjust=3), Bias(pattern='brted', adjust=-1)}


class TestAppInProgress:

    def test_load_config(self):
        conf = hunterlib.steps.config.load_config(env.env_config)
        assert len(conf.word_list) > 0
        assert len(conf.word_biases) > 0
        assert len(conf.word_filters) > 0
        assert len(conf.tld_list) > 0
        assert len(conf.tld_biases) > 0
        assert len(conf.tld_filters) > 0
        assert len(conf.domain_biases) > 0
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
        assert all(w.concatenated != '' for w in result)


class TestSearchCombos:
    @given(st.lists(st.from_type(ScoredWord)), st.integers(1))
    def test_does_not_explode(self, words: list[ScoredWord], depth: int):
        words = tuple(words)
        tuple(islice(hunterlib.steps.chains.search_combos(words, depth), 0, 5))

    @given(st.lists(st.from_type(ScoredWord), min_size=1), st.integers(1, 10))
    def test_yields_output(self, words: list[ScoredWord], depth: int):
        words.sort(key=lambda sw: sw.score, reverse=True)
        words = tuple(words)
        result = tuple(islice(hunterlib.steps.chains.search_combos(words, depth), 0, 500))
        assert len(result) >= 1
        for (a, b) in zip(result, result[1:]):
            assert a.score >= b.score


class TestDataClasses:
    letters = 'abcdefghijklmnopqrstuvwxyz'

    # @given(st.text(alphabet=letters, min_size=1), st.text(alphabet=letters, min_size=1), st.integers(1, 5))
    # def test_score_function_decreases_with_word_length(self, word_a, word_b, score):
    #     assume(len(word_a) < len(word_b))
    #     word_a = ScoredWord(word=word_a, score=score)
    #     word_b = ScoredWord(word=word_b, score=score)
    #     assert WordCombo.score_words((word_a,)) > WordCombo.score_words((word_b,))

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

        words_a = tuple(words_a)
        words_b = tuple(words_b)
        assert WordCombo.score_words(words_a) >= WordCombo.score_words(words_b)
