"""
Module that contains a class that defines a contact.
A contact represents a member of a group or individual chat.
"""

import sqlite3


# TODO: allow email addresses
# TODO: allow multiple phone numbers/emails in one contact
class Contact:
    """
    A class to define how to input a contact i.e. a member of a chat

    Attributes:
        name (str):
            Name of the person.
        phone_number (str):
            Phone number of the person. Used for finding their messages.
    """

    def __init__(self, name: str, phone_number: str):
        """
        Args:
            name (str):
                Name of the person. Doesn't have to match their actual contact.
            phone_number (str):
                Phone number of the person. Has to be the number they are sending messages from.
                Non-numeric characters are ignored and can be used to make numbers more readable.
        """
        self.name = name
        self.phone_number = self.clean_phone_number(phone_number)

    @staticmethod
    def clean_phone_number(phone_number: str) -> str:
        """
        Cleans phone number so it can be used to query the DB.
        Removes non-numeric characters.
        Phone number must have 10-15 digits (country codes optional).

        Args:
            phone_number (str):
                The phone number as a string.

        Returns:
            str:
                Phone number with non-numeric characters removed.
        """
        cleaned_phone_number = "".join(c for c in phone_number if c.isdigit())
        if len(cleaned_phone_number) < 10:
            raise ValueError(f"phone number {phone_number} is too short")
        if len(cleaned_phone_number) > 15:
            raise ValueError(f"phone number {phone_number} is too long")
        return cleaned_phone_number

    def get_contact_ids(self, chat_db: sqlite3.Cursor):
        """
        Find contact IDs (iMessage internal concept) for each chat member based on phone number.
        A phone number can be associated with multiple IDs.

        Args:
            chat_db (sqlite3.Cursor):
                Connection to the chat DB.

        Returns:
            list[str]:
                List of contacts IDs for this contact.
                There may be more than one contact ID for each contact.
        """
        query = f"""
        SELECT ROWID
        FROM handle
        WHERE id like "%{self.phone_number}%"
        """
        chat_db.execute(query)
        contact_ids = chat_db.fetchall()
        if len(contact_ids) == 0:
            raise ValueError(
                f"phone number {self.phone_number} not found in the chat DB."
            )
        # each row is a singleton tuple
        return [str(contact_id[0]) for contact_id in contact_ids]
