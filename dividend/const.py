"""
xml column names and output names
"""


# interactive brokers xml column names
class ColumnName(str):
    """Keep track of the column names both imported from xml statement and output"""

    CURRENCY = "currency"
    LISTING_EXCHANGE = "listingExchange"
    SYMBOL = "symbol"
    TYPE = "type"
    FX_RATE_TO_BASE = "fxRateToBase"
    GROSS_DIVIDEND = "Gross dividend"
    AMOUNT = "amount"
    SETTLE_DATE = "settleDate"
    ISIN = "isin"
    DESCRIPTION = "description"
    TAX_IN_STERLING = "Withholding Tax in Sterling"
    DIVIDEND_IN_STERLING = "Gross Dividend in Sterling"
    INTEREST_IN_STERLING = "Gross Interest in Sterling"
    COUNTRY = "country"


# interactive brokers cash transaction type
class TransactionType(str):
    """Keep track of the possible transaction type"""

    IN_LIEU_OF_DIVIDENDS = "Payment In Lieu Of Dividends"
    WITHHOLDING_TAX = "Withholding Tax"
    DIVIDENDS = "Dividends"
    BOND_INTEREST = "Bond Interest Received"
    BROKER_INTEREST_RECEIVED = "Broker Interest Received"
    BROKER_INTEREST_PAID = "Broker Interest Paid"


INTEREST_COLUMN = [
    ColumnName.SETTLE_DATE,
    ColumnName.DESCRIPTION,
    ColumnName.TYPE,
    ColumnName.AMOUNT,
    ColumnName.CURRENCY,
    ColumnName.FX_RATE_TO_BASE,
    ColumnName.INTEREST_IN_STERLING,
]

INTEREST_INCOME = [
    TransactionType.BOND_INTEREST,
    TransactionType.BROKER_INTEREST_RECEIVED,
]

DIVIDEND_TYPE = [
    TransactionType.IN_LIEU_OF_DIVIDENDS,
    TransactionType.WITHHOLDING_TAX,
    TransactionType.DIVIDENDS,
]
