"""
Test the Contact class.
"""

import sqlite3

import pytest

from textsgpt.mac.contact import Contact


@pytest.mark.parametrize(
    "phone_number",
    [("1234567890"), ("(123)456-7890"), ("123-456-7890"), ("   1234567890   ")],
)
def test_clean_phone_number__success(phone_number: str):
    """
    Test that clean_phone_number works in successful case.
    """
    assert Contact.clean_phone_number(phone_number) == "1234567890"


@pytest.mark.parametrize(
    "phone_number",
    [("123456789"), (""), ("123"), ("(123)456-789"), ("   (123)456-789   ")],
)
def test_clean_phone_number__too_short(phone_number: str):
    """
    Test that clean_phone_number raises an error when the number is too short.
    """
    with pytest.raises(ValueError):
        Contact.clean_phone_number(phone_number)


@pytest.mark.parametrize(
    "phone_number",
    [("1234567890123456"), ("+1(123)456-7890-12345")],
)
def test_clean_phone_number__too_long(phone_number: str):
    """
    Test that clean_phone_number raises an error when the number is too long.
    """
    with pytest.raises(ValueError):
        Contact.clean_phone_number(phone_number)


@pytest.mark.parametrize(
    "phone_number", [("email@notaphonenumber.net"), ("abcdef"), ("abc123")]
)
def test_clean_phone_number__not_a_number(phone_number: str):
    """
    Test that clean_phone_number raises an error when the input is not a number.
    This assumes email addresses are not supported, though it's possible they are used to end texts.
    """
    with pytest.raises(ValueError):
        Contact.clean_phone_number(phone_number)


def test_contact__create_success():
    """
    Test normal contact creation sets attributes as expected.
    """
    c = Contact("name", "(123)456-7890")
    assert c.name == "name"
    assert c.phone_number == "1234567890"


def test_contact__create_failed_bad_phone_number():
    """
    Test that errors in clean_phone_number get passed through to Contact initialization.
    """
    with pytest.raises(ValueError):
        Contact("name", "abc123")


def test_contact__contact_not_found(test_db: sqlite3.Cursor):
    """
    Test that correct error is thrown when contact ID(s) can't be found.
    """
    c = Contact("name", "(987)654-3210")
    with pytest.raises(ValueError) as e:
        c.get_contact_ids(test_db)
    assert "not found" in str(e.value)


def test_contact__single_contact_id(test_db: sqlite3.Cursor):
    """
    Test that a single contact ID will be found.
    """
    c = Contact("name", "1(100)000-0000")
    contact_ids = c.get_contact_ids(test_db)
    assert contact_ids == ["2"]


def test_contact__multiple_contact_ids(test_db: sqlite3.Cursor):
    """
    Test that multiple contact IDs will be found.
    """
    c = Contact("name", "(123)456-7890")
    contact_ids = c.get_contact_ids(test_db)
    assert contact_ids == ["1", "4"]
