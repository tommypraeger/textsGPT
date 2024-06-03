"""
Entry point to the script. Contains the high-level logic.
"""

import sys

from .mac.chat import Chat
from .rules import (
    Rule,
    remove_links,
    remove_non_alphanumeric_messages,
    remove_non_standard_imessages,
)
from .llm_lib import create_faiss_index, gpt_completion


if len(sys.argv) < 2:
    raise Exception(
        "Expected the name of the chat as the first argument to the script."
    )
chat_name = sys.argv[1]


# Collect messages and set up vector index
# If running for the first time with a big group chat,
# setting up the index can take several minutes.
chat = Chat(chat_name)
chat.apply_rules(
    Rule(remove_links),
    Rule(remove_non_standard_imessages),
    Rule(remove_non_alphanumeric_messages),
)
faiss_index = create_faiss_index(chat)
chat.save_messages()


# Start interacting
print(
    f"""
{'=' * 50}\n\n
Hello {chat.user_name}!
I am a chatbot trained on text messages with {chat_name}.
Ask me something about your chat. Type 'exit' to quit.
"""
)
while True:
    query = input("Prompt: ")
    if query.lower().strip() == "exit":
        break
    response = gpt_completion(query, faiss_index)
    print(f"Chatbot: {response}")
print("\nBye!")
