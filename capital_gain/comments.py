""" Strings representation of the comment section in transactions """

from dataclasses import dataclass
from decimal import Decimal


@dataclass(repr=False)
class AddToSection104:
    """Comment for adding a buy transaction to the Section 104 pool"""

    old_qty: Decimal
    old_cost: Decimal
    added_qty: Decimal
    added_cost: Decimal

    def __repr__(self) -> str:
        return (
            f"{self.added_qty} share(s) added to Section104 pool "
            f"with allowable cost {self.added_cost}.\n"
            f"New total number of share(s) for section 104 "
            f"is {self.added_qty+self.old_qty}.\n"
            f"New total allowable cost is {self.added_cost + self.old_cost}"
        )


@dataclass(repr=False)
class RemoveFromSection104:
    """Comment for adding a buy transaction to the Section 104 pool"""

    old_qty: Decimal
    old_cost: Decimal
    removed_qty: Decimal
    removed_cost: Decimal

    def __repr__(self) -> str:
        return (
            f"{self.removed_qty} share(s) removed to Section104 pool "
            f"with allowable cost {self.removed_cost}.\n"
            f"New total number of share(s) for section 104 "
            f"is {self.removed_qty+self.old_qty}.\n"
            f"New total allowable cost is {self.removed_cost + self.old_cost}"
        )
