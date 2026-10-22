import pytest

from bill_split import split_bill, split_weighted


def test_two_to_one_split():
    assert split_weighted(1000, [2, 1]) == [667, 333]


def test_equal_two_weights():
    assert split_weighted(1000, [1, 1]) == [500, 500]


def test_three_to_one_split():
    assert split_weighted(100, [3, 1]) == [75, 25]


def test_zero_total_with_weights():
    assert split_weighted(0, [1, 2]) == [0, 0]


def test_zero_weight_gets_zero_share():
    assert split_weighted(1000, [0, 1]) == [0, 1000]
    assert split_weighted(1000, [1, 0, 1]) == [500, 0, 500]


def test_single_positive_weight_gets_entire_total():
    assert split_weighted(12345, [7]) == [12345]


def test_tuple_weights_are_accepted():
    assert split_weighted(1000, (2, 1)) == [667, 333]


def test_very_large_values_are_exact():
    total = 10**18
    weights = [10**12, 3 * 10**12]
    shares = split_weighted(total, weights)
    assert shares == [total // 4, total - total // 4]
    assert sum(shares) == total


def test_fractional_thirds_round_largest_remainder_first():
    assert split_weighted(1000, [1, 1, 1]) == [334, 333, 333]


def test_fractional_hundred_thirds():
    assert split_weighted(100, [1, 1, 1]) == [34, 33, 33]


def test_each_share_within_one_cent_of_exact_proportion():
    cases = [
        (1000, [2, 1]),
        (100, [3, 1]),
        (100, [1, 2, 3]),
        (101, [5, 7, 11]),
        (999, [1, 1, 1, 1]),
        (12345, [2, 3, 5, 7, 11]),
    ]
    for total, weights in cases:
        shares = split_weighted(total, weights)
        wsum = sum(weights)
        assert sum(shares) == total
        for share, weight in zip(shares, weights):
            assert abs(total * weight - share * wsum) < wsum


def test_sum_exact_and_non_negative_over_table():
    for total in [0, 1, 2, 3, 7, 100, 101, 1000, 999999]:
        for weights in [[1], [1, 1], [1, 2], [1, 2, 3], [0, 1], [5, 0, 2]]:
            shares = split_weighted(total, weights)
            assert len(shares) == len(weights)
            assert all(type(s) is int and s >= 0 for s in shares)
            assert sum(shares) == total


def test_leftover_goes_to_largest_remainder():
    assert split_weighted(100, [1, 2, 3]) == [17, 33, 50]


def test_tie_break_favours_earlier_weight():
    assert split_weighted(10, [1, 1, 1]) == [4, 3, 3]
    assert split_weighted(5, [1, 1, 1, 1]) == [2, 1, 1, 1]


@pytest.mark.parametrize("total", [0, 1, 10, 100, 1000, 12345])
@pytest.mark.parametrize("people", [1, 2, 3, 4, 7])
def test_equal_weights_match_split_bill(total, people):
    assert split_weighted(total, [1] * people) == split_bill(total, people)


def test_non_integer_total_raises_type_error():
    with pytest.raises(TypeError):
        split_weighted(100.0, [1, 2])


def test_float_weight_raises_type_error():
    with pytest.raises(TypeError):
        split_weighted(100, [1.5, 1])


def test_bool_total_raises_type_error():
    with pytest.raises(TypeError):
        split_weighted(True, [1])


def test_bool_weight_raises_type_error():
    with pytest.raises(TypeError):
        split_weighted(100, [True, 1])


def test_generator_weights_raise_type_error():
    with pytest.raises(TypeError):
        split_weighted(100, (w for w in [1, 2]))


def test_string_weights_raise_type_error():
    with pytest.raises(TypeError):
        split_weighted(100, "12")


def test_none_weights_raise_type_error():
    with pytest.raises(TypeError):
        split_weighted(100, None)


def test_other_non_sequence_weights_raise_type_error():
    with pytest.raises(TypeError):
        split_weighted(100, {1, 2})
    with pytest.raises(TypeError):
        split_weighted(100, {1: 2})


def test_type_error_precedes_value_error():
    with pytest.raises(TypeError):
        split_weighted(-1.5, [1])
    with pytest.raises(TypeError):
        split_weighted(-1, [1.5])
    with pytest.raises(TypeError):
        split_weighted(-1, [-1.5])


def test_negative_total_raises_value_error():
    with pytest.raises(ValueError):
        split_weighted(-1, [1, 2])


def test_empty_weights_raises_value_error():
    with pytest.raises(ValueError):
        split_weighted(100, [])


def test_all_zero_weights_raise_value_error():
    with pytest.raises(ValueError):
        split_weighted(100, [0, 0])


def test_negative_weight_raises_value_error():
    with pytest.raises(ValueError):
        split_weighted(100, [1, -1])


def test_range_weights_raise_type_error():
    # Review fix for analyze finding A1: only list or tuple is accepted.
    with pytest.raises(TypeError):
        split_weighted(10, range(1, 3))
