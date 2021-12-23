![Pylint](https://github.com/alexpung/taxCalculator/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/alexpung/taxCalculator/branch/development/graph/badge.svg?token=O5UGER8FEJ)](https://codecov.io/gh/alexpung/taxCalculator)

# taxCalculator

UK tax calculator for Interactive Broker

To help report UK tax for dividend and capital gain.

# What is included

1. XML downloader to download report from web flex query
2. Dividend summary generator to an Excel file (gross dividend and withholding tax by company country, for any period)
3. (planning) Capital gain tax calculation to the same Excel file
4. (planning) Handle tax relief cap due to tax treaty
