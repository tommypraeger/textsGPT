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
                Members of the chat.
                You don't need to include a contact for yourself,
                but it can be useful if your messages are coming from multiple addresses.
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
        known_missing_contacts: set[str] = set()
        for row in range(len(message_df)):
            sender_id = str(message_df.loc[row, "sender"])
            try:
                sender = contact_id_map[sender_id]
                message_df.loc[row, "sender"] = sender
            except KeyError:
                # if a contact hasn't been provided for this sender,
                # use the handle (phone number or email) associated with the sender instead
                missing_contact = self.get_handle_for_contact_id(chat_db, sender_id)
                message_df.loc[row, "sender"] = missing_contact

                # save the missing contact value in case it pops up again
                if missing_contact not in known_missing_contacts:
                    print(
                        f"[WARN] Found message(s) from unknown sender: {missing_contact}. "
                        "Please make sure all chat members are added as Contacts."
                    )
                    contact_id_map[sender_id] = missing_contact
                    known_missing_contacts.add(missing_contact)

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
                List of chat IDs for this chat.
                There may be more than one chat ID for each chat.
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

    def get_handle_for_contact_id(
        self, chat_db: sqlite3.Cursor, contact_id: str
    ) -> str:
        """
        Find the handle for a given contact ID (iMessage internal concept).
        The handle will be the phone number or email that iMessage associates with the contact.
        This is used to find a meaningful way to label the sender of a message
        for which there was no associated `Contact` provided.

        Args:
            chat_db (sqlite3.Cursor):
                Connection to the chat DB.
            contact_id (str):
                The contact ID (iMessage internal concept) to search for.

        Returns:
            str:
                The handle (phone number or email) corresponding to the given contact ID.
        """
        query = f"""
        SELECT id
        FROM handle
        WHERE ROWID={contact_id}
        """
        chat_db.execute(query)
        return str(chat_db.fetchone()[0])  # fetchone will return a singleton tuple

    def get_message_df(
        self, chat_db: sqlite3.Cursor, chat_ids: list[str]
    ) -> pd.DataFrame:
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
        SELECT handle_id, text, date, associated_message_type
        FROM message T1
        INNER JOIN chat_message_join T2
            ON T2.chat_id IN ({",".join(chat_ids)})
            AND T1.ROWID=T2.message_id
        ORDER BY T1.date
        """
        chat_db.execute(query)
        df = pd.DataFrame(
            chat_db.fetchall(),
            columns=["sender", "text", "time", "type"],
        )
        df.dropna(inplace=True)  # type: ignore
        df.reset_index(drop=True, inplace=True)
        df = df.astype({"sender": str, "text": str, "time": str, "type": str})  # type: ignore
        return df
