import pytest

def test_pytest():
	assert 1 == 1

def divide_by_zero():
	1 / 0

def test_fail():
	with pytest.raises(ZeroDivisionError):
		divide_by_zero()

