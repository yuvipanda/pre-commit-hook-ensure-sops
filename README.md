# pre-commit-hook-ensure-sops

A [pre-commit](https://pre-commit.com/) hook to ensure that users don't
accidentally check-in unencrypted files into a repository that uses
[sops](https://github.com/mozilla/sops) to safely store encrypted secrets.

By default, any file with the word `secret` in its path is required to
be encrypted with `sops`. This means any files under a directory
named `secret` are also required to be encrypted. If you want to exempt
specific files or directories from this requirement in your repository,
use the `exclude` option in your `.pre-commit-config.yaml`. When pushing
secrets to a repo, better safe than sorry :)

## Installation

Add this to your `.pre-commit-config.yaml`:

```yaml
  - repo: https://github.com/yuvipanda/pre-commit-hook-ensure-sops
    rev: v1.0
    hooks:
      - id: sops-encryption
        # Uncomment to exclude all markdown files from encryption
        # exclude: *.\.md
```
