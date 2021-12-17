ass_lint
========

A Python tool to check ASS subtitles for common mistakes and errors.

## Installation

```
pip install --user ass-lint
```

## To do:

- Split some of the big classes into separate files
- Add human readable and numeric codes to each check
- Allow disabling each checks via command line and via inline comments
- Allow setting the language via command line
- Allow setting the fonts directory via command line
- Provide documentation for some more exotic checks such as the fonts check

## Contributing

```sh
# Clone the repository:
git clone https://github.com/bubblesub/ass_lint.git
cd ass_lint

# Install to a local venv:
poetry install

# Install pre-commit hooks:
poetry run pre-commit install

# Enter the venv:
poetry shell
```

This project uses [poetry](https://python-poetry.org/) for packaging,
install instructions at [poetry#installation](https://python-poetry.org/docs/#installation)
