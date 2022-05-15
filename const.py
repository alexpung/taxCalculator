"""constants"""
import datetime

CONFIG_FILE = "init.toml"


def get_tax_year(date: datetime.date) -> int:
    """return the tax year given a date"""
    if date.month == 4:
        if date.day <= 5:
            return date.year - 1
        else:
            return date.year
    elif date.month < 4:
        return date.year - 1
    else:
        return date.year
