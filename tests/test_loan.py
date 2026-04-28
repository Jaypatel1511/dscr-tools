import pytest
from dscrtools.data.schema import LoanParams, INTEREST_METHODS
from dscrtools.models.loan import (
    periodic_payment, interest_payment, is_io_period, arm_rate
)


def test_periodic_payment_positive(standard_loan):
    pmt = periodic_payment(standard_loan)
    assert pmt > 0


def test_periodic_payment_covers_interest(standard_loan):
    pmt = periodic_payment(standard_loan)
    interest = interest_payment(standard_loan, standard_loan.loan_amount)
    assert pmt > interest


def test_interest_only_no_principal(io_loan):
    assert is_io_period(io_loan, 1) is True
    assert is_io_period(io_loan, 120) is True


def test_partial_io_transitions(partial_io_loan):
    assert is_io_period(partial_io_loan, 1) is True
    assert is_io_period(partial_io_loan, 24) is True
    assert is_io_period(partial_io_loan, 25) is False


def test_arm_rate_clamped(arm_loan):
    rate = arm_rate(arm_loan, 1, rate_adjustments={1: 0.15})
    assert rate <= arm_loan.rate_cap


def test_arm_rate_floor(arm_loan):
    rate = arm_rate(arm_loan, 1, rate_adjustments={1: 0.01})
    assert rate >= arm_loan.rate_floor


def test_invalid_method_raises():
    with pytest.raises(ValueError, match="interest_method must be"):
        LoanParams(
            loan_amount=1_000_000,
            interest_rate=0.06,
            amortization_years=30,
            loan_term_years=10,
            interest_method="invalid_method",
        )


def test_actual_360_higher_than_30_360(standard_loan):
    base = interest_payment(standard_loan, 1_000_000)
    actual_loan = LoanParams(
        loan_amount=standard_loan.loan_amount,
        interest_rate=standard_loan.interest_rate,
        amortization_years=standard_loan.amortization_years,
        loan_term_years=standard_loan.loan_term_years,
        interest_method="fixed_actual_360",
    )
    actual = interest_payment(actual_loan, 1_000_000)
    assert actual >= base
