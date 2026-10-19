import pytest

from bill_split import split_bill


def test_even_split_with_remainder():
    assert split_bill(1000, 3) == [334, 333, 333]


def test_even_split_without_remainder():
    assert split_bill(900, 3) == [300, 300, 300]


def test_zero_total():
    assert split_bill(0, 2) == [0, 0]


def test_zero_people_raises_value_error():
    with pytest.raises(ValueError):
        split_bill(100, 0)


def test_negative_people_raises_value_error():
    with pytest.raises(ValueError):
        split_bill(100, -2)


def test_negative_total_raises_value_error():
    with pytest.raises(ValueError):
        split_bill(-1, 2)


def test_float_total_raises_type_error():
    with pytest.raises(TypeError):
        split_bill(100.0, 2)


def test_bool_people_raises_type_error():
    with pytest.raises(TypeError):
        split_bill(100, True)


def test_string_total_raises_type_error():
    with pytest.raises(TypeError):
        split_bill("100", 2)
