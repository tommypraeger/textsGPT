"""
Entry point to the script. Contains the high-level logic.
"""

import sys

from .mac.chat import Chat

chat = Chat(sys.argv[1], sys.argv[2])
df = chat.load_messages()
print(df.head(n=5))
