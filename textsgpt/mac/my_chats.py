"""
Define your input here.

CHATS (dict[str, GroupChat | IndividualChat]):
    Define chats here. You can define multiple chats so it's easy to
    run the script on multiple chats in succession
    without having to swap out the chat input each time.

    dict key (str):
        Used to refer to a chat when passing input to the script.
    dict value (GroupChat | IndividualChat):
        Definition of a chat. Can be a group chat or individual chat.
"""

from .contact import Contact
from .group_chat import GroupChat
from .individual_chat import IndividualChat

# Define your chats here
# Replace these examples
CHATS: dict[str, GroupChat | IndividualChat] = {
    "my groupchat": GroupChat(
        name="my groupchat",
        members=[
            Contact("Alice", "(123)456-7890"),
            Contact("Bob", "987-654-3210"),
            Contact("Alice", "1(314)159-2653"),
            Contact("Alice", "1123581321"),
        ],
    ),
    "Alice": IndividualChat(other_person=Contact("Alice", "(123)456-7890")),
}
