import pytest
from museum_admission import ticket_price, group_discount, gallery_entry


# ================= ticket_price =================
# if category not in BASE_PRICE -> True / False
def test_unknown_category_raises():
    with pytest.raises(ValueError):
        ticket_price("vip", 30, "tuesday", False)

# if age < 0 -> True / False
def test_negative_age_raises():
    with pytest.raises(ValueError):
        ticket_price("adult", -1, "tuesday", False)

# if age < 5 -> True (boundary 4) / False (boundary 5)
def test_age_four_free():
    assert ticket_price("child", 4, "tuesday", False) == 0

def test_age_zero_free():
    assert ticket_price("adult", 0, "sunday", True) == 0

def test_age_five_pays():
    assert ticket_price("child", 5, "tuesday", False) == 100

# day: monday / saturday / sunday / other weekday
def test_monday_half_price():
    assert ticket_price("adult", 30, "monday", False) == 150

def test_monday_odd_price_floor():
    assert ticket_price("student", 20, "monday", False) == 75

def test_saturday_surcharge():
    assert ticket_price("senior", 70, "saturday", False) == 250

def test_sunday_surcharge():
    assert ticket_price("child", 8, "sunday", False) == 150

def test_weekday_no_change():
    assert ticket_price("adult", 30, "wednesday", False) == 300

# with_guided_tour True(student / non-student) / False
def test_student_tour():
    assert ticket_price("student", 20, "tuesday", True) == 200

def test_adult_tour():
    assert ticket_price("adult", 30, "tuesday", True) == 400

def test_senior_tour_weekend():
    assert ticket_price("senior", 65, "sunday", True) == 350

def test_child_tour_monday():
    assert ticket_price("child", 10, "monday", True) == 150

def test_no_tour():
    assert ticket_price("student", 20, "friday", False) == 150


# ================= group_discount =================
def test_group_zero_raises():
    with pytest.raises(ValueError):
        group_discount(0, True)

def test_group_negative_raises():
    with pytest.raises(ValueError):
        group_discount(-3, False)

# school: >=20 True / False
def test_school_20():
    assert group_discount(20, True) == 40

def test_school_19():
    assert group_discount(19, True) == 25

def test_school_one():
    assert group_discount(1, True) == 25

# public: >=15 / >=8 / else
def test_public_15():
    assert group_discount(15, False) == 20

def test_public_14():
    assert group_discount(14, False) == 10

def test_public_8():
    assert group_discount(8, False) == 10

def test_public_7():
    assert group_discount(7, False) == 0

def test_public_one():
    assert group_discount(1, False) == 0


# ================= gallery_entry =================
# visitors >= capacity True / False
def test_at_capacity_wait():
    assert gallery_entry(100, 100, True) == "wait"

def test_over_capacity_wait():
    assert gallery_entry(120, 100, False) == "wait"

# >=90% and no slot -> queue
def test_ninety_percent_no_slot_queue():
    assert gallery_entry(90, 100, False) == "queue"

# >=90% but has slot -> enter (short-circuit second operand False)
def test_ninety_percent_with_slot_enter():
    assert gallery_entry(90, 100, True) == "enter"

# <90% -> enter (first operand False)
def test_below_ninety_enter():
    assert gallery_entry(89, 100, False) == "enter"

def test_empty_gallery_enter():
    assert gallery_entry(0, 50, True) == "enter"
