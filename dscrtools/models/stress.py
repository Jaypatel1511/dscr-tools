"""
Stress testing — rate shocks, NOI declines, and scenario analysis.
"""
import pandas as pd
from dscrtools.data.schema import LoanParams, NOISchedule
from dscrtools.models.dscr import analyze


def rate_shock(
    loan: LoanParams,
    noi_schedule: NOISchedule,
    rate_shocks: list,
    min_dscr: float = 1.25,
) -> pd.DataFrame:
    """Test DSCR across a range of interest rate increases."""
    results = {}
    base = analyze(loan, noi_schedule, min_dscr=min_dscr)
    results["Base"] = {r.year: r.dscr for r in base}

    for shock in rate_shocks:
        shocked_loan = LoanParams(
            loan_amount=loan.loan_amount,
            interest_rate=min(loan.interest_rate + shock, loan.rate_cap),
            amortization_years=loan.amortization_years,
            loan_term_years=loan.loan_term_years,
            interest_method=loan.interest_method,
            io_periods=loan.io_periods,
            payments_per_year=loan.payments_per_year,
            rate_floor=loan.rate_floor,
            rate_cap=loan.rate_cap,
        )
        shocked = analyze(shocked_loan, noi_schedule, min_dscr=min_dscr)
        label = f"+{shock*100:.0f}bps"
        results[label] = {r.year: r.dscr for r in shocked}

    df = pd.DataFrame(results)
    df.index.name = "Year"
    print("\nRate Shock Sensitivity — DSCR by Year")
    print("=" * 60)
    print(df.round(2).to_string())
    print()
    return df


def noi_stress(
    loan: LoanParams,
    noi_schedule: NOISchedule,
    noi_haircuts: list,
    min_dscr: float = 1.25,
) -> pd.DataFrame:
    """Test DSCR across a range of NOI haircuts."""
    results = {}
    base = analyze(loan, noi_schedule, min_dscr=min_dscr)
    results["Base"] = {r.year: r.dscr for r in base}

    for haircut in noi_haircuts:
        stressed_noi = NOISchedule(
            base_noi=noi_schedule.base_noi * (1 - haircut),
            growth_rate=noi_schedule.growth_rate,
            vacancy_rate=noi_schedule.vacancy_rate,
            capex_reserve=noi_schedule.capex_reserve,
        )
        stressed = analyze(loan, stressed_noi, min_dscr=min_dscr)
        label = f"-{haircut*100:.0f}% NOI"
        results[label] = {r.year: r.dscr for r in stressed}

    df = pd.DataFrame(results)
    df.index.name = "Year"
    print("\nNOI Stress Sensitivity — DSCR by Year")
    print("=" * 60)
    print(df.round(2).to_string())
    print()
    return df


def break_even_noi(
    loan: LoanParams,
    min_dscr: float = 1.0,
) -> float:
    """Compute the minimum NOI required to maintain a given DSCR."""
    from dscrtools.models.amortization import schedule as amort_schedule
    amort = amort_schedule(loan)
    annual_ds = sum(p["payment"] for p in amort[:loan.payments_per_year])
    min_noi = annual_ds * min_dscr
    print(f"\nBreak-even NOI (DSCR = {min_dscr:.2f}x): ${min_noi:,.0f}")
    return min_noi
