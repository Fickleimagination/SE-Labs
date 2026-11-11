import datetime


def format_visitor_name(name):
    """
    Formats a full name as 'Surname, Given names' for the ticket.

    Never raises. Returns '' when name is not a string or has no words, and
    just the surname (no trailing comma) when the name is a single word.
    """
    if not isinstance(name, str):
        return ""
    parts = name.split()
    if not parts:
        return ""
    surname = parts[-1].title()
    given = ' '.join(parts[:-1]).title()
    return surname + ', ' + given if given else surname


def parse_group_ages(text):
    """
    Parses space-separated ages into a list of ints.

    Never raises. Returns [] when text is not a string. Any value that is not
    a whole non-negative number (letters, decimals, negatives) is skipped.
    """
    if not isinstance(text, str):
        return []
    ages = []
    for token in text.split():
        if token.isascii() and token.isdigit():
            try:
                ages.append(int(token))
            except ValueError:  # absurdly long digit strings
                continue
    return ages


def parse_visit_date(text):
    """
    Parses a YYYY-MM-DD date into a (year, month, day) tuple.

    Never raises. Returns None when text is not a string, does not have exactly
    two dashes, has non-numeric parts, or is not a real calendar date.
    """
    if not isinstance(text, str):
        return None
    parts = text.strip().split('-')
    if len(parts) != 3:
        return None
    if not all(p.isascii() and p.isdigit() for p in parts):
        return None
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        datetime.date(year, month, day)  # rejects month 13, Feb 30, year 0, ...
    except (ValueError, OverflowError):
        return None
    return year, month, day


def main():
    print("==== Running format_visitor_name ====")
    value = input("Enter a visitor's full name (e.g. asha rao): ")
    result = format_visitor_name(value)
    print("Name on ticket:", result if result else "Invalid name (no words entered)")

    print("\n==== Running parse_group_ages ====")
    value = input("Enter the ages in the group separated by spaces (e.g. 34 12 70): ")
    print("Group ages:", parse_group_ages(value))

    print("\n==== Running parse_visit_date ====")
    value = input("Enter the visit date as YYYY-MM-DD (e.g. 2026-11-05): ")
    result = parse_visit_date(value)
    if result is None:
        print("Invalid date (expected a real date as YYYY-MM-DD)")
    else:
        print("Visit date (year, month, day):", result)


if __name__ == "__main__":
    main()
