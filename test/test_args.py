import pytest

from hunterlib.args import arg_parser
from hunterlib.wordlist import flatten


class TestArgParser:
    def test_multiple_categories(self):
        parse_res = arg_parser.parse_args(['--words-from-kind', 'animal.n.01', '--words-from-kind', 'tree.n.01'])
        assert list(flatten(parse_res.category_words)) == ['animal.n.01', 'tree.n.01']

    def test_multiple_parts_of_speech(self):
        parse_res = arg_parser.parse_args(['--words-from-part', 'adverb', '--words-from-part', 'verb'])
        assert list(flatten(parse_res.pos_words)) == ['adverb', 'verb']

    def test_specify_config_file(self):
        parse_res = arg_parser.parse_args(['--config-file', 'conf.py'])
        assert parse_res.config_file == 'conf.py'

    def test_specify_config_file_with_no_arg(self):
        with pytest.raises(SystemExit):
            arg_parser.parse_args(['--config-file'])
