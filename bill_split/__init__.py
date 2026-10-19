def split_bill(total_cents: int, people: int) -> list[int]:
    """Split total_cents evenly between people, distributing the remainder.

    Returns a list of length ``people`` whose elements sum to ``total_cents``.
    """
    if type(total_cents) is not int or type(people) is not int:
        raise TypeError("total_cents and people must be int")
    if people < 1 or total_cents < 0:
        raise ValueError("people must be >= 1 and total_cents must be >= 0")
    base, extra = divmod(total_cents, people)
    return [base + 1] * extra + [base] * (people - extra)
