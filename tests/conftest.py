import pytest
from dscrtools.data.schema import LoanParams, NOISchedule


@pytest.fixture
def standard_loan():
    return LoanParams(
        loan_amount=8_000_000,
        interest_rate=0.065,
        amortization_years=30,
        loan_term_years=10,
        interest_method="fixed_30_360",
        payments_per_year=12,
        property_name="Midtown Office Building",
    )


@pytest.fixture
def io_loan():
    return LoanParams(
        loan_amount=8_000_000,
        interest_rate=0.065,
        amortization_years=30,
        loan_term_years=10,
        interest_method="interest_only",
        payments_per_year=12,
    )


@pytest.fixture
def partial_io_loan():
    return LoanParams(
        loan_amount=8_000_000,
        interest_rate=0.065,
        amortization_years=30,
        loan_term_years=10,
        interest_method="partial_io",
        io_periods=24,
        payments_per_year=12,
    )


@pytest.fixture
def arm_loan():
    return LoanParams(
        loan_amount=8_000_000,
        interest_rate=0.055,
        amortization_years=30,
        loan_term_years=10,
        interest_method="arm",
        payments_per_year=12,
        rate_floor=0.04,
        rate_cap=0.10,
    )


@pytest.fixture
def sample_noi():
    return NOISchedule(
        base_noi=750_000,
        growth_rate=0.03,
        vacancy_rate=0.05,
        capex_reserve=10_000,
    )
