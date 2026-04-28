import pytest
from dscrtools.models.sizing import size_loan


def test_sizing_returns_result(standard_loan):
    result = size_loan(
        standard_loan,
        noi=750_000,
        property_value=12_000_000,
        min_dscr=1.25,
        max_ltv=0.75,
        min_debt_yield=0.08,
    )
    assert result.max_loan_amount > 0


def test_binding_constraint_is_lowest(standard_loan):
    result = size_loan(
        standard_loan,
        noi=750_000,
        property_value=12_000_000,
    )
    assert result.max_loan_amount == min(
        result.max_loan_dscr,
        result.max_loan_ltv,
        result.max_loan_dy,
    )


def test_dscr_at_max_near_minimum(standard_loan):
    result = size_loan(
        standard_loan,
        noi=750_000,
        property_value=12_000_000,
        min_dscr=1.25,
    )
    if result.binding_constraint == "DSCR":
        assert abs(result.dscr_at_max - 1.25) < 0.05


def test_ltv_at_max_within_limit(standard_loan):
    result = size_loan(
        standard_loan,
        noi=750_000,
        property_value=12_000_000,
        max_ltv=0.75,
    )
    assert result.ltv_at_max <= 0.76
