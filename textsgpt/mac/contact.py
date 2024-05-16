"""
Module that contains a class that defines a contact.
A contact represents a member of a group or individual chat.
"""

import sqlite3


class Contact:
    """
    A class to define how to input a contact i.e. a member of a chat

    Attributes:
        name (str):
            Name of the person.
        addresses (list[str]):
            List of phone numbers and/or email addresses for this person.
            Used for finding their messages.
    """

    def __init__(self, name: str, addresses: list[str]):
        """
        Args:
            name (str):
                Name of the person. Doesn't have to match their actual contact.
            addresses (str):
                List of phone numbers and/or email addresses for this person.
                This should be the address(es) they are sending messages from.
                Non-numeric characters in phone numbers are not necessary,
                but can be included for readability.
        """
        self.name = name
        if not addresses:
            raise ValueError("at least 1 address must be provided for each contact")
        self.addresses = self.clean_and_verify_addresses(addresses)

    def clean_and_verify_addresses(self, addresses: list[str]) -> list[str]:
        """
        Sort addresses into email addresses and phone numbers.
        Perform cleaning and verification of phone numbers.
        No verification is done for emails. They just need to have an @.
        """
        verified_addresses: list[str] = []
        for address in addresses:
            if "@" in address:
                # treating having an @ good enough to validate an email address
                verified_addresses.append(address)
            else:
                verified_addresses.append(self.clean_and_verify_phone_number(address))
        return verified_addresses

    @staticmethod
    def clean_and_verify_phone_number(phone_number: str) -> str:
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
        Find contact IDs (iMessage internal concept) for each chat member
        based on addresses, which are phone numbers and/or emails.
        Each address can be associated with multiple contact IDs.

        Args:
            chat_db (sqlite3.Cursor):
                Connection to the chat DB.

        Returns:
            list[str]:
                List of contacts IDs for this contact.
                There may be more than one contact ID for each contact.
        """
        contact_ids: list[str] = []
        for address in self.addresses:
            query = f"""
            SELECT ROWID
            FROM handle
            WHERE id like "%{address}%"
            """
            chat_db.execute(query)
            contact_ids_for_address = chat_db.fetchall()
            if len(contact_ids_for_address) == 0:
                raise ValueError(f"address {address} not found in the chat DB.")
            # each row of sql response is a singleton tuple
            contact_ids.extend(
                [str(contact_id[0]) for contact_id in contact_ids_for_address]
            )
        return contact_ids
