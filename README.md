# textsGPT
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

textsGPT creates a chatbot that has knowledge of your text messages on your Mac. It works by first reading in messages from an iMessage group or individual chat, filtering the messages, and then encoding them into a local vector DB. You can then prompt a chatbot which uses retrieval-augmented generation (RAG) to find relevant messages and provide them as context in a prompt to a GPT completion model.

## Getting started

### Prerequisites
1. This project requires using macOS. It reads messages from the built-in messages database on Mac. I welcome future support for other operating systems and/or just passing in messages as a CSV file.
2. This project was written using Python 3.12.3. It may work with other Python versions. Download python: https://www.python.org/downloads/
3. You need an OpenAI API key to use with this project.

### Installation
1. Clone the repository:
```
git clone https://github.com/tommypraeger/textsGPT.git
```
2. Navigate to the repository directory:
```
cd textsGPT
```
3. Create a virtual environment:
```
python3 -m venv venv
```
4. Activate the virtual environment:
```
source venv/bin/activate
```
5. Install dependencies:
```
pip install -r requirements.txt
```
6. Set environment variables (you can use a `.env` file to define them if you would like):
    1. `OPENAI_API_KEY=<your OpenAI API key>`. https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key
    2. (optional) `TOKENIZERS_PARALLELISM=false` . Could help prevent the messages described [here](https://github.com/huggingface/transformers/issues/5486) from being printed.
7. Give the application you will use to run this script Full Disk Access (I know this seems sketchy but it needs to be able to access the messages database stored on your Mac, which is not available to applications by default):
   1. Open System Preferences
   2. Go to Security and Privacy
   3. Go to Privacy
   4. Go to Full Disk Access
   5. Give whatever application you're running this from Full Disk Access

    Note: These instructions might be different on newer versions of macOS. These instructions work for macOS Monterrey (v12) (I need a new Mac to use a newer version)

## Usage
First, edit the `CHATS` dictionary in `textsgpt/mac/my_chats.py` to include information about the chat(s) you want to use.

Run the script (replace `<name of chat>` with the dictionary key you used for the chat in `CHATS`):
```
python3 -m textsgpt "<name of chat>"
```

The first execution of the script can take several minutes for large chats as it builds an index for the entire content of the chat. Subsequent executions for the same chat should be faster as only new messages since the last script execution need to be indexed.

Once the indexing finishes, you can prompt the chatbot for information about your chat. Some example prompts:
- Suggest a new name for the group chat.
- Please suggest date ideas that \<name> would like in New York City. Be specific.
- What does \<name> think about \<topic>?
- Create a nickname for each member of the group.

## Contributing

### Formatting

This project uses `black` for formatting. Following the [instructions for installation](https://github.com/psf/black?tab=readme-ov-file#installation-and-usage). Once installed, format by running the following from the root of this project:
```
black .
```

### Typing

This project uses `typing`. If you are using VS Code and have a Python language server configured, I recommend setting `"python.analysis.typeCheckingMode": "strict"` in your settings.json to enforce type checking. Learn more [here](https://code.visualstudio.com/docs/python/settings-reference#_python-language-server-settings).

### Testing

#### Unit tests

This project uses [pytest](https://docs.pytest.org/). To run unit tests, run the following from the root of this project:
```
pytest
```

To generate a test coverage report, run:
```
pytest --cov-report=term-missing --cov=textsgpt
```

#### Manual testing

To change the contents of `my_chats.py` without accidentally committing your chat info, you can run:
```
git update-index --assume-unchanged textsgpt/mac/my_chats.py
```
If you want git to track `my_chats.py` again, run:
```
git update-index --no-assume-unchanged textsgpt/mac/my_chats.py
```

### Current limitations and ideas for improvements
In no particular order:
- iMessage group chats must be named and have a unique display name. This simplifies finding group chats in the database but is limiting.
- There isn't a nice UI to interact with.
- Adding chats/contacts is manual. It doesn't auto-fill contacts and chats with info from the database. Not sure if there is a way to integrate with Contacts in addition to the messages DB that is used in this application.
- Type hinting is not used in several places - mostly when working with Pandas and other libraries. I'm somewhat limited by the libraries, but there is more that could be done here.
- Data caching is pretty basic and not very robust.
- Text splitting is very basic. Texts could be split in a more sophisticated way, such as something that accounts for message timestamps, before being indexed.
- Only textual data is used. Attachments, links, emoji, etc are ignored.
- I have not experimented with other language models and strategies that might produce better results.
- Each prompt is given a limited context, which reduces effectiveness in answering meta prompts about the chat as opposed to more targeted information lookups.
- The chatbot has no memory of previous prompts.
- Only iMessage group chats are supported. At least CSVs of messages should be supported too.

## Acknowledgements
- This project is in collaboration with Gabe Schmittlein and draws significant inspiration from https://github.com/gschmittlein/imessageGPT
- This project borrows from https://github.com/tommypraeger/imessage_analysis, which drew inspiration from https://stmorse.github.io/journal/iMessage.html