"""
Thin route registration helpers.

This module exposes `register_routes(app, chart, journal, posting_engine, ledger)`
which wires read-only endpoints to the provided Flask `app` using the
passed-in core services. No business logic, no persistence, no sample
transactions are created here — the module only adapts core objects for
presentation in templates.
"""

## Wireframe Phase: Phase 3 (Read-only Visibility)
# This module implements read-only route registration only. All routes are GET
# endpoints for inspection purposes. Mutation endpoints (POST/PUT/DELETE) are
# planned for Phase 4: Controlled Mutation.
from typing import List, Dict, Any
from flask import render_template, Blueprint, current_app
from decimal import Decimal
import logging

main = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


def _serialize_journal_entry(e) -> Dict[str, Any]:
    """Serialize a JournalEntry for template rendering."""
    lines = []
    for li in e.line_items:
        lines.append({
            "account_code": li.account_code,
            "side": li.side.value if hasattr(li.side, "value") else str(li.side),
            "amount": str(li.amount),
            "description": getattr(li, "description", None),
            "project_id": getattr(li, "project_id", None),
        })
    return {
        "id": e.id,
        "date": e.date.isoformat() if hasattr(e, "date") else None,
        "description": getattr(e, "description", None),
        "source_ref": getattr(e, "source_ref", None),
        "reference_type": getattr(e, "reference_type", {}).value if hasattr(e, "reference_type") else None,
        "project_id": getattr(e, "project_id", None),
        "lines": lines,
    }


def register_routes(app, chart, journal, posting_engine, ledger_view, url_prefix: str = ""):
    """Register thin, read-only routes on `app` using provided services.

    - `chart` must implement `export_dict()` (ChartOfAccounts)
    - `journal` must implement `all_entries()` (Journal)
    - `ledger_view` must implement `trial_balance()` (Ledger)

    The function registers a small blueprint and attaches it to `app`.
    """
    # Guard against double-registration of blueprint routes
    if "main" in app.blueprints:
        return

    @main.route("/")
    def index():
        """Home page with navigation."""
        try:
            return render_template("index.html", title="Home")
        except Exception as e:
            logger.error(f"Error rendering index page: {e}")
            return "Error loading page", 500

    @main.route("/chart-of-accounts")
    def chart_of_accounts():
        """Display Chart of Accounts."""
        try:
            accounts = chart.export_dict()
            logger.debug(f"Loaded {len(accounts)} accounts for chart display")
            return render_template("chart_of_accounts.html", title="Chart of Accounts", accounts=accounts)
        except Exception as e:
            logger.error(f"Error loading chart of accounts: {e}")
            return "Error loading Chart of Accounts", 500

    @main.route("/journal-entries")
    def journal_entries():
        """Display Journal Entries."""
        try:
            entries = [_serialize_journal_entry(e) for e in journal.all_entries()]
            logger.debug(f"Loaded {len(entries)} journal entries for display")
            return render_template("journal_entries.html", title="Journal Entries", entries=entries)
        except Exception as e:
            logger.error(f"Error loading journal entries: {e}")
            return "Error loading Journal Entries", 500

    @main.route("/ledger")
    def ledger_view_handler():
        """Display Trial Balance."""
        try:
            rows, total_debits, total_credits = ledger_view.trial_balance()

            # Filter out accounts with zero balances for cleaner display
            non_zero_rows = [
                r for r in rows
                if r.debit != Decimal(0) or r.credit != Decimal(0)
            ]

            serialized_rows: List[Dict[str, Any]] = []
            for r in non_zero_rows:
                serialized_rows.append({
                    "account_code": r.account_code,
                    "account_name": r.account_name,
                    "debit": str(r.debit),
                    "credit": str(r.credit),
                })

            logger.debug(
                f"Trial balance: {len(serialized_rows)} non-zero accounts, "
                f"total debits={total_debits}, total_credits={total_credits}"
            )

            return render_template(
                "ledger.html",
                title="Trial Balance",
                rows=serialized_rows,
                total_debits=str(total_debits),
                total_credits=str(total_credits),
            )
        except Exception as e:
            logger.error(f"Error loading trial balance: {e}")
            return "Error loading Trial Balance", 500

    def _serialize_ledger_entry(e) -> Dict[str, Any]:
        """Serialize a LedgerEntry for template rendering."""
        return {
            "id": e.id,
            "journal_entry_id": e.journal_entry_id,
            "account_code": e.account_code,
            "amount": str(e.amount),
            "side": e.side.value if hasattr(e.side, "value") else str(e.side),
            "timestamp": e.timestamp.isoformat() if hasattr(e, "timestamp") else None,
            "description": getattr(e, "description", None),
            "project_id": getattr(e, "project_id", None),
        }

    @main.route("/ledger/account/<int:account_code>")
    def ledger_account(account_code: int):
        """Display General Ledger for a specific account."""
        try:
            # Get human-friendly account info from the chart
            account = chart.get_account(account_code)
            if account is None:
                logger.warning(f"Account {account_code} not found")
                return f"Account {account_code} not found", 404

            account_name = account.name

            # Ledger entries for the account (read-only view)
            entries = ledger_view.general_ledger(account_code)
            serialized_entries: List[Dict[str, Any]] = [
                _serialize_ledger_entry(e) for e in entries
            ]

            # Totals come from the posting engine
            totals = posting_engine.get_account_totals(account_code)

            logger.debug(
                f"Account {account_code} ledger: {len(entries)} entries, "
                f"debits={totals['debits']}, credits={totals['credits']}"
            )

            # Calculate running balance
            running_balance = Decimal(0)
            for entry in serialized_entries:
                if entry['side'] == 'debit':
                    running_balance += Decimal(entry['amount'])
                else:
                    running_balance -= Decimal(entry['amount'])
                entry['running_balance'] = str(running_balance)

            return render_template(
                "ledger_account.html",
                title=f"Ledger — {account_name}",
                account_code=account_code,
                account_name=account_name,
                account_type=account.type.value,
                entries=serialized_entries,
                total_debits=str(totals.get("debits")),
                total_credits=str(totals.get("credits")),
                net_balance=str(running_balance),
            )
        except Exception as e:
            logger.error(f"Error loading ledger for account {account_code}: {e}")
            return f"Error loading account {account_code} ledger", 500

    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors."""
        logger.warning(f"404 error: {e}")
        return render_template("error.html", error_code=404, error_message="Page not found"), 404

    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 errors."""
        logger.error(f"500 error: {e}")
        return render_template("error.html", error_code=500, error_message="Internal server error"), 500

    # attach blueprint under optional prefix
    app.register_blueprint(main, url_prefix=url_prefix or None)


__all__ = ["register_routes", "main"]
