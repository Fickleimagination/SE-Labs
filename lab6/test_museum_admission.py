import pytest
from museum_admission import ticket_price, group_discount, gallery_entry

#Example test cases:
def test_adult_weekday():
    assert ticket_price("adult", 30, "tuesday", False) == 300

def test_small_group():
    assert group_discount(4, False) == 0

#Write the rest of the test cases so that the code is 90- 100% covered.
