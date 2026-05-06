"""
Full amortization schedule engine.
Supports all interest methods including I/O periods and ARM.
"""
import pandas as pd
from dscrtools.data.schema import LoanParams
from dscrtools.models.loan import (
    periodic_payment, interest_payment, is_io_period, arm_rate
)


def schedule(
    loan: LoanParams,
    rate_adjustments: dict = None,
) -> list:
    """
    Generate a complete amortization schedule period by period.

    Args:
        loan:             LoanParams instance
        rate_adjustments: Dict of {period: rate} for ARM adjustments

    Returns:
        List of dicts with period-by-period payment breakdown
    """
    rows = []
    balance = loan.loan_amount

    # Compute standard P&I payment (used after I/O period ends)
    # For partial_io: recompute payment on remaining balance after I/O
    std_payment = periodic_payment(loan)

    for period in range(1, loan.total_periods + 1):

        # Determine effective rate for this period
        if loan.interest_method == "arm":
            rate = arm_rate(loan, period, rate_adjustments)
        else:
            rate = loan.interest_rate

        # Interest due this period
        interest = interest_payment(loan, balance, rate=rate)

        # Determine if this is an I/O period
        io = is_io_period(loan, period)

        if io:
            principal = 0.0
            payment = interest
        else:
            if loan.interest_method == "partial_io" and period == loan.io_periods + 1:
                # Recompute payment on remaining balance after I/O period
                # Use correct periodic rate based on day-count convention
                remaining_periods = loan.amortization_periods - loan.io_periods
                if loan.interest_method == "fixed_actual_360":
                    days_per_period = 360 / loan.payments_per_year
                    r = (rate / 360) * days_per_period
                elif loan.interest_method == "fixed_actual_365":
                    days_per_period = 365 / loan.payments_per_year
                    r = (rate / 365) * days_per_period
                else:
                    r = rate / loan.payments_per_year
                if r == 0:
                    std_payment = balance / remaining_periods
                else:
                    std_payment = balance * (r * (1 + r) ** remaining_periods) / \
                                  ((1 + r) ** remaining_periods - 1)

            payment = min(std_payment, balance + interest)
            principal = payment - interest
            principal = min(principal, balance)

        ending_balance = max(balance - principal, 0)

        rows.append({
            "period":          period,
            "beginning_balance": balance,
            "payment":         round(payment, 2),
            "interest":        round(interest, 2),
            "principal":       round(principal, 2),
            "ending_balance":  round(ending_balance, 2),
            "is_io":           io,
            "rate":            round(rate * 100, 4),
        })

        balance = ending_balance

        if balance <= 0.01:
            break

    return rows


def to_dataframe(loan: LoanParams,
                 rate_adjustments: dict = None) -> pd.DataFrame:
    """Return amortization schedule as a pandas DataFrame."""
    rows = schedule(loan, rate_adjustments=rate_adjustments)
    df = pd.DataFrame(rows)
    return df


def summary(loan: LoanParams,
            rate_adjustments: dict = None) -> pd.DataFrame:
    """Print and return a clean amortization schedule."""
    df = to_dataframe(loan, rate_adjustments=rate_adjustments)

    print(f"\nAmortization Schedule — {loan.property_name or 'Loan'}")
    print(f"{loan}")
    print("-" * 85)

    display = df.copy()
    for col in ["beginning_balance", "payment", "interest",
                "principal", "ending_balance"]:
        display[col] = display[col].apply(lambda x: f"${x:,.0f}")
    display["rate"] = display["rate"].apply(lambda x: f"{x:.3f}%")
    display["is_io"] = display["is_io"].apply(lambda x: "I/O" if x else "P&I")

    display = display.rename(columns={
        "period": "Period",
        "beginning_balance": "Beg Balance",
        "payment": "Payment",
        "interest": "Interest",
        "principal": "Principal",
        "ending_balance": "End Balance",
        "is_io": "Type",
        "rate": "Rate",
    })

    print(display.to_string(index=False))

    total_interest = df["interest"].sum()
    total_principal = df["principal"].sum()
    balloon = df["ending_balance"].iloc[-1]

    print("-" * 85)
    print(f"  Total Interest Paid:  ${total_interest:,.0f}")
    print(f"  Total Principal Paid: ${total_principal:,.0f}")
    if balloon > 0.01:
        print(f"  Balloon Payment:      ${balloon:,.0f}")
    print()

    return df
