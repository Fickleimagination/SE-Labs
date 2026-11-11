from hypothesis import given, strategies as st
from museum_admission_parser import format_visitor_name, parse_group_ages, parse_visit_date


# Each test feeds arbitrary text (and None) to one function. A function passes
# only if it never raises, whatever the input. Any exception is caught with
# try/except and turned into a failure that names the crashing input.


@given(st.text() | st.none())
def test_format_visitor_name_no_crash(s):
    error = None
    try:
        result = format_visitor_name(s)
    except Exception as e:
        error = e
    assert error is None, (
        f"format_visitor_name({s!r}) crashed with {type(error).__name__}: {error}"
    )
    assert isinstance(result, str)


@given(st.text() | st.none())
def test_parse_group_ages_no_crash(s):
    error = None
    try:
        result = parse_group_ages(s)
    except Exception as e:
        error = e
    assert error is None, (
        f"parse_group_ages({s!r}) crashed with {type(error).__name__}: {error}"
    )
    assert isinstance(result, list)
    assert all(isinstance(age, int) and age >= 0 for age in result)


@given(st.text() | st.none())
def test_parse_visit_date_no_crash(s):
    error = None
    try:
        result = parse_visit_date(s)
    except Exception as e:
        error = e
    assert error is None, (
        f"parse_visit_date({s!r}) crashed with {type(error).__name__}: {error}"
    )
    assert result is None or (isinstance(result, tuple) and len(result) == 3)
