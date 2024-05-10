"""
Entry point to the script. Contains the high-level logic.
"""

import sys

from .mac.chat import Chat
from .rules import Rule, remove_non_alphanumeric_messages, remove_non_standard_imessages

chat = Chat(sys.argv[1], sys.argv[2])
chat.apply_rules(
    Rule(remove_non_alphanumeric_messages), Rule(remove_non_standard_imessages)
)
print(chat.messages.head(n=5))
# chat.messages.to_csv("messages.csv")
