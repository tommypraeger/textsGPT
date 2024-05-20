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
from .ml_lib import create_faiss_index

chat = Chat(sys.argv[1], sys.argv[2])
chat.apply_rules(
    Rule(remove_links),
    Rule(remove_non_standard_imessages),
    Rule(remove_non_alphanumeric_messages),
)
print(chat.messages.head(n=5))
create_faiss_index(chat)
chat.save_messages()
