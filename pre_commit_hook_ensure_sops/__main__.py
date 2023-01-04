#!/usr/bin/env python3
"""
Validate if given list of files are encrypted with sops.
"""
from argparse import ArgumentParser
import json
from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
import sys

yaml = YAML(typ='safe')


def validate_enc(item):
    """
    Validate given item is encrypted.

    All leaf values in a sops encrypted file must be strings that
    start with ENC[. We iterate through lists and dicts, checking
    only for leaf strings. Presence of any other data type (like
    bool, number, etc) also makes the file invalid.
    """

    if isinstance(item, str):
        return item.startswith('ENC[')
    elif isinstance(item, list):
        return all(validate_enc(i) for i in item)
    elif isinstance(item, dict):
        return all(validate_enc(i) for i in item.values())
    else:
        return False

def check_file(filename):
    """
    Check if a file has been encrypted properly with sops.

    Returns a boolean indicating wether given file is valid or not, as well as
    a string with a human readable success / failure message.
    """
    # All YAML is valid JSON *except* if it contains hard tabs, and the default go
    # JSON outputter uses hard tabs, and since sops is written in go it does the same.
    # So we can't just use a YAML loader here - we use a yaml one if it ends in
    # .yaml, but json otherwise
    if filename.endswith('.yaml'):
        loader_func = yaml.load
    else:
        loader_func = json.load
    # sops doesn't have a --verify (https://github.com/mozilla/sops/issues/437)
    # so we implement some heuristics, primarily to guard against unencrypted
    # files being checked in.
    with open(filename) as f:
        try:
            doc = loader_func(f)
        except ParserError:
            # All sops encrypted files are valid JSON or YAML
            return False, f"{filename}: Not valid JSON or YAML, is not properly encrypted"

    if 'sops' not in doc:
        # sops puts a `sops` key in the encrypted output. If it is not
        # present, very likely the file is not encrypted.
        return False, f"{filename}: sops metadata key not found in file, is not properly encrypted"

    invalid_keys = []
    for k in doc:
        if k != 'sops':
            # Values under the `sops` key are not encrypted.
            if not validate_enc(doc[k]):
                # Collect all invalid keys so we can provide useful error message
                invalid_keys.append(k)

    if invalid_keys:
        return False, f"{filename}: Unencrypted values found nested under keys: {','.join(invalid_keys)}"

    return True, f"{filename}: Valid encryption"

def main():
    argparser = ArgumentParser()
    argparser.add_argument('filenames', nargs='+')

    args = argparser.parse_args()

    failed_messages = []

    for f in args.filenames:
        is_valid, message = check_file(f)

        if not is_valid:
            failed_messages.append(message)

    if failed_messages:
        print('\n'.join(failed_messages))
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
