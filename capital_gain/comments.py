""" Strings representation of the comment section in transactions """

from decimal import Decimal


def add_to_section104(
    qty: Decimal, cost: Decimal, new_quantity: Decimal, new_cost: Decimal
) -> str:
    """Comment when adding shares to the Section 104 pool"""
    return (
        f"{qty:.2f} share(s) added to Section104 pool "
        f"with allowable cost {cost:.2f}.\n"
        f"New total number of share(s) for section 104 "
        f"is {new_quantity:.2f}.\n"
        f"New total allowable cost is {new_cost:.2f}\n"
    )


def remove_from_section104(
    qty: Decimal, cost: Decimal, new_quantity: Decimal, new_cost: Decimal
) -> str:
    """Comment when removing shares to the Section 104 pool"""
    return (
        f"{qty:.2f} share(s) removed to Section104 pool "
        f"with allowable cost {cost:.2f}.\n"
        f"New total number of share(s) for section 104 "
        f"is {new_quantity:.2f}.\n"
        f"New total allowable cost is {new_cost:.2f}\n"
    )


def capital_gain_calc(proceeds: Decimal, cost: Decimal) -> str:
    """Comments to show capital gain calculation"""
    return (
        f"Net proceeds after dealing cost is {proceeds:.2f}.\n"
        f"Allowable cost of shares sold is {cost:.2f}.\n"
        f"Capital gain (loss) is {proceeds-cost:.2f}\n"
    )
