Documentation
====================

This repository contains source for the documentation.
Part of documentation is generated using Pandoc from the code docstrings.

## Test locally

Run the following from the repository root directory:

```
pip3 install -r ./docs/requirements.txt
python3 -m sphinx -b html ./docs/source public
```
