"""
Maximum loan sizing based on DSCR, LTV, and Debt Yield constraints.
"""
from dataclasses import dataclass
from dscrtools.data.schema import LoanParams
from dscrtools.models.amortization import schedule as amort_schedule


@dataclass
class SizingResult:
    max_loan_dscr: float
    max_loan_ltv: float
    max_loan_dy: float
    binding_constraint: str
    max_loan_amount: float
    property_value: float
    noi: float
    dscr_at_max: float
    ltv_at_max: float
    dy_at_max: float


def size_loan(
    loan_template: LoanParams,
    noi: float,
    property_value: float,
    min_dscr: float = 1.25,
    max_ltv: float = 0.75,
    min_debt_yield: float = 0.08,
) -> SizingResult:
    """
    Compute maximum loan amount based on DSCR, LTV, and Debt Yield tests.
    The binding constraint (lowest max loan) determines the actual max.
    """
    lo, hi = 100_000, property_value * 1.5
    for _ in range(60):
        mid = (lo + hi) / 2
        test_loan = LoanParams(
            loan_amount=mid,
            interest_rate=loan_template.interest_rate,
            amortization_years=loan_template.amortization_years,
            loan_term_years=loan_template.loan_term_years,
            interest_method=loan_template.interest_method,
            io_periods=loan_template.io_periods,
            payments_per_year=loan_template.payments_per_year,
        )
        amort = amort_schedule(test_loan)
        annual_ds = sum(p["payment"] for p in amort[:loan_template.payments_per_year])
        dscr = noi / annual_ds if annual_ds > 0 else float("inf")
        if dscr > min_dscr:
            lo = mid
        else:
            hi = mid
    max_loan_dscr = round(lo, -3)

    max_loan_ltv = round(property_value * max_ltv, -3)
    max_loan_dy  = round(noi / min_debt_yield, -3)

    candidates = {
        "DSCR":       max_loan_dscr,
        "LTV":        max_loan_ltv,
        "Debt Yield": max_loan_dy,
    }
    binding   = min(candidates, key=candidates.get)
    max_loan  = candidates[binding]

    test_loan = LoanParams(
        loan_amount=max_loan,
        interest_rate=loan_template.interest_rate,
        amortization_years=loan_template.amortization_years,
        loan_term_years=loan_template.loan_term_years,
        interest_method=loan_template.interest_method,
        io_periods=loan_template.io_periods,
        payments_per_year=loan_template.payments_per_year,
    )
    amort      = amort_schedule(test_loan)
    annual_ds  = sum(p["payment"] for p in amort[:loan_template.payments_per_year])

    result = SizingResult(
        max_loan_dscr=max_loan_dscr,
        max_loan_ltv=max_loan_ltv,
        max_loan_dy=max_loan_dy,
        binding_constraint=binding,
        max_loan_amount=max_loan,
        property_value=property_value,
        noi=noi,
        dscr_at_max=round(noi / annual_ds, 2) if annual_ds > 0 else 0,
        ltv_at_max=round(max_loan / property_value, 4),
        dy_at_max=round(noi / max_loan, 4) if max_loan > 0 else 0,
    )

    print(f"\nLoan Sizing Analysis")
    print("=" * 55)
    print(f"  NOI:                   ${noi:,.0f}")
    print(f"  Property Value:        ${property_value:,.0f}")
    print(f"  Max Loan (DSCR {min_dscr:.2f}x): ${max_loan_dscr:,.0f}")
    print(f"  Max Loan (LTV {max_ltv:.0%}):   ${max_loan_ltv:,.0f}")
    print(f"  Max Loan (DY {min_debt_yield:.0%}):    ${max_loan_dy:,.0f}")
    print(f"  Binding:               {binding}")
    print(f"  Max Loan Amount:       ${max_loan:,.0f}")
    print(f"  DSCR at Max:           {result.dscr_at_max:.2f}x")
    print(f"  LTV at Max:            {result.ltv_at_max:.1%}")
    print(f"  Debt Yield at Max:     {result.dy_at_max:.1%}")
    print()

    return result
