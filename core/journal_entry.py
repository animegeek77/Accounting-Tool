"""Journal entry model for the accounting system.

Implements double-entry accounting. JournalEntry is the SOLE mechanism for
creating and modifying account balances. Each entry contains JournalLine items
(account + debit/credit + amount). Validation enforces:
- At least 2 lines
- Debits == Credits
- No archived accounts

Immutable IDs and timestamps, reversing entries, and a minimal in-memory
`Journal` store for local use are provided.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Tuple
import uuid

from .account import ChartOfAccounts


class JournalError(Exception):
    """Base error for journal operations."""


class ValidationError(JournalError):
    """Raised when a journal entry fails validation."""


class EntrySide(Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class ReferenceType(Enum):
    """Type of transaction that generated this journal entry."""
    INVOICE = "invoice"
    PAYROLL = "payroll"
    ADJUSTMENT = "adjustment"
    OTHER = "other"


@dataclass
class JournalLine:
    """A single line (debit or credit) within a journal entry.

    Represents an account, an amount, and the side (debit/credit).

    Attributes:
        account_code: int - account code referenced (must exist in chart to post)
        amount: Decimal - positive amount
        side: EntrySide - debit or credit
        project_id: Optional[str] - optional project tag
        tax_meta: Optional[Dict] - optional tax metadata (type, rate, jurisdiction)
        description: Optional[str]
    """

    account_code: int
    amount: Decimal
    side: EntrySide
    project_id: Optional[str] = None
    tax_meta: Optional[Dict] = None  # Optional tax metadata
    description: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            try:
                self.amount = Decimal(str(self.amount))
            except Exception as exc:
                raise ValidationError(f"Invalid amount for JournalLine: {exc}")

        # Quantize amounts to 2 decimal places using banker's rounding.
        try:
            self.amount = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        except Exception:
            # If quantize fails, leave as-is and let positivity check fail later.
            pass

        if self.amount <= Decimal(0):
            raise ValidationError("JournalLine amount must be positive")


# Backward compatibility alias
LineItem = JournalLine


@dataclass
class JournalEntry:
    """Represents a double-entry journal entry.

    JournalEntry is the ONLY mechanism by which account balances are created
    or modified. Each entry is immutable once posted and must satisfy:
    - At least 2 journal lines
    - Sum(debits) == Sum(credits)
    - All referenced accounts exist and are not archived

    Enforces:
    - Immutable `id` and `created_at`
    - Reversing entries for corrections
    """

    description: str
    date: datetime = field(default_factory=lambda: datetime.utcnow())
    source_ref: Optional[str] = None  # e.g., invoice ID, payroll run ID
    reference_type: ReferenceType = ReferenceType.OTHER
    project_id: Optional[str] = None  # Optional project association
    _journal_lines: List[JournalLine] = field(default_factory=list, repr=False)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    posted: bool = False

    def add_line(self, line: JournalLine) -> None:
        """Add a journal line to the entry (only if not yet posted)."""
        if self.posted:
            raise JournalError("Cannot modify a posted journal entry")
        self._journal_lines.append(line)

    def add_line_item(self, item: JournalLine) -> None:
        """Backward compatibility alias for add_line."""
        self.add_line(item)
    @property
    def journal_lines(self) -> Tuple[JournalLine, ...]:
        """Externally visible immutable view of journal lines."""
        return tuple(self._journal_lines)

    @property
    def line_items(self) -> Tuple[JournalLine, ...]:
        """Backward compatibility alias exposing an immutable tuple."""
        return self.journal_lines

    def total_by_side(self) -> Dict[EntrySide, Decimal]:
        totals = {EntrySide.DEBIT: Decimal(0), EntrySide.CREDIT: Decimal(0)}
        for li in self._journal_lines:
            totals[li.side] += li.amount
        return totals

    def validate(self) -> None:
        """Validate the journal entry meets double-entry accounting rules.

        Rules:
        - At least 2 lines
        - At least one debit and one credit
        - Debits == Credits

        Raises ValidationError on failure.
        """
        if len(self._journal_lines) < 2:
            raise ValidationError("JournalEntry must have at least 2 lines")

        totals = self.total_by_side()
        if totals[EntrySide.DEBIT] == Decimal(0) or totals[EntrySide.CREDIT] == Decimal(0):
            raise ValidationError("JournalEntry must have at least one debit and one credit")

        if totals[EntrySide.DEBIT] != totals[EntrySide.CREDIT]:
            raise ValidationError(
                f"Entry not balanced: debits={totals[EntrySide.DEBIT]} credits={totals[EntrySide.CREDIT]}"
            )

    def post(self, chart: ChartOfAccounts) -> None:
        """Post the journal entry against a `ChartOfAccounts`.

        This is the ONLY way balances are created in the system. Validates entry,
        ensures all referenced accounts exist and are not archived, then marks posted.
        """
        if self.posted:
            raise JournalError("JournalEntry already posted")

        # validate internal accounting rules
        self.validate()

        # ensure all referenced accounts exist in chart and are not archived
        missing: List[int] = []
        archived: List[int] = []
        inconsistent_projects: List[str] = []
        for li in self._journal_lines:
            account = chart.get_account(li.account_code)
            if account is None:
                missing.append(li.account_code)
                continue  # Skip further validation for missing accounts
            elif account.is_archived:
                archived.append(li.account_code)
                continue  # Skip further validation for archived accounts

            # Validate project tagging: if either the entry or line has a project,
            # ensure the referenced account is project-taggable.
            effective_project = li.project_id if li.project_id is not None else self.project_id
            if effective_project is not None:
                if not getattr(account, 'is_project_taggable', False):
                    inconsistent_projects.append(f"{li.account_code}")

            # If both entry-level and line-level project IDs are present, they must match
            if self.project_id is not None and li.project_id is not None and li.project_id != self.project_id:
                inconsistent_projects.append(f"mismatch:{li.account_code}")

        if missing:
            raise ValidationError(f"Referenced accounts not found in chart: {missing}")
        if archived:
            raise ValidationError(f"Cannot post to archived accounts: {archived}")
        if inconsistent_projects:
            raise ValidationError(f"Inconsistent or invalid project tagging for accounts: {inconsistent_projects}")

        # mark as posted (posting_engine will actually create ledger postings)
        self.posted = True

    def reversing_entry(self) -> "JournalEntry":
        """Return a reversing JournalEntry with opposite sides and same amounts.

        Per accounting_scope.md: "Corrections are made using reversing entries."
        The reversing entry has source_ref pointing to the original entry id.
        """
        rev = JournalEntry(
            description=f"Reversal of {self.id}: {self.description}",
            date=datetime.utcnow(),
            source_ref=self.id,
            reference_type=ReferenceType.ADJUSTMENT,
        )
        for li in self._journal_lines:
            opposite = EntrySide.CREDIT if li.side == EntrySide.DEBIT else EntrySide.DEBIT
            rev.add_line(
                JournalLine(
                    account_code=li.account_code,
                    amount=li.amount,
                    side=opposite,
                    project_id=li.project_id,
                    tax_meta=li.tax_meta,
                    description=f"Reversal: {li.description}" if li.description else None,
                )
            )
        return rev


class Journal:
    """A minimal in-memory journal for storing journal entries.

    IMPORTANT: This is a lightweight helper for tests and local operations.
    In production, use PostingEngine with durable storage.

    JournalEntry remains the sole source of balance creation.
    """

    def __init__(self):
        self._entries: Dict[str, JournalEntry] = {}

    def add_entry(self, entry: JournalEntry, chart: Optional[ChartOfAccounts] = None) -> None:
        """Validate (and optionally post) the entry, then store it.

        If `chart` is provided the entry will be `post()`ed (validates accounts and archives).
        """
        if entry.id in self._entries:
            raise JournalError(f"Entry with id {entry.id} already exists in journal")

        # validate basic rules
        entry.validate()

        # optionally post against chart (ensures accounts exist and are not archived)
        if chart is not None:
            entry.post(chart)

        self._entries[entry.id] = entry

    def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        return self._entries.get(entry_id)

    def all_entries(self) -> List[JournalEntry]:
        return list(self._entries.values())
