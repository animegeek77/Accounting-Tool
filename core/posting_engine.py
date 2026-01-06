"""Posting engine: converts validated JournalEntry objects into ledger postings.

Provides a lightweight in-memory ledger for testing and local use. Records
per-account debit/credit totals and individual ledger entries. Integrates
with `ChartOfAccounts` to validate account existence before posting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
import uuid

from .journal_entry import JournalEntry, LineItem, EntrySide, JournalError
from .account import ChartOfAccounts


class PostingError(JournalError):
    """Errors raised by the posting engine."""


@dataclass
class LedgerEntry:
    id: str
    journal_entry_id: str
    account_code: int
    amount: Decimal
    side: EntrySide
    timestamp: datetime
    description: Optional[str] = None
    project_id: Optional[str] = None
    tax_meta: Optional[Dict] = None


class PostingEngine:
    """In-memory posting engine.

    Responsibilities:
    - Post validated `JournalEntry` objects into ledger entries
    - Maintain per-account debit/credit totals
    - Support reversing entries
    """

    def __init__(self, chart: ChartOfAccounts):
        self.chart = chart
        self._ledger: List[LedgerEntry] = []
        # account_code -> { 'debits': Decimal, 'credits': Decimal }
        self._account_totals: Dict[int, Dict[str, Decimal]] = {}
        self._posted_entry_ids: set = set()

    def _ensure_account_totals(self, account_code: int) -> None:
        if account_code not in self._account_totals:
            self._account_totals[account_code] = {
                'debits': Decimal(0),
                'credits': Decimal(0),
            }

    def post(self, entry: JournalEntry) -> None:
        """Post a JournalEntry to the ledger.

        If the entry is not yet posted, this will call `entry.post(self.chart)`
        to validate and mark it posted. Then create ledger entries and update
        per-account totals.
        """
        if entry.id in self._posted_entry_ids:
            raise PostingError(f"JournalEntry {entry.id} already posted")

        # Ensure the entry has been validated and accounts exist
        if not entry.posted:
            entry.post(self.chart)

        # Create ledger entries
        for li in entry.line_items:
            # defensive check (should be covered by entry.post)
            if self.chart.get_account(li.account_code) is None:
                raise PostingError(f"Account {li.account_code} not found in chart")

            led = LedgerEntry(
                id=str(uuid.uuid4()),
                journal_entry_id=entry.id,
                account_code=li.account_code,
                amount=li.amount,
                side=li.side,
                timestamp=datetime.utcnow(),
                description=li.description,
                project_id=li.project_id,
                tax_meta=li.tax_meta,
            )
            self._ledger.append(led)

            # update totals
            self._ensure_account_totals(li.account_code)
            if li.side == EntrySide.DEBIT:
                self._account_totals[li.account_code]['debits'] += li.amount
            else:
                self._account_totals[li.account_code]['credits'] += li.amount

        self._posted_entry_ids.add(entry.id)

    def reverse(self, entry_id: str) -> JournalEntry:
        """Create and post a reversing JournalEntry for the given entry id.

        Returns the reversing JournalEntry.
        """
        from .journal_entry import JournalEntry as JE  # local import for clarity

        original = None
        for e in self._ledger:
            if e.journal_entry_id == entry_id:
                original = entry_id
                break

        if original is None:
            raise PostingError(f"Original journal entry {entry_id} not found in ledger")

        # We don't keep JournalEntry objects here; caller should manage them.
        # Look up stored JournalEntry via external store if needed. For now,
        # raising a clear error to indicate integration point.
        raise PostingError("Reverse requires access to original JournalEntry object; please call reverse on the JournalEntry and post it")

    def get_account_totals(self, account_code: int) -> Dict[str, Decimal]:
        """Return debit/credit totals for an account."""
        self._ensure_account_totals(account_code)
        return dict(self._account_totals[account_code])

    def get_account_balance(self, account_code: int) -> Decimal:
        """Return balance as (debits - credits). Interpretation of sign depends on account normal balance."""
        totals = self.get_account_totals(account_code)
        return totals['debits'] - totals['credits']

    def ledger_entries_for_account(self, account_code: int) -> List[LedgerEntry]:
        return [le for le in self._ledger if le.account_code == account_code]

    def all_ledger_entries(self) -> List[LedgerEntry]:
        return list(self._ledger)
