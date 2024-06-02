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

# Define your user name here
# This will be used to label messages you sent
# Pass this as `user_name` to each chat
# You can use different user names for each chat instead of this constant if you would like
USER_NAME = "User"

# Define your chats here
# Replace these examples
CHATS: dict[str, GroupChat | IndividualChat] = {
    "my groupchat": GroupChat(
        name="my groupchat",
        user_name=USER_NAME,
        members=[
            Contact("Alice", ["(123)456-7890"]),
            Contact("Bob", ["987-654-3210"]),
            Contact("Carol", ["1(314)159-2653", "carol@email.com"]),
            Contact("Dan", ["1123581321", "dan@email.com", "dan2@email.com"]),
            Contact("Erin", ["erin@email.com"]),
        ],
    ),
    "Alice": IndividualChat(
        user_name=USER_NAME, other_person=Contact("Alice", ["(123)456-7890"])
    ),
}
