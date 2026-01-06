"""Ledger: derives account balances from journal postings.

The Ledger is a READ-ONLY view that aggregates journal lines by account
and derives balances. It never stores balances—they are calculated on demand
respecting each account's NormalBalance.

Responsibilities:
- Aggregate journal lines by account
- Respect NormalBalance when interpreting debit/credit totals
- Produce account balances and trial balance views
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from .account import Account, ChartOfAccounts, NormalBalance, AccountType
from .posting_engine import PostingEngine, LedgerEntry
from .journal_entry import EntrySide


@dataclass
class AccountBalance:
    """A read-only view of a single account's balance.

    The balance is derived from ledger entries and respects the account's
    NormalBalance. A positive balance means the account is in its normal state;
    negative means it has an unusual (contra) balance.
    """

    account: Account
    debit_total: Decimal
    credit_total: Decimal
    # balance = (debits - credits) if normal balance is DEBIT,
    #         = (credits - debits) if normal balance is CREDIT
    balance: Decimal

    @property
    def is_in_normal_balance(self) -> bool:
        """Return whether balance is in the account's normal direction."""
        if self.account.normal_balance == NormalBalance.DEBIT:
            return self.balance >= Decimal(0)
        elif self.account.normal_balance == NormalBalance.CREDIT:
            return self.balance <= Decimal(0)
        return True


@dataclass
class TrialBalanceRow:
    """A single row in the trial balance report."""

    account_code: int
    account_name: str
    debit: Decimal = Decimal(0)
    credit: Decimal = Decimal(0)


class Ledger:
    """A read-only ledger view derived from posting engine entries.

    All balances are calculated on demand from ledger entries. No balances
    are stored directly; the Ledger is purely a derived view.

    Responsibilities:
    - Aggregate ledger entries by account
    - Respect account NormalBalance when interpreting balances
    - Produce account balance queries
    - Produce trial balance reports
    """

    def __init__(self, chart: ChartOfAccounts, posting_engine: PostingEngine):
        """Initialize ledger with a chart and posting engine.

        Args:
            chart: ChartOfAccounts instance
            posting_engine: PostingEngine holding all ledger entries
        """
        self.chart = chart
        self.posting_engine = posting_engine

    def _get_account_totals(self, account_code: int) -> Tuple[Decimal, Decimal]:
        """Fetch debit and credit totals for an account from posting engine.

        Returns:
            (debit_total, credit_total)
        """
        totals = self.posting_engine.get_account_totals(account_code)
        return totals['debits'], totals['credits']

    def get_account_balance(self, account_code: int) -> Optional[AccountBalance]:
        """Get the balance for a specific account.

        Derives the balance respecting the account's NormalBalance.
        Returns None if account does not exist.

        Balance interpretation:
        - DEBIT normal: balance = debits - credits (positive is normal)
        - CREDIT normal: balance = credits - debits (positive is normal)
        """
        account = self.chart.get_account(account_code)
        if account is None:
            return None

        debit_total, credit_total = self._get_account_totals(account_code)

        # Respect normal balance when calculating balance
        if account.normal_balance == NormalBalance.DEBIT:
            balance = debit_total - credit_total
        elif account.normal_balance == NormalBalance.CREDIT:
            balance = credit_total - debit_total
        else:
            balance = debit_total - credit_total  # fallback

        return AccountBalance(
            account=account,
            debit_total=debit_total,
            credit_total=credit_total,
            balance=balance,
        )

    def account_balances(self) -> Dict[int, AccountBalance]:
        """Return balances for all accounts in the chart.

        Balances are derived on demand (not stored).
        Returns a dict: {account_code: AccountBalance}
        """
        balances = {}
        for account in self.chart.get_all_accounts():
            ab = self.get_account_balance(account.code)
            if ab is not None:
                balances[account.code] = ab
        return balances

    def trial_balance(self) -> Tuple[List[TrialBalanceRow], Decimal, Decimal]:
        """Produce a trial balance report.

        Returns:
            (rows, total_debits, total_credits)

        Each row shows an account code, name, and the debit/credit
        side of its balance (not the net balance). This ensures debits
        and credits balance to the same total.

        Accounts are ordered by code.
        """
        rows = []
        total_debits = Decimal(0)
        total_credits = Decimal(0)

        balances = self.account_balances()
        sorted_codes = sorted(balances.keys())

        for code in sorted_codes:
            ab = balances[code]
            account = ab.account
            balance_amount = abs(ab.balance)

            # Determine which side the balance goes on
            if account.normal_balance == NormalBalance.DEBIT:
                if ab.balance >= Decimal(0):
                    # Normal debit balance
                    debit_amt = balance_amount
                    credit_amt = Decimal(0)
                else:
                    # Contra (credit) balance
                    debit_amt = Decimal(0)
                    credit_amt = balance_amount
            elif account.normal_balance == NormalBalance.CREDIT:
                if ab.balance <= Decimal(0):
                    # Normal credit balance (note: balance is negative in this case)
                    debit_amt = Decimal(0)
                    credit_amt = balance_amount
                else:
                    # Contra (debit) balance
                    debit_amt = balance_amount
                    credit_amt = Decimal(0)
            else:
                # Fallback: assume debit
                debit_amt = balance_amount if ab.balance >= Decimal(0) else Decimal(0)
                credit_amt = balance_amount if ab.balance < Decimal(0) else Decimal(0)

            total_debits += debit_amt
            total_credits += credit_amt

            rows.append(
                TrialBalanceRow(
                    account_code=account.code,
                    account_name=account.name,
                    debit=debit_amt,
                    credit=credit_amt,
                )
            )

        return rows, total_debits, total_credits

    def general_ledger(self, account_code: int) -> List[LedgerEntry]:
        """Retrieve all ledger entries for a specific account.

        Useful for detailed account reconciliation.
        """
        return self.posting_engine.ledger_entries_for_account(account_code)

    def accounts_by_type(self, account_type: AccountType) -> Dict[int, AccountBalance]:
        """Get balances for all accounts of a specific type."""
        accounts = self.chart.get_accounts_by_type(account_type)
        balances = {}
        for acc in accounts:
            ab = self.get_account_balance(acc.code)
            if ab is not None:
                balances[acc.code] = ab
        return balances
