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
from flask import render_template, Blueprint
from decimal import Decimal

main = Blueprint("main", __name__)


def _serialize_journal_entry(e) -> Dict[str, Any]:
    lines = []
    for li in e.line_items:
        lines.append({
            "account_code": li.account_code,
            "side": li.side.value if hasattr(li.side, "value") else str(li.side),
            "amount": str(li.amount),
            "description": getattr(li, "description", None),
        })
    return {
        "id": e.id,
        "date": e.date.isoformat() if hasattr(e, "date") else None,
        "description": getattr(e, "description", None),
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
        return render_template("index.html", title="Home")

    @main.route("/chart-of-accounts")
    def chart_of_accounts():
        accounts = chart.export_dict()
        return render_template("chart_of_accounts.html", title="Chart of Accounts", accounts=accounts)

    @main.route("/journal-entries")
    def journal_entries():
        entries = [_serialize_journal_entry(e) for e in journal.all_entries()]
        return render_template("journal_entries.html", title="Journal Entries", entries=entries)

    @main.route("/ledger")
    def ledger_view_handler():
        rows, total_debits, total_credits = ledger_view.trial_balance()
        serialized_rows: List[Dict[str, Any]] = []
        for r in rows:
            serialized_rows.append({
                "account_code": r.account_code,
                "account_name": r.account_name,
                "debit": str(r.debit),
                "credit": str(r.credit),
            })

        return render_template(
            "ledger.html",
            title="Ledger",
            rows=serialized_rows,
            total_debits=str(total_debits if isinstance(total_debits, Decimal) else total_debits),
            total_credits=str(total_credits if isinstance(total_credits, Decimal) else total_credits),
        )

    def _serialize_ledger_entry(e) -> Dict[str, Any]:
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
        # Get human-friendly account info from the chart
        account = chart.get_account(account_code)
        account_name = account.name if account is not None else "(Unknown)"

        # Ledger entries for the account (read-only view)
        entries = ledger_view.general_ledger(account_code)
        serialized_entries: List[Dict[str, Any]] = [_serialize_ledger_entry(e) for e in entries]

        # Totals come from the posting engine
        totals = posting_engine.get_account_totals(account_code)

        return render_template(
            "ledger_account.html",
            title=f"Ledger — {account_code}",
            account_code=account_code,
            account_name=account_name,
            entries=serialized_entries,
            total_debits=str(totals.get("debits")),
            total_credits=str(totals.get("credits")),
        )

    # attach blueprint under optional prefix
    app.register_blueprint(main, url_prefix=url_prefix or None)


__all__ = ["register_routes", "main"]
