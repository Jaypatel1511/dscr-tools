import pytest
import pandas as pd
from dscrtools.models.amortization import schedule, to_dataframe, summary


def test_schedule_returns_list(standard_loan):
    sched = schedule(standard_loan)
    assert isinstance(sched, list)
    assert len(sched) == standard_loan.total_periods


def test_schedule_interest_only(io_loan):
    sched = schedule(io_loan)
    for row in sched:
        assert row["principal"] == 0.0
        assert row["is_io"] is True


def test_schedule_partial_io_transitions(partial_io_loan):
    sched = schedule(partial_io_loan)
    assert sched[0]["is_io"] is True
    assert sched[23]["is_io"] is True
    assert sched[24]["is_io"] is False


def test_balance_decreases_after_io(partial_io_loan):
    sched = schedule(partial_io_loan)
    io_balance = sched[23]["ending_balance"]
    amort_balance = sched[25]["ending_balance"]
    assert amort_balance < io_balance


def test_to_dataframe_returns_df(standard_loan):
    df = to_dataframe(standard_loan)
    assert isinstance(df, pd.DataFrame)
    assert "payment" in df.columns
    assert "interest" in df.columns
    assert "principal" in df.columns


def test_total_principal_equals_loan(standard_loan):
    df = to_dataframe(standard_loan)
    balloon = df["ending_balance"].iloc[-1]
    total_principal = df["principal"].sum() + balloon
    assert abs(total_principal - standard_loan.loan_amount) < 10


def test_summary_returns_dataframe(standard_loan):
    df = summary(standard_loan)
    assert isinstance(df, pd.DataFrame)


def test_arm_schedule_runs(arm_loan):
    sched = schedule(arm_loan, rate_adjustments={13: 0.075, 25: 0.085})
    assert len(sched) == arm_loan.total_periods


def test_actual_360_partial_io_payment_correct():
    """Actual/360 payment after I/O period should use correct day-count rate."""
    from dscrtools.data.schema import LoanParams
    from dscrtools.models.amortization import to_dataframe

    loan = LoanParams(
        loan_amount=1_000_000,
        interest_rate=0.06,
        amortization_years=30,
        loan_term_years=10,
        interest_method="partial_io",
        io_periods=12,
        payments_per_year=12,
    )
    df = to_dataframe(loan)

    io_rows = df[df["is_io"] == True]
    pi_rows = df[df["is_io"] == False]
    assert len(io_rows) == 12
    assert len(pi_rows) > 0
    first_pi_payment = pi_rows["payment"].iloc[0]
    last_io_payment = io_rows["payment"].iloc[-1]
    assert first_pi_payment > last_io_payment
