"""
Module containing rules that filter or alter a messages DataFrame in some way.
For example, a rule might filter out messages containing no text.
Each rule is implemented as function that takes a messages DataFrame as the first argument
followed by an arbitrary number of arguments
and returns the resulting messages DataFrame.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Callable

import pandas as pd


@dataclass
class Rule:
    """
    A class to define a "rule". A rule filters or alters a messages DataFrame in some way.

    Attributes:
        func (Callable[[pd.DataFrame, ...], pd.DataFrame]):
            A function that takes a DataFrame as the first argument
            followed by an arbitrary number of arguments and returns a DataFrame.
            The function should modify the DataFrame in some way.
            The arguments of the function are not actually enforced through type-checking
            (they should be, still figuring out the best way to do that).
        kwargs (dict[str, Any]):
            A dictionary that contains a mapping of keyword arguments to pass to the function.
            Defaults to an empty dictionary if not set.
    """

    func: Callable[..., pd.DataFrame]
    kwargs: dict[str, Any] = field(default_factory=dict)


def remove_non_alphanumeric_messages(messages: pd.DataFrame) -> pd.DataFrame:
    """
    Remove messages that do not contain any alphanumeric characters from the DataFrame.
    The message just has to contain a single alphanumeric character to avoid removal
    (i.e. the characters don't all have to be alphanumeric).
    """
    # using \w to represent alphanumeric characters
    # \w also includes underscores
    return messages[messages["text"].str.contains(r"\w")]  # type: ignore


def remove_non_standard_imessages(messages: pd.DataFrame) -> pd.DataFrame:
    """
    Remove messages that are not standard text messages,
    such as iMessage reactions (like, love, emphasize, etc) or GamePigeon messages.
    Messages with (`type != 0`) are non-standard.
    `type` represents `associated_message_type` in the `messages` table in `chat.db`

    Type mappings (that I know of):
    2: GamePigeon message that has not been played
    3: GamePigeon message that has been played
    1000: sticker
    2000: love reaction
    2001: like reaction
    2002: dislike reaction
    2003: laugh reaction
    2004: emphasize reaction
    2005: question reaction
    3000: removed love reaction
    3001: removed like reaction
    3002: removed dislike reaction
    3003: removed laugh reaction
    3004: removed emphasize reaction
    3005: removed question reaction
    """
    return messages[messages["type"] == "0"]


def remove_links(messages: pd.DataFrame) -> pd.DataFrame:
    """
    Remove links from messages. Does not remove the whole message.
    If this rule is executed by remove_non_alphanumeric_messages,
    messages that are links and nothing else will be removed.
    """
    link_regex = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    messages["text"] = [re.sub(link_regex, "", str(text)) for text in messages["text"]]  # type: ignore
    return messages
