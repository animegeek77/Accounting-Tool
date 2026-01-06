"""
Minimal Flask app wired to in-memory core objects.

Design notes (accountant perspective):
  `PostingEngine` (in-memory totals), and `Ledger` (read-only views).
  for accountants to inspect system state. No business logic, persistence,
  or seeded transactional data is added here.
"""
## Wireframe Phase
# Implements Phase 3: Read-only Visibility
#
# - Provides web UI for inspection of core accounting objects
# - Routes expose Chart of Accounts, Journal, and Ledger/Trial Balance
# - All endpoints read from in-memory data (no persistence)
# - No mutation endpoints yet (Phase 4: Controlled Mutation - planned)
# - No database integration yet (Phase 5: Persistence - planned)

from flask import Flask

# Use the package-level factory to create in-memory services and the
# routes module which contains frozen, read-only route registrations.
from app import make_in_memory_services
from app.routes import register_routes


app = Flask(__name__, static_folder='static', template_folder='templates')

# Create isolated in-memory services and register read-only routes.
chart, journal, posting_engine, ledger_view = make_in_memory_services()
register_routes(app, chart, journal, posting_engine, ledger_view)


if __name__ == '__main__':
    app.run(debug=True)

