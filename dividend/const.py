"""
xml column names and output names
"""
# excel sheet names
DIVIDEND_SUMMARY = "dividend summary"
DIVIDEND_DATA = "dividend data"
INTEREST_DATA = 'interest data'

# interactive brokers xml column names
CURRENCY = 'currency'
LISTING_EXCHANGE = 'listingExchange'
SYMBOL = 'symbol'
TYPE = 'type'
FX_RATE_TO_BASE = 'fxRateToBase'
GROSS_DIVIDEND = 'Gross dividend'
AMOUNT = 'amount'
SETTLE_DATE = 'settleDate'
ISIN = 'isin'
DESCRIPTION = 'description'

# interactive brokers cash transaction type
IN_LIEU_OF_DIVIDENDS = "Payment In Lieu Of Dividends"
WITHHOLDING_TAX = 'Withholding Tax'
DIVIDENDS = "Dividends"
DIVIDEND_TYPE = [IN_LIEU_OF_DIVIDENDS, WITHHOLDING_TAX, DIVIDENDS]
BOND_INTEREST = "Bond Interest Received"
BROKER_INTEREST_RECEIVED = "Broker Interest Received"
BROKER_INTEREST_PAID = "Broker Interest Paid"
INTEREST_INCOME = [BOND_INTEREST, BROKER_INTEREST_RECEIVED]

# output names
TAX_IN_STERLING = 'Withholding Tax in Sterling'
DIVIDEND_IN_STERLING = 'Gross Dividend in Sterling'
INTEREST_IN_STERLING = 'Gross Interest in Sterling'
COUNTRY = 'country'
INTEREST_COLUMN = [SETTLE_DATE, DESCRIPTION, TYPE, AMOUNT, CURRENCY, FX_RATE_TO_BASE, INTEREST_IN_STERLING]
