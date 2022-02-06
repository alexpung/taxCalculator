![Pylint](https://github.com/alexpung/taxCalculator/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/alexpung/taxCalculator/branch/development/graph/badge.svg?token=O5UGER8FEJ)](https://codecov.io/gh/alexpung/taxCalculator)

# taxCalculator

UK tax calculator for Interactive Broker

To help report UK tax for dividend and capital gain.

# What is included

1. XML downloader to download report from web flex query (\xml_import\importer.py)
2. GUI interface with kivyMD (\gui\main_app.py)

# Current functionality

1. Parse Interactive Brokers trade data to Trade objects, then use these objects to calculate capital gain and loss
2. Parse Interactive Brokers dividend/dividend in lieu/Witholding tax and shows dividend by country and total income for the tax year specified
3. For each trade calculation steps are shown (in export text file or GUI windows)
4. Show section 104 holdings and sell that are unmatched with a buy (i.e. short sale)
5. Show trades in the GUI to allow user double-checking.

Known limitation:

1. Corporate Action is not handled yet
2. Most of the GUI interface is not implemented yet

This project use Poetry to manage dependency.
To set up:

1. pip install --user poetry
2. poetry install

Design notes:

1.  When a share forward or reverse split occurs it is assumed that the decimal shares will be lost and be given cash.
    For example when you have 11 shares then a 3-for-2 splits occurs, then it is assumed you would have 16 shares.
    Or when you have the same 11 shares and the company undergo a 1-for-2 reverse split. Then the app would assume you to have 5 shares.
    This is really corner case though and should not happen very often.
2.  Rounding problem:
    - Consider the following scenario:
    1. Long time ago you bought 100 shares of Company 'XYZ'
    2. Day 1: You sold 100 shares of Company 'XYZ'
    3. Day 10: Company undergone a forward split with ratio 3-to-1
    4. Day 11,12,13: You bought back 100 shares each day (one-third of your holding)
    - Internally I am using the Decimal class you would have a rounding problem for share matching. Internally this is rounded to 0
    -     >>> x = Decimal(100)
          >>> (x := x - Decimal(100)/Decimal(3))
          Decimal('66.66666666666666666666666667')
          >>> (x := x - Decimal(100)/Decimal(3))
          Decimal('33.33333333333333333333333334')
          >>> (x := x - Decimal(100)/Decimal(3))
          Decimal('1E-26')
          >>> x == 0
          False
    - The share holding is set to 0 by:
    -     if value < 0.0001:
              self.unmatched = Decimal(0)
