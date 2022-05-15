![Pylint](https://github.com/alexpung/taxCalculator/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/alexpung/taxCalculator/branch/development/graph/badge.svg?token=O5UGER8FEJ)](https://codecov.io/gh/alexpung/taxCalculator)

# taxCalculator

UK tax calculator for Interactive Broker

To help report UK tax for dividend and capital gain.

# What is included

1. XML downloader to download report from web flex query (\xml_import\importer.py)
2. Command line entry point main.py

# Current functionality

1. Parse Interactive Brokers trade data to Trade objects, then use these objects to calculate capital gain and loss
2. Parse Interactive Brokers dividend/dividend in lieu/Witholding tax and shows dividend by country and total income for the tax year specified
3. Show section 104 holdings and sell that are unmatched with a buy (i.e. short sale)
4. Allow user to specify the initial section 104 pool (in case old trades cannot be found) (\gui\init.toml)
5. Dividend and withholding tax list and summary in excel
   TBD: Capital gain report in excel

This project use Poetry to manage dependency. Or you can install the dependency yourself by looking at [tool.poetry.dependencies] at pyproject.toml
To set up:

1. pip install --user poetry
2. poetry install

# To use:

1. Put your xml statements (option required: statement of fund, CashTransactions, corporate actions, Trades with detail level: order)
2. execute main.py
3. A folder selector will pop up, select the folder where your statement is located.
4. Excel reports will be generated in the same folder.

# Design notes:

1. When a share forward or reverse split occurs it is assumed that the decimal shares will be kept. But it is possible that
   the decimal shares are lost and be given cash in lieu.
2. Share matching rules are implemented according to: https://rppaccounts.co.uk/taxation-of-shares/
   1. acquisitions on the same day as the disposal
   2. acquisitions within 30 days after the day of disposal (except where made by a non-resident). Disposals are identified first with securities acquired earlier within the 30-day period after disposal – the First In First Out basis (FIFO)
   3. any shares acquired before the date of disposal which are included in an expanded ‘s. 104 holding’
   4. if the above identification rules fail to exhaust the shares disposed of, they are to be identified with subsequent acquisitions beyond the 30-day period following the disposal.

Note point #4 when buying back shorted shares #1 (same day rule) and #2 (bed&breakfast) still applies.

3. Rounding: Trade values and number of shares are stored in Decimal class with default precision (28 places). In case of unlikely share splits rounding may occur (e.g. 3 shares merge to 1).
