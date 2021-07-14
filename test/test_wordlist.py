import pytest

import hunterlib.wordlist as wl


class TestWords:

    @pytest.mark.parametrize("lemma", {
        'animal.n.01',
        'color.n.01'
    })
    def test_handles_happy_path(self, lemma):
        res = tuple(wl.words(lemma))
        assert len(res) > 0

    def test_part_of_speech_produces_results(self):
        assert len(wl.PartOfSpeech.ADJECTIVE) > 0
