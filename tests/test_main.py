"""
Tests for main functions.
"""
from pathlib import Path

import pytest

from pre_commit_hook_ensure_sops.__main__ import check_file

VALID_YAML_SECRET = """
foo: ENC[AES256_GCM,data:9LiS,iv:B/Add+R3lTSx66Qrq8/+jFD2mok8GdD7R32uAf04+Ho=,tag:iyCZ1thFop63/2L+skFcdg==,type:str]
sops:
"""

VALID_JSON_SECRET = """
{
    "foo": "ENC[AES256_GCM,data:9LiS,iv:B/Add+R3lTSx66Qrq8/+jFD2mok8GdD7R32uAf04+Ho=,tag:iyCZ1thFop63/2L+skFcdg==,type:str]",
    "sops": ""
}
"""

INVALID_JSON_SECRET = """
{
    "foo": "this_is_not_encrypted_text",
    "sops": ""
}
"""

INVALID_YAML_SECRET = """
foo: this_is_not_encrypted_text
sops:
"""

NO_SOPS_METADATA_YAML = """
foo: ENC[AES256_GCM,data:9LiS,iv:B/Add+R3lTSx66Qrq8/+jFD2mok8GdD7R32uAf04+Ho=,tag:iyCZ1thFop63/2L+skFcdg==,type:str]
"""

INVALID_YAML = """
this_is_not_valid_yaml
"""


@pytest.mark.parametrize(
    "text,is_valid,extension",
    [
        pytest.param(INVALID_YAML_SECRET, False, "yaml", id="invalid_secret"),
        pytest.param(VALID_YAML_SECRET, True, "yaml", id="valid_secret"),
        pytest.param(NO_SOPS_METADATA_YAML, False, "yaml", id="no_sops_metadata"),
        pytest.param(INVALID_YAML, False, "yaml", id="invalid_yaml"),
        pytest.param(VALID_JSON_SECRET, True, "json", id="valid_json"),
        pytest.param(
            INVALID_JSON_SECRET, False, "json", id="valid_json_with_yaml_loader"
        ),
    ],
)
def test_check_file_validity_yaml(text, is_valid, extension, tmp_path: Path):
    """
    Test check_file.

    Checks with known valid and invalid yaml texts and checks
    if an error is raised with invalid one.
    """
    filepath = tmp_path / f"test.{extension}"
    filepath.write_text(text)
    filename = filepath.as_posix()
    result = check_file(filename=filename)
    assert result[0] == is_valid
