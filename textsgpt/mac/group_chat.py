"""
Module containing a class that defines an iMessage group chat.
Includes functionality for loading messages from that group chat.
"""

import sqlite3

import pandas as pd

from .contact import Contact


class GroupChat:
    """
    A class to define a chat in the Messages app.

    Attributes:
        name (str):
            Name of the group chat.
        members (list[Contact]):
            Members of the group chat.
        user_name (str):
            Your name. Used to label messages you sent.
            Defaults to "You".
    """

    def __init__(self, name: str, members: list[Contact]):
        """
        Initializes a group chat.

        Args:
            name (str):
                Name of the group chat.
                This must match the name of the group chat exactly
                as it appears in the Messages app.
            members (list[Contact]):
                Members of the chat. Don't include yourself.
        """
        self.name = name
        self.members = members
        self.user_name = "You"

    def load_messages(self, chat_db: sqlite3.Cursor):
        """
        Load messages from database for this group chat into a pandas DataFrame

        Args:
            chat_db (sqlite3.Cursor):
                Connection to the chat DB.

        Returns:
            pandas.DataFrame:
                pandas DataFrame containing the messages of the chat.
        """

        # save the contact IDs and chat IDs for this chat
        # map from contact ID -> contact name to be used in substitution later
        # contact ID 0 is always the user
        contact_id_map = {"0": self.user_name}
        for member in self.members:
            contact_ids = member.get_contact_ids(chat_db)
            for contact_id in contact_ids:
                contact_id_map[contact_id] = member.name
        chat_ids = self.get_chat_ids(chat_db)

        # get messages and replace contact IDs with names
        message_df = self.get_message_df(chat_db, chat_ids)
        for row in range(len(message_df)):
            try:
                sender = contact_id_map[message_df.loc[row, "sender"]]  # type: ignore
                message_df.loc[row, "sender"] = sender
            except KeyError:
                print(
                    "[WARN] Found message from unknown sender. "
                    "Please make sure all chat members are added as Contacts."
                )
                # use "Unknown" as name for undeclared contacts
                message_df.loc[row, "sender"] = "Unknown"
                contact_id_map[message_df.loc[row, "sender"]] = "Unknown"  # type: ignore

        return message_df

    def get_chat_ids(self, chat_db: sqlite3.Cursor):
        """
        Find chat IDs (iMessage internal concept) for the chat.
        Each chat could have multiple IDs.

        Args:
            chat_db (sqlite3.Cursor):
                Connection to the chat DB.

        Returns:
            list[str]:
                List of contacts IDs for this contact.
                There may be more than one contact ID for one contact.
        """
        query = f"""
        SELECT ROWID
        FROM chat
        WHERE display_name="{self.name}"
        """
        chat_db.execute(query)
        chat_ids = chat_db.fetchall()
        if len(chat_ids) == 0:
            raise ValueError(f'chat with name "{self.name}" not found in the chat DB.')
        # each row is a singleton tuple
        return [str(chat_id[0]) for chat_id in chat_ids]

    def get_message_df(self, chat_db: sqlite3.Cursor, chat_ids: list[str]):
        """
        Read the messages from the DB into a Pandas DataFrame

        Args:
            chat_db (sqlite3.Cursor):
                Connection to the chat DB.
            chat_ids (list[str]):
                List of chat IDs (iMessage internal concept) that correspond to this chat.

        Returns:
            pandas.DataFrame:
                DataFrame containing raw message data from the chat.
        """
        query = f"""
        SELECT handle_id, text, date, associated_message_type \
        FROM message T1 \
        INNER JOIN chat_message_join T2 \
            ON T2.chat_id IN ({",".join(chat_ids)}) \
            AND T1.ROWID=T2.message_id \
        ORDER BY T1.date
        """
        chat_db.execute(query)
        df = pd.DataFrame(
            chat_db.fetchall(),
            columns=["sender", "text", "time", "type"],
        )
        df = df.astype({"sender": str, "text": str, "time": str, "type": str})  # type: ignore
        return df
