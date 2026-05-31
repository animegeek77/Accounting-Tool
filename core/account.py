"""
Account module for Line Media Solutions accounting system.

Implements the Chart of Accounts with immutable account codes and types,
hierarchical structure, and project-tagging support as defined in accounting_scope.md.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json


class AccountType(Enum):
    """Account types as per Chart of Accounts."""
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    INCOME = "Income"
    EXPENSE = "Expense"


class NormalBalance(Enum):
    """Normal balance side for accounts."""
    DEBIT = "debit"
    CREDIT = "credit"


class Account:
    """
    Represents a single account in the Chart of Accounts.
    
    Attributes:
        code (int): Immutable account code (e.g., 1010, 2050, 4010).
        name (str): Account name.
        type (AccountType): Immutable account type.
        is_project_taggable (bool): Whether transactions can be linked to projects.
        is_tax_relevant (bool): Whether account is marked for tax reporting.
        is_archived (bool): Whether account is archived (deprecated but not deleted).
        created_at (datetime): Timestamp when account was created.
    """

    def __setattr__(self, name, value):
        # Prevent changing immutable internals after initialization
        if getattr(self, '_initialized', False):
            if name in ('_code', 'code', '_type', 'type'):
                raise AttributeError(f"Cannot modify immutable attribute '{name}' on Account")
        object.__setattr__(self, name, value)
    
    def __init__(
        self,
        code: int,
        name: str,
        account_type: AccountType,
        is_project_taggable: bool = False,
        is_tax_relevant: bool = False,
        normal_balance: Optional[NormalBalance] = None,
        parent_code: Optional[int] = None,
    ):
        """
        Initialize an Account.
        
        Args:
            code: Immutable account code.
            name: Account name.
            account_type: Immutable account type.
            is_project_taggable: Whether transactions can link to projects.
            is_tax_relevant: Whether account is marked for tax reporting.
            
        Raises:
            ValueError: If code is invalid or already exists.
        """
        self._code = code
        self._name = name
        self._type = account_type
        self._is_project_taggable = is_project_taggable
        self._is_tax_relevant = is_tax_relevant
        # Normal balance (debit or credit). If not provided, callers should
        # default based on account type.
        self._normal_balance = normal_balance
        # Optional hierarchical parent account code
        self._parent_code = parent_code
        self._is_archived = False
        self._created_at = datetime.utcnow()
        # mark initialization complete for immutability enforcement
        object.__setattr__(self, '_initialized', True)
    
    @property
    def code(self) -> int:
        """Return immutable account code."""
        return self._code
    
    @property
    def name(self) -> str:
        """Return account name."""
        return self._name
    
    @property
    def type(self) -> AccountType:
        """Return immutable account type."""
        return self._type
    
    @property
    def is_project_taggable(self) -> bool:
        """Return whether account supports project tagging."""
        return self._is_project_taggable
    
    @property
    def is_tax_relevant(self) -> bool:
        """Return whether account is marked for tax reporting."""
        return self._is_tax_relevant
    
    @property
    def is_archived(self) -> bool:
        """Return whether account is archived."""
        return self._is_archived
    
    @property
    def created_at(self) -> datetime:
        """Return account creation timestamp."""
        return self._created_at

    @property
    def normal_balance(self) -> Optional[NormalBalance]:
        """Return the account's normal balance (DEBIT or CREDIT)."""
        return self._normal_balance

    @property
    def parent_code(self) -> Optional[int]:
        """Return parent account code if part of a hierarchy."""
        return self._parent_code

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation of the account for UI/config exports."""
        return {
            "code": self._code,
            "name": self._name,
            "type": self._type.value,
            "normal_balance": self._normal_balance.value if self._normal_balance else None,
            "project_taggable": bool(self._is_project_taggable),
            "tax_relevant": bool(self._is_tax_relevant),
            "archived": bool(self._is_archived),
            "parent_code": self._parent_code,
        }
    
    def archive(self) -> None:
        """
        Archive (deprecate) the account.
        
        Archived accounts are not deleted but are marked as inactive.
        Per accounting_scope.md: "Deprecated accounts may be archived but not deleted."
        """
        self._is_archived = True
    
    def __repr__(self) -> str:
        return (
            f"Account(code={self._code}, name='{self._name}', "
            f"type={self._type.value}, normal_balance={self._normal_balance}, archived={self._is_archived})"
        )


class ChartOfAccounts:
    """
    Manages the Chart of Accounts for the organization.
    
    Ensures account code and type immutability, hierarchical structure,
    and numbering convention compliance as per accounting_scope.md.
    """
    
    # Account code ranges per Chart of Accounts
    RANGES: Dict[str, tuple] = {
        "ASSET": (1000, 1999),
        "LIABILITY": (2000, 2999),
        "EQUITY": (3000, 3999),
        "INCOME": (4000, 4999),
        "EXPENSE": (5000, 7999),  # Includes Operating Expenses (6000-6999) and Taxes (7000-7999)
    }
    
    def __init__(self):
        """Initialize Chart of Accounts."""
        self._accounts = {}  # {code: Account}
        self._initialize_default_accounts()
    
    def _initialize_default_accounts(self) -> None:
        """
        Initialize the default Chart of Accounts as per chart_of_accounts.md.
        
        Includes accounts for:
        - Assets (1000–1999)
        - Liabilities (2000–2999)
        - Equity (3000–3999)
        - Income (4000–4999)
        - Cost of Services (5000–5999)
        - Operating Expenses (6000–6999)
        - Taxes (7000–7999)
        """
        # Assets (normal balance = DEBIT)
        self._add_default_account(1010, "Cash – Operating Account", AccountType.ASSET)
        self._add_default_account(1020, "Cash – Savings / Reserve", AccountType.ASSET)
        self._add_default_account(1030, "Mobile Money / Payment Wallets", AccountType.ASSET)
        self._add_default_account(1040, "Accounts Receivable", AccountType.ASSET)
        self._add_default_account(1050, "Prepaid Expenses", AccountType.ASSET)
        self._add_default_account(1060, "Client Advance Receipts (Trust / Holding)", AccountType.ASSET)
        self._add_default_account(1110, "Office Equipment", AccountType.ASSET)
        self._add_default_account(1120, "Computer & Production Equipment", AccountType.ASSET)
        # Accumulated Depreciation is a contra-asset: normal balance = CREDIT
        self._add_default_account(1130, "Accumulated Depreciation", AccountType.ASSET, normal_balance=NormalBalance.CREDIT)
        
        # Liabilities (normal balance = CREDIT)
        self._add_default_account(2010, "Accounts Payable", AccountType.LIABILITY)
        self._add_default_account(2020, "Accrued Expenses", AccountType.LIABILITY)
        self._add_default_account(2030, "Unearned Revenue (Client Retainers)", AccountType.LIABILITY)
        self._add_default_account(2040, "Payroll Liabilities", AccountType.LIABILITY)
        self._add_default_account(2050, "Tax Payable – VAT", AccountType.LIABILITY, is_tax_relevant=True)
        self._add_default_account(2060, "Tax Payable – Withholding", AccountType.LIABILITY, is_tax_relevant=True)
        self._add_default_account(2070, "Client Payables (Pass-Through Costs)", AccountType.LIABILITY)
        self._add_default_account(2110, "Loans Payable", AccountType.LIABILITY)
        
        # Equity (normal balance = CREDIT)
        self._add_default_account(3010, "Owner's Capital", AccountType.EQUITY)
        self._add_default_account(3020, "Retained Earnings", AccountType.EQUITY)
        self._add_default_account(3030, "Current Year Profit/(Loss)", AccountType.EQUITY)
        
        # Income (normal balance = CREDIT)
        self._add_default_account(4010, "Project Revenue", AccountType.INCOME, is_project_taggable=True)
        self._add_default_account(4020, "Retainer Revenue", AccountType.INCOME, is_project_taggable=True)
        self._add_default_account(4030, "Consulting & Strategy Revenue", AccountType.INCOME, is_project_taggable=True)
        self._add_default_account(4040, "Production & Creative Services Revenue", AccountType.INCOME, is_project_taggable=True)
        self._add_default_account(4110, "Interest Income", AccountType.INCOME)
        self._add_default_account(4120, "Miscellaneous Income", AccountType.INCOME)
        
        # Cost of Services (normal balance = DEBIT)
        self._add_default_account(5010, "Freelancers & Contractors", AccountType.EXPENSE, is_project_taggable=True)
        self._add_default_account(5020, "Project-Specific Ad Spend", AccountType.EXPENSE, is_project_taggable=True)
        self._add_default_account(5030, "Production Costs", AccountType.EXPENSE, is_project_taggable=True)
        self._add_default_account(5040, "Content & Media Purchases", AccountType.EXPENSE, is_project_taggable=True)
        self._add_default_account(5050, "Client Pass-Through Expenses", AccountType.EXPENSE, is_project_taggable=True)
        
        # Operating Expenses (normal balance = DEBIT)
        self._add_default_account(6010, "Salaries & Wages", AccountType.EXPENSE)
        self._add_default_account(6020, "Employer Payroll Taxes", AccountType.EXPENSE)
        self._add_default_account(6030, "Staff Benefits", AccountType.EXPENSE)
        self._add_default_account(6110, "Office Rent", AccountType.EXPENSE)
        self._add_default_account(6120, "Utilities", AccountType.EXPENSE)
        self._add_default_account(6130, "Internet & Communications", AccountType.EXPENSE)
        self._add_default_account(6140, "Software Subscriptions", AccountType.EXPENSE)
        self._add_default_account(6150, "Insurance", AccountType.EXPENSE)
        self._add_default_account(6210, "Advertising & Promotion", AccountType.EXPENSE)
        self._add_default_account(6220, "Client Entertainment", AccountType.EXPENSE)
        self._add_default_account(6310, "Accounting & Legal Fees", AccountType.EXPENSE)
        self._add_default_account(6320, "Consulting Fees", AccountType.EXPENSE)
        self._add_default_account(6410, "Depreciation Expense", AccountType.EXPENSE)
        
        # Taxes (represented as expense accounts; no separate TAX range)
        self._add_default_account(7010, "Income Tax Expense", AccountType.EXPENSE, is_tax_relevant=True)
        self._add_default_account(7020, "Withholding Tax Expense", AccountType.EXPENSE, is_tax_relevant=True)
        self._add_default_account(7030, "VAT Expense (Non-Recoverable)", AccountType.EXPENSE, is_tax_relevant=True)
    
    def _add_default_account(
        self,
        code: int,
        name: str,
        account_type: AccountType,
        is_project_taggable: bool = False,
        is_tax_relevant: bool = False,
        normal_balance: Optional[NormalBalance] = None,
        parent_code: Optional[int] = None,
    ) -> None:
        """Helper to add a default account during initialization."""
        # If normal_balance not explicitly provided, derive from account type
        if normal_balance is None:
            nb_map = {
                AccountType.ASSET: NormalBalance.DEBIT,
                AccountType.LIABILITY: NormalBalance.CREDIT,
                AccountType.EQUITY: NormalBalance.CREDIT,
                AccountType.INCOME: NormalBalance.CREDIT,
                AccountType.EXPENSE: NormalBalance.DEBIT,
            }
            normal_balance = nb_map.get(account_type)

        account = Account(code, name, account_type, is_project_taggable, is_tax_relevant, normal_balance=normal_balance, parent_code=parent_code)
        self._accounts[code] = account
    
    def add_account(
        self,
        code: int,
        name: str,
        account_type: AccountType,
        is_project_taggable: bool = False,
        is_tax_relevant: bool = False,
    ) -> Account:
        """
        Add a new account to the Chart of Accounts.
        
        Args:
            code: Account code (must follow numbering convention).
            name: Account name.
            account_type: Account type (immutable once created).
            is_project_taggable: Whether transactions can link to projects.
            is_tax_relevant: Whether account is marked for tax reporting.
        
        Returns:
            The newly created Account.
            
        Raises:
            ValueError: If code already exists, violates numbering convention,
                       or account type mismatch.
        """
        if code in self._accounts:
            raise ValueError(f"Account code {code} already exists.")
        
        if not self._validate_code_for_type(code, account_type):
            raise ValueError(
                f"Account code {code} does not match expected range for {account_type.value}."
            )
        
        # derive default normal balance
        nb_map = {
            AccountType.ASSET: NormalBalance.DEBIT,
            AccountType.LIABILITY: NormalBalance.CREDIT,
            AccountType.EQUITY: NormalBalance.CREDIT,
            AccountType.INCOME: NormalBalance.CREDIT,
            AccountType.EXPENSE: NormalBalance.DEBIT,
        }
        normal_balance = nb_map.get(account_type)

        account = Account(code, name, account_type, is_project_taggable, is_tax_relevant, normal_balance=normal_balance)
        self._accounts[code] = account
        return account
    
    def _validate_code_for_type(self, code: int, account_type: AccountType) -> bool:
        """Validate account code follows numbering convention for its type."""
        mapping = {
            AccountType.ASSET: self.RANGES['ASSET'],
            AccountType.LIABILITY: self.RANGES['LIABILITY'],
            AccountType.EQUITY: self.RANGES['EQUITY'],
            AccountType.INCOME: self.RANGES['INCOME'],
            AccountType.EXPENSE: self.RANGES['EXPENSE'],
        }
        if account_type not in mapping:
            # If no range defined, allow any code (for extensibility)
            return True
        min_code, max_code = mapping[account_type]
        return min_code <= code <= max_code
    
    def get_account(self, code: int) -> Optional[Account]:
        """Retrieve an account by code."""
        return self._accounts.get(code)
    
    def get_all_accounts(self) -> List[Account]:
        """Return all accounts."""
        return list(self._accounts.values())
    
    def get_accounts_by_type(self, account_type: AccountType) -> List[Account]:
        """Return all accounts of a specific type."""
        return [acc for acc in self._accounts.values() if acc.type == account_type]
    
    def get_project_taggable_accounts(self) -> List[Account]:
        """Return all accounts that support project tagging."""
        return [acc for acc in self._accounts.values() if acc.is_project_taggable]

    def get_child_accounts(self, parent_code: int) -> List[Account]:
        """Return accounts whose `parent_code` equals the provided code."""
        return [acc for acc in self._accounts.values() if getattr(acc, 'parent_code', None) == parent_code]

    def export_dict(self) -> List[Dict[str, Any]]:
        """Return a list-of-dicts representation of the chart suitable for JSON export.

        Accounts are ordered by code for deterministic output.
        """
        accounts = sorted(self._accounts.values(), key=lambda a: a.code)
        return [acc.to_dict() for acc in accounts]

    def export_json(self, indent: int = 2) -> str:
        """Return the chart as a JSON string (useful for UI/config)."""
        return json.dumps(self.export_dict(), indent=indent)
