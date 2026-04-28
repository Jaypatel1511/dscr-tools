"""
Interest calculation methods for different loan conventions.
Handles 30/360, Actual/360, Actual/365, interest-only, partial I/O, and ARM.
"""
import math
from dscrtools.data.schema import LoanParams


def periodic_payment(loan: LoanParams, balance: float = None,
                     rate: float = None) -> float:
    """
    Compute the standard periodic payment (P&I) using the loan params.

    Args:
        loan:    LoanParams instance
        balance: Override balance (default: loan.loan_amount)
        rate:    Override periodic rate (default: loan.periodic_rate)

    Returns:
        Periodic payment amount
    """
    balance = balance if balance is not None else loan.loan_amount
    rate = rate if rate is not None else loan.periodic_rate
    n = loan.amortization_periods

    if rate == 0:
        return balance / n

    return balance * (rate * (1 + rate) ** n) / ((1 + rate) ** n - 1)


def interest_payment(loan: LoanParams, balance: float,
                     rate: float = None) -> float:
    """
    Compute interest due for a single period.

    Adjusts for day-count convention:
    - 30/360:      rate / periods_per_year (standard)
    - Actual/360:  rate / 360 * 30 (slightly higher than 30/360)
    - Actual/365:  rate / 365 * (365/periods_per_year)
    """
    rate = rate if rate is not None else loan.interest_rate
    method = loan.interest_method

    if method in ("fixed_30_360", "interest_only",
                  "partial_io", "arm"):
        return balance * (rate / loan.payments_per_year)

    elif method == "fixed_actual_360":
        # Actual/360: assumes 30-day months, 360-day year
        days_per_period = 360 / loan.payments_per_year
        return balance * (rate / 360) * days_per_period

    elif method == "fixed_actual_365":
        days_per_period = 365 / loan.payments_per_year
        return balance * (rate / 365) * days_per_period

    return balance * (rate / loan.payments_per_year)


def is_io_period(loan: LoanParams, period: int) -> bool:
    """Return True if this period falls within the interest-only phase."""
    if loan.interest_method == "interest_only":
        return True
    if loan.interest_method == "partial_io":
        return period <= loan.io_periods
    return False


def arm_rate(loan: LoanParams, period: int,
             rate_adjustments: dict = None) -> float:
    """
    Return the applicable rate for an ARM loan at a given period.

    Args:
        loan:             LoanParams with ARM method
        period:           Current period number
        rate_adjustments: Dict of {period: new_rate} overrides

    Returns:
        Effective rate for the period (clamped to floor/cap)
    """
    if rate_adjustments and period in rate_adjustments:
        raw_rate = rate_adjustments[period]
    else:
        raw_rate = loan.interest_rate

    return max(loan.rate_floor, min(loan.rate_cap, raw_rate))


def balloon_balance(loan: LoanParams,
                    rate_adjustments: dict = None) -> float:
    """
    Compute the outstanding principal at end of loan term (balloon payment).

    Args:
        loan: LoanParams where loan_term_years < amortization_years

    Returns:
        Remaining principal balance at loan maturity
    """
    from dscrtools.models.amortization import schedule
    sched = schedule(loan, rate_adjustments=rate_adjustments)
    return sched[-1]["ending_balance"]
