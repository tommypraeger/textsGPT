# textsGPT
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


## Installation
TODO

## Usage
TODO

## Contributing
This project uses `black` for formatting. Following the [instructions for installation](https://github.com/psf/black?tab=readme-ov-file#installation-and-usage). Once installed, format by running the following from the root of this project:
```
black .
```

This project uses `typing`. If you are using VS Code and have a Python language server configured, I recommend setting `"python.analysis.typeCheckingMode": "strict"` in your settings.json to enforce type checking. Learn more [here](https://code.visualstudio.com/docs/python/settings-reference#_python-language-server-settings).

To change the contents of `my_chats.py` without accidentally committing your chat info, you can run:
```
git update-index --assume-unchanged textsgpt/mac/my_chats.py
```
If you want git to track `my_chats.py` again, run:
```
git update-index --no-assume-unchanged textsgpt/mac/my_chats.py
```

## Acknowledgements
- This project is in collaboration with Gabe Schmittlein and draws significant inspiration from https://github.com/gschmittlein/imessageGPT
- This project borrows from https://github.com/tommypraeger/imessage_analysis, which drew inspiration from https://stmorse.github.io/journal/iMessage.html