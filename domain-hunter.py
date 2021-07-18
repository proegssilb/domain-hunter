from importlib import import_module
from itertools import islice

import hunterlib.steps as s
from hunterlib.args import arg_parser


def main():
    args = arg_parser.parse_args()
    conf_mod = import_module(args.config_file)
    conf = s.load_config(conf_mod)
    words_chain = s.generate_word_chain(conf)
    tld_chain = s.generate_tld_chain(conf)
    domain_chain = s.generate_domains(conf, words_chain, tld_chain)
    for d in islice(domain_chain, 0, 250):
        print("{0:32s} {1: 11.9g}".format(d.domain, d.score))


if __name__ == "__main__":
    main()
