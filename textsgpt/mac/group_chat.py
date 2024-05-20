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
        unknown_addresses (dict[str, str]):
            Contains a mapping of contact IDs to address (phone number or email)
            for contact IDs that have associated messages in this group chat
            but have not explicitly been added as contacts.
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
        self.unknown_addresses: dict[str, str] = {}

    def load_messages(self, chat_db: sqlite3.Cursor, since: str = ""):
        """
        Load messages from database for this group chat into a pandas DataFrame

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
        message_df = self.get_message_df(chat_db, chat_ids, since)
        message_df["sender"] = message_df["sender"].apply(  # type: ignore
            lambda sender_id: contact_id_map.get(sender_id)
            # if the sender contact_id isn't found, use the address directly
            or self.get_address_for_contact_id(chat_db, sender_id)
        )
        if len(self.unknown_addresses) > 0:
            print(
                f"[WARN] Found messages from {len(self.unknown_addresses)} unknown address(es). "
                "Please make sure all chat members are added as Contacts. "
                f"Unknown addresses: {', '.join(self.unknown_addresses.values())}"
            )

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

    def get_address_for_contact_id(
        self, chat_db: sqlite3.Cursor, contact_id: str
    ) -> str:
        """
        Find the address for a given contact ID (iMessage internal concept).
        The address will be the phone number or email that iMessage associates with the contact.
        This is used to find a meaningful way to label the sender of a message
        for which there was no associated `Contact` provided.

        Args:
            chat_db (sqlite3.Cursor):
                Connection to the chat DB.
            contact_id (str):
                The contact ID (iMessage internal concept) to search for.

        Returns:
            str:
                The address (phone number or email) corresponding to the given contact ID.
        """
        # avoid repeating query for every message sent by a contact ID
        if contact_id in self.unknown_addresses:
            return self.unknown_addresses[contact_id]

        query = f"""
        SELECT id
        FROM handle
        WHERE ROWID={contact_id}
        """
        chat_db.execute(query)
        address = str(chat_db.fetchone()[0])  # fetchone will return a singleton tuple

        # cache address for this contact ID
        self.unknown_addresses[contact_id] = address

        return address

    def get_message_df(
        self, chat_db: sqlite3.Cursor, chat_ids: list[str], since: str
    ) -> pd.DataFrame:
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
        SELECT handle_id, text, date, associated_message_type
        FROM message T1
        INNER JOIN chat_message_join T2
            ON T2.chat_id IN ({",".join(chat_ids)})
            AND T1.ROWID=T2.message_id
        {since_filter}
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
