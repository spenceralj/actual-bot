import os
from collections import defaultdict
from datetime import date
from decimal import Decimal

from actual import Actual
from actual.queries import get_accounts, get_transactions

_actual_client = None

def format_decimal(decimal):
    return round(float(decimal), 2)

def get_actual():
    global _actual_client
    if _actual_client == None:
        _actual_client = Actual(
            base_url=os.getenv("ACTUAL_URL", "https://localhost:5006"),
            password=os.getenv("ACTUAL_PASSWORD"),
            file=os.getenv("ACTUAL_SYNC_ID"),
        ).__enter__()
    else:
        _actual_client.sync()

    return _actual_client


def list_accounts():
    """
    Retrieves current balances for all active on-budget and off-budget accounts.
    Use this tool whenever the user asks:
    - How much money they have in specific accounts (e.g. 'checking balance', 'savings').
    - What their current credit card debt or account balances look like.
    - Total financial net worth calculations.
    """
    actual = get_actual()

    accounts = {"on-budget": {}, "off-budget": {}}

    for account in get_accounts(actual.session):
        if account.closed:
            continue

        if account.offbudget:
            accounts["off-budget"][account.name] = format_decimal(account.balance)
        else:
            accounts["on-budget"][account.name] = format_decimal(account.balance)

    return accounts


def list_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
    payee: str | None = None,
    category: str | None = None,
    transfer: bool | None = None,
    limit: int = 10,
):
    """
    Searches and retrieves individual itemized transactions with store/payee names,
    amounts, dates, categories, and account names.
    Use this tool for:
    - Finding recent purchases (e.g., 'What were my last 5 purchases?').
    - Looking up spending at a specific merchant (e.g., 'How much did I spend at Amazon?').
    - Getting specific purchase examples to accompany a category spending review.
    Args:
        start_date: Optional start date in YYYY-MM-DD format.
        end_date: Optional end date in YYYY-MM-DD format.
        payee: Optional merchant/store name to filter by (e.g. 'Amazon', 'Starbucks', 'Costco').
        category: Optional category name to filter by (e.g. 'Eating Out', 'Groceries').
        transfer: Set True for transfers between accounts, False to exclude transfers, or None for all.
        limit: Maximum number of transactions to return (default 10, keep small for quick summaries).
    """

    client = get_actual()

    start = None
    end = None

    if start_date and end_date:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

    transactions = []

    for transaction in get_transactions(
        client.session,
        start_date=start,
        end_date=end,
        payee=payee,
        category=category,
        transfer=transfer,
    ):
        trans_info = {
            "amount": format_decimal(transaction.get_amount()),
            "payee": transaction.payee.name if transaction.payee else "",
            "category": transaction.category.name if transaction.category else "",
            "account": transaction.account.name,
            "date": str(transaction.get_date()),
            "notes": transaction.notes,
        }

        transactions.append(trans_info)
        if len(transactions) >= limit:
            break

    return transactions


def get_aggregate_analytics(
    start_date: str,
    end_date: str,
    group_by: str = "category",
    is_income: bool = False,
    category: str | None = None,
    payee: str | None = None,
):
    """
    General-purpose financial aggregator for spending and income.
    Calculates totals broken down by 'category', 'month', or 'payee'.
    Args:
        start_date: Start date YYYY-MM-DD
        end_date: End date YYYY-MM-DD
        group_by: How to group the results. Allowed values: 'category', 'month', 'payee'.
        is_income: Set to True to calculate earnings/income/paychecks. Set to False (default) to calculate spending/expenses.
        category: Optional category filter.
        payee: Optional payee/merchant filter.
    """

    client = get_actual()

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    analytics = defaultdict(Decimal)

    for transaction in get_transactions(
        client.session,
        start_date=start,
        end_date=end,
        category=category,
        payee=payee,
        transfer=False,
    ):
        if (transaction.category.is_income if transaction.category else False) != is_income:
            continue

        amount = transaction.get_amount() if is_income else (-1) * transaction.get_amount()

        if group_by == "category":
            if transaction.category is None:
                analytics["uncategorized"] += amount
                continue

            analytics[transaction.category.name] += amount

        if group_by == "month":
            analytics[transaction.get_date().strftime("%Y-%m")] += amount

        if group_by == "payee":
            if transaction.payee is None:
                analytics["no payee"] += amount
                continue

            analytics[transaction.payee.name] += amount

    float_analytics = {key: format_decimal(val) for key, val in analytics.items()}
    return float_analytics
