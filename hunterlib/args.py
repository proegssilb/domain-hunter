import argparse

arg_parser = argparse.ArgumentParser(description="Use one or more lists of words to generate possible domain names.")

# General
arg_parser.add_argument('--config-file', action='store', dest='config_file', type=str)

# Adding sources
arg_parser.add_argument('--words-from-kind', nargs=1, action='append', dest='category_words', type=str,
                        help='Category used to derive words, specified as a WordNet synset.')

arg_parser.add_argument('--words-from-part', nargs=1, action='append', dest='pos_words', type=str,
                        help='Part of speech used to derive words, via WordNet.')

# Adding filters


# Adding bias
