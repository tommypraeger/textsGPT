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

    def load_messages(self, chat_db: sqlite3.Cursor, since: str = ""):
        """
        Load messages from database for this individual chat into a pandas DataFrame

        Args:
            chat_db (sqlite3.Cursor):
                Connection to the chat DB.
            since (str):
                Timestamp. Only messages newer than `since` will be loaded.
                Defaults to empty string, which means all messages should be loaded.

        Returns:
            pandas.DataFrame:
                pandas DataFrame containing the messages of the chat.
        """
        chat_ids = self.get_chat_ids(chat_db)
        message_df = self.get_message_df(chat_db, chat_ids, since)

        # replace leftmost column is_from_me with sender
        senders = message_df["is_from_me"].apply(  # type: ignore
            lambda is_from_me: (
                self.user_name if is_from_me == 1 else self.other_person.name
            )
        )
        message_df.drop(columns=["is_from_me"], inplace=True)
        message_df.insert(loc=0, column="sender", value=senders)  # type: ignore
        message_df = message_df.astype({"sender": str})  # type: ignore

        return message_df

    def get_chat_ids(self, chat_db: sqlite3.Cursor):
        """
        Find chat IDs (iMessage internal concept) for the chat with the other person.
        Each chat could have multiple IDs.

        Args:
            chat_db (sqlite3.Cursor):
                Connection to the chat DB.

        Returns:
            list[str]:
                List of chat IDs for this contact.
                There may be more than one chat ID for each chat.
        """
        chat_ids: list[str] = []
        for address in self.other_person.addresses:
            query = f"""
            SELECT ROWID
            FROM chat
            WHERE chat_identifier like "%{address}%"
            """
            chat_db.execute(query)
            chat_ids_for_address = chat_db.fetchall()
            if len(chat_ids_for_address) == 0:
                raise ValueError(f'chat for "{address}" not found in the chat DB.')
            # each row of sql response is a singleton tuple
            chat_ids.extend([str(chat_id[0]) for chat_id in chat_ids_for_address])
        return chat_ids

    def get_message_df(self, chat_db: sqlite3.Cursor, chat_ids: list[str], since: str):
        """
        Read the messages from the DB into a Pandas DataFrame

        Args:
            chat_db (sqlite3.Cursor):
                Connection to the chat DB.
            chat_ids (list[str]):
                List of chat IDs (iMessage internal concept) that correspond to this chat.
            since (str):
                Timestamp. Only messages newer than `since` will be loaded.
                If `since` is an empty string, load all messages.

        Returns:
            pandas.DataFrame:
                DataFrame containing raw message data from the chat.
        """
        since_filter = f"WHERE date > {since}" if since else ""
        query = f"""
        SELECT is_from_me, text, date, associated_message_type
        FROM message T1
        INNER JOIN chat_message_join T2
            ON T2.chat_id IN ({",".join([str(chat_id) for chat_id in chat_ids])})
            AND T1.ROWID=T2.message_id
        {since_filter}
        ORDER BY T1.date
        """
        chat_db.execute(query)
        df = pd.DataFrame(
            chat_db.fetchall(),
            columns=["is_from_me", "text", "time", "type"],
        )
        df.dropna(inplace=True)  # type: ignore
        df.reset_index(drop=True, inplace=True)
        df = df.astype({"is_from_me": int, "text": str, "time": str, "type": str})  # type: ignore
        return df
