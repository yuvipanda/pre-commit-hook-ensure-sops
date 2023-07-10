"""
Tests for main functions.
"""
from contextlib import nullcontext
from pathlib import Path

import pytest
from ruamel.yaml.parser import ParserError

from pre_commit_hook_ensure_sops.__main__ import check_file

VALID_SECRET = """
foo: ENC[AES256_GCM,data:9LiS,iv:B/Add+R3lTSx66Qrq8/+jFD2mok8GdD7R32uAf04+Ho=,tag:iyCZ1thFop63/2L+skFcdg==,type:str]
sops:
"""

INVALID_SECRET = """
foo: this_is_not_encrypted_text
sops:
"""

NO_SOPS_METADATA = """
foo: ENC[AES256_GCM,data:9LiS,iv:B/Add+R3lTSx66Qrq8/+jFD2mok8GdD7R32uAf04+Ho=,tag:iyCZ1thFop63/2L+skFcdg==,type:str]
"""

INVALID_YAML = """
this_is_not_valid_yaml
"""


@pytest.mark.parametrize(
    "text,is_valid",
    [
        pytest.param(INVALID_SECRET, False, id="invalid_secret"),
        pytest.param(VALID_SECRET, True, id="valid_secret"),
        pytest.param(NO_SOPS_METADATA, False, id="no_sops_metadata"),
        pytest.param(INVALID_YAML, False, id="invalid_yaml"),
    ],
)
def test_check_file_validity(text, is_valid, tmp_path: Path):
    """
    Test check_file.

    Checks with known valid and invalid yaml texts and checks
    if an error is raised with invalid one.
    """
    filepath = tmp_path / "test.yaml"
    filepath.write_text(text)
    filename = filepath.as_posix()
    result = check_file(filename=filename)
    assert result[0] == is_valid
