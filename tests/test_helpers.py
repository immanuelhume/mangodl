import pytest
from mangodl.helpers import chunk, safe_to_int, find_int_between, parse_range_input


@pytest.fixture
def twelve_integers():
    return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


def test_chunk_overflow(twelve_integers):
    # size of chunk
    n = 5
    # expected output
    l_ = [[1, 2, 3, 4, 5],
          [6, 7, 8, 9, 10, 11, 12]]

    assert chunk(twelve_integers, n) == l_


def test_chunk_underflow(twelve_integers):
    # size of chunk
    n = 20
    # expected output
    l_ = [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]

    assert chunk(twelve_integers, n) == l_


def test_chunk_exact(twelve_integers):
    # size of chunk
    n = 4
    # expected output
    l_ = [[1, 2, 3, 4],
          [5, 6, 7, 8],
          [9, 10, 11, 12]]

    assert chunk(twelve_integers, n) == l_


def test_safe_to_int_given_int():
    # positive integer
    i = 1
    res = safe_to_int(i)
    assert isinstance(res, int)
    assert res == 1
    # negative integer
    i_ = -1
    res = safe_to_int(i_)
    assert isinstance(res, int)
    assert res == -1


def test_safe_to_int_given_float():
    # positive float
    i = 0.5
    res = safe_to_int(i)
    assert isinstance(res, float)
    assert res == 0.5
    # negative float
    i_ = -0.5
    res = safe_to_int(i_)
    assert isinstance(res, float)
    assert res == -0.5
    # positive float 'integer'
    j = 1.0
    res = safe_to_int(j)
    assert isinstance(res, int)
    assert res == 1
    # negative float 'integer'
    j_ = -1.0
    res = safe_to_int(j_)
    assert isinstance(res, int)
    assert res == -1


def test_safe_to_int_given_str():
    # input
    s = 'i think this is a number'
    res = safe_to_int(s)
    assert res == s


def test_find_int_between_integers():
    # list to test
    l = [0, 1, 3, 6]
    # expected return value
    l_ = [2, 4, 5]

    assert find_int_between(l) == l_


def test_find_int_between_floats():
    # list to test
    l = [0.1, 1.1, 5.5, 6.1]
    # expected return value
    l_ = [1, 2, 3, 4, 5, 6]

    assert find_int_between(l) == l_


def test_find_int_between_float_and_int():
    # list to test
    l = [1, 1.5, 3, 5.5]
    # expected return value
    l_ = [2, 4, 5]

    assert find_int_between(l) == l_


def test_parse_range_input_single_inputs():
    # single range input
    i = '1-10'
    i_ = ['1-10']
    assert parse_range_input(i) == i_
    # single range input with whitespace
    i = ' 1  -   10    '
    assert parse_range_input(i) == i_
    # single number input
    j = '1'
    j_ = ['1']
    assert parse_range_input(j) == j_
    # single number input with whitespace
    j = ' 1  '
    assert parse_range_input(j) == j_


def test_parse_range_input_comma_separated():
    # comma separated ranges
    i = '1-5,10-15'
    i_ = ['1-5', '10-15']
    assert parse_range_input(i) == i_
    # comma separated ranges with whitespace
    i = ' 1  -   5    , 10  -  15   ,'
    assert parse_range_input(i) == i_
    # comma separated numbers
    j = '1,2,3,4'
    j_ = ['1', '2', '3', '4']
    assert parse_range_input(j) == j_
    # comma separated numbers with whitespace
    j = ' 1  ,   2  ,    3   ,    4     ,'
    assert parse_range_input(j) == j_


def test_parse_range_input_mixed():
    # a mixed input
    i = '1-10, 11, 12-20'
    i_ = ['1-10', '11', '12-20']
    assert parse_range_input(i) == i_
    # mixed input with whitespace
    i = ' 1  -   10    , 11  , 12  -    20  '
    assert parse_range_input(i) == i_
