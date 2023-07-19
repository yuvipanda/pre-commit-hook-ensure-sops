#!/usr/bin/env python3
"""
Validate if given list of files are encrypted with sops.
"""
from argparse import ArgumentParser
import json
from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
import sys
import re

yaml = YAML(typ='safe')

def _load_all(*args, **kwargs):
    # need to exhaust the generator
    return tuple(yaml.load_all(*args, **kwargs))


def validate_enc(item):
    """
    Validate given item is encrypted.

    All leaf values in a sops encrypted file must be strings that
    start with ENC[. We iterate through lists and dicts, checking
    only for leaf strings. Presence of any other data type (like
    bool, number, etc) also makes the file invalid except an empty
    string which would pass the encryption check.
    """
    
    if isinstance(item, str):
        if item == "" or item.startswith('ENC['):
            return True
    elif isinstance(item, list):
        return all(validate_enc(i) for i in item)
    elif isinstance(item, dict):
        return all(validate_enc(i) for i in item.values())
    else:
        return False

def check_file(filename, args):
    """
    Check if a file has been encrypted properly with sops.

    Returns a boolean indicating wether given file is valid or not, as well as
    a string with a human readable success / failure message.
    """
    # All YAML is valid JSON *except* if it contains hard tabs, and the default go
    # JSON outputter uses hard tabs, and since sops is written in go it does the same.
    # So we can't just use a YAML loader here - we use a yaml one if it ends in
    # .yaml, but json otherwise
    # We also leverage the _load_all function if the user specifies to allow muliple documents
    # in each individual YAML file
    if filename.endswith('.yaml'):
        if args.allow_multiple_documents:
            loader_func = _load_all
        else:
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
    if not args.allow_multiple_documents:
        docs = [doc]
    else:
        docs = doc

    for doc in docs:

        if 'sops' not in doc:
            # sops puts a `sops` key in the encrypted output. If it is not
            # present, very likely the file is not encrypted.
            return False, f"{filename}: sops metadata key not found in file, is not properly encrypted"

        # Checks for the presense of the encrypted_regex key within the sops section
        # if present sets the encrypted regex value to the value of this key
        # otherwise, sets the value to "match all strings" \S regex
        if 'encrypted_regex' in doc['sops']:
            encrypted_regex = doc['sops']['encrypted_regex']
        else:
            encrypted_regex = '\S'

        invalid_keys = []
        for k in doc:
            if k != 'sops' and re.match(encrypted_regex, k):
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
    argparser.add_argument('-m', '--allow-multiple-documents', action='store_true')

    args = argparser.parse_args()

    failed_messages = []

    for f in args.filenames:
        is_valid, message = check_file(f, args)

        if not is_valid:
            failed_messages.append(message)

    if failed_messages:
        print('\n'.join(failed_messages))
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
