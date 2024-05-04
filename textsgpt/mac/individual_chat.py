"""
Module containing a class that defines an iMessage individual chat
i.e. a chat between you and one other person.
Includes functionality for loading messages from that chat.
"""

import sqlite3

import pandas as pd

from .contact import Contact


class IndividualChat:
    """
    A class to define a chat in the Messages app.

    Attributes:
        other_person (Contact):
            Contact representing the other person in the chat (aside from you)
        user_name (str):
            Your name. Used to label messages you sent.
            Defaults to "You".
    """

    def __init__(self, other_person: Contact):
        """
        Args:
            other_person (Contact):
                Contact representing the other persion in the chat (aside from you).
        """
        self.other_person = other_person
        self.user_name = "You"

    def load_messages(self, chat_db: sqlite3.Cursor):
        """
        Load messages from database for this individual chat into a pandas DataFrame

        Args:
            chat_db (sqlite3.Cursor):
                Connection to the chat DB.

        Returns:
            pandas.DataFrame:
                pandas DataFrame containing the messages of the chat.
        """
        return pd.DataFrame()
