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


def split_weighted(
    total_cents: int, weights: list[int] | tuple[int, ...]
) -> list[int]:
    """Split total_cents in proportion to non-negative integer weights.

    Returns a list of one share per weight, in weight order, whose elements sum
    exactly to ``total_cents``. Leftover cents go to the largest fractional
    remainders, with ties resolved in favour of the earlier weight.
    """
    if type(total_cents) is not int:
        raise TypeError("total_cents must be an int")
    if not isinstance(weights, (list, tuple)):
        raise TypeError("weights must be a list or tuple of int")
    for weight in weights:
        if type(weight) is not int:
            raise TypeError("every weight must be an int")
    if total_cents < 0:
        raise ValueError("total_cents must be >= 0")
    if len(weights) == 0:
        raise ValueError("weights must not be empty")
    if any(weight < 0 for weight in weights):
        raise ValueError("weights must be >= 0")
    weight_sum = sum(weights)
    if weight_sum == 0:
        raise ValueError("at least one weight must be positive")

    bases = []
    remainders = []
    for weight in weights:
        base, remainder = divmod(total_cents * weight, weight_sum)
        bases.append(base)
        remainders.append(remainder)

    leftover = total_cents - sum(bases)
    order = sorted(range(len(weights)), key=lambda i: (-remainders[i], i))
    for index in order[:leftover]:
        bases[index] += 1
    return bases
