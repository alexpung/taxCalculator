""" Excel name constants """

from enum import Enum


# excel sheet names
class SheetNames(str, Enum):
    """Name constants of the output Excel sheets"""

    DIVIDEND_SUMMARY = "dividend summary"
    DIVIDEND_DATA = "dividend data"
    INTEREST_DATA = "interest data"
