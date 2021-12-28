""" Strings representation of the comment section in transactions """

from decimal import Decimal


class Comment:
    """Comment class for commenting transactions"""

    @staticmethod
    def add_to_section104(
        qty: Decimal, cost: Decimal, new_quantity: Decimal, new_cost: Decimal
    ) -> str:
        """Comment when adding shares to the Section 104 pool"""
        return (
            f"{qty} share(s) added to Section104 pool "
            f"with allowable cost {cost}.\n"
            f"New total number of share(s) for section 104 "
            f"is {new_quantity}.\n"
            f"New total allowable cost is {new_cost}"
        )

    @staticmethod
    def remove_from_section104(
        qty: Decimal, cost: Decimal, new_quantity: Decimal, new_cost: Decimal
    ) -> str:
        """Comment when removing shares to the Section 104 pool"""
        return (
            f"{qty} share(s) removed to Section104 pool "
            f"with allowable cost {cost}.\n"
            f"New total number of share(s) for section 104 "
            f"is {new_quantity}.\n"
            f"New total allowable cost is {new_cost}"
        )
