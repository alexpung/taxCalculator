"""Main executable file for the project"""
from glob import glob
from tkinter import Tk, filedialog

from tomlkit import parse
from tomlkit.exceptions import NonExistentKey
from tomlkit.items import AoT

from capital_gain.calculator import CgtCalculator
from capital_gain.dividend_summary import get_dividend_summary
from capital_gain.model import BuyTrade, Dividend, Section104, SellTrade, ShareReorg
import const
from excel_output.capital_gain_list import write_capital_gain_excels
from excel_output.dividend_list import write_dividend_list
import exception
from statement_parser.ibkr import (
    parse_corp_action,
    parse_dividend,
    parse_fx_acquisition_and_disposal,
    parse_trade,
)


class UKTaxCalculator:
    """Command line application for tax calculator"""

    def __init__(self) -> None:
        self.section104: Section104 = Section104()
        self.trades_list: list[BuyTrade | SellTrade] = []
        self.corp_action_list: list[ShareReorg] = []
        self.dividend_list: list[Dividend] = []
        self.read_section104_from_toml()
        self.load_files(self.select_directory())
        # Acquisitions and disposals of GBP is not taxable, so including it is redundant
        self.trades_list = [x for x in self.trades_list if x.ticker != "GBP"]
        self.calculate()

        write_dividend_list(
            self.dividend_list, get_dividend_summary(self.dividend_list)
        )
        write_capital_gain_excels(
            [*self.trades_list, *self.corp_action_list], self.section104
        )

    def read_section104_from_toml(self) -> None:
        """Reading section 104 init data from toml file"""
        try:
            with open(const.CONFIG_FILE, encoding="utf-8") as config_file:
                parsed_content = parse(config_file.read())
                section104 = parsed_content["Section104"]
                if isinstance(section104, AoT):
                    for entry in section104.value:
                        self.section104.add_to_section104(
                            entry["symbol"], entry["quantity"], entry["value"]
                        )
                else:
                    exception.toml_heading_incorrect()
        except FileNotFoundError:
            exception.section_104_init_not_found()
        except NonExistentKey:
            exception.section104_key_incorrect_or_not_found()

    @staticmethod
    def select_directory() -> list[str]:
        """Invoke Tinker for selecting import directory"""
        root = Tk()
        root.withdraw()
        file_path = filedialog.askdirectory()
        if file_path != "":
            return glob(file_path + "/*.xml")
        else:
            return []

    def load_files(self, file_list: list[str]) -> None:
        """Read trade, dividend and stock split data from files"""
        for file in file_list:
            self.trades_list.extend(parse_trade(file))
            self.corp_action_list.extend(parse_corp_action(file))
            self.trades_list.extend(parse_fx_acquisition_and_disposal(file))
            self.dividend_list.extend(parse_dividend(file))

    def calculate(self) -> None:
        """invoke calculation of capital gain"""
        calculator = CgtCalculator(
            self.trades_list, self.corp_action_list, self.section104
        )
        calculator.calculate_tax()
        self.section104 = calculator.get_section104()


if __name__ == "__main__":
    UKTaxCalculator()
