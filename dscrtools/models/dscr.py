"""
DSCR calculation, covenant tracking, and period-by-period analysis.
"""
from dataclasses import dataclass
from typing import Optional
import pandas as pd

from dscrtools.data.schema import LoanParams, NOISchedule, DSCR_BENCHMARKS
from dscrtools.models.amortization import schedule as amort_schedule


@dataclass
class DSCRPeriod:
    """DSCR result for a single period."""
    year: int
    noi: float
    effective_noi: float
    debt_service: float
    dscr: float
    min_dscr: float
    status: str
    covenant_breach: bool
    default: bool
    excess_cash: float


def analyze(
    loan: LoanParams,
    noi_schedule: NOISchedule,
    min_dscr: float = 1.25,
    rate_adjustments: dict = None,
) -> list:
    """
    Compute DSCR for each year of the loan term.

    Args:
        loan:         LoanParams instance
        noi_schedule: NOISchedule with annual NOI projections
        min_dscr:     Minimum DSCR covenant threshold
        rate_adjustments: ARM rate overrides by period

    Returns:
        List of DSCRPeriod objects
    """
    amort = amort_schedule(loan, rate_adjustments=rate_adjustments)
    periods_per_year = loan.payments_per_year
    results = []

    for year in range(1, loan.loan_term_years + 1):
        # Get periods for this year
        start = (year - 1) * periods_per_year
        end = year * periods_per_year
        year_periods = amort[start:end]

        if not year_periods:
            break

        # Annual debt service
        annual_ds = sum(p["payment"] for p in year_periods)

        # NOI
        noi = noi_schedule.get_noi(year)
        effective_noi = noi_schedule.get_effective_noi(year)

        # DSCR
        dscr = effective_noi / annual_ds if annual_ds > 0 else float("inf")
        dscr = round(dscr, 4)

        covenant_breach = dscr < min_dscr
        default = dscr < 1.0
        excess_cash = max(effective_noi - annual_ds, 0)

        if default:
            status = "DEFAULT"
        elif covenant_breach:
            status = "BREACH"
        else:
            status = "OK"

        results.append(DSCRPeriod(
            year=year,
            noi=round(noi, 0),
            effective_noi=round(effective_noi, 0),
            debt_service=round(annual_ds, 0),
            dscr=dscr,
            min_dscr=min_dscr,
            status=status,
            covenant_breach=covenant_breach,
            default=default,
            excess_cash=round(excess_cash, 0),
        ))

    return results


def summary_table(results: list) -> pd.DataFrame:
    """Return DSCR analysis as a formatted DataFrame."""
    rows = []
    for r in results:
        rows.append({
            "Year":           r.year,
            "NOI ($)":        f"${r.noi:,.0f}",
            "Eff. NOI ($)":   f"${r.effective_noi:,.0f}",
            "Debt Service ($)": f"${r.debt_service:,.0f}",
            "DSCR":           f"{r.dscr:.2f}x",
            "Min DSCR":       f"{r.min_dscr:.2f}x",
            "Excess Cash ($)": f"${r.excess_cash:,.0f}",
            "Status":         r.status,
        })

    df = pd.DataFrame(rows)

    breaches = sum(1 for r in results if r.covenant_breach)
    defaults = sum(1 for r in results if r.default)
    min_dscr_val = min(r.dscr for r in results)

    print(f"\nDSCR Analysis")
    print("=" * 90)
    print(df.to_string(index=False))
    print("=" * 90)
    print(f"  Min DSCR:          {min_dscr_val:.2f}x")
    print(f"  Covenant Breaches: {breaches}")
    print(f"  Defaults:          {defaults}")
    print()

    return df
