""" Prototype UI for the App """
from collections import defaultdict
from glob import glob
from tkinter import Tk, filedialog
from typing import Any, List

from kivy.config import Config
from kivy.lang import Builder
from kivy.metrics import dp

# pylint: disable=no-name-in-module
from kivy.properties import ListProperty, StringProperty
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineIconListItem

from capital_gain.calculator import CgtCalculator
from capital_gain.model import Dividend, Section104, Trade
from statement_parser.ibkr import parse_dividend, parse_trade

Config.set("input", "mouse", "mouse,multitouch_on_demand")


class CalculatorControl:
    """Control functions for the app"""

    def __init__(self) -> None:
        self.trades: List[Trade] = []
        self.dividends: List[Dividend] = []
        self.section104: List[Section104] = []

    def calculate(self) -> None:
        """invoke calculation of capital gain"""
        trade_bucket = defaultdict(list)
        for trade in self.trades:
            trade_bucket[trade.ticker].append(trade)
        for _, trade_list in trade_bucket.items():
            section104_single = CgtCalculator(trade_list).calculate_tax()
            if section104_single.quantity > 0:
                self.section104.append(section104_single)

    def import_file(self, file: str) -> None:
        """Import a single file"""
        self.trades += parse_trade(file)
        self.trades = sorted(self.trades, key=lambda x: (x.ticker, x.transaction_date))
        self.dividends += parse_dividend(file)
        self.calculate()
        for trade in self.trades:
            if DataTable.last_instance:
                DataTable.last_instance.add_row(trade.get_tuple_repr())

    def import_folder(self, path: str) -> None:
        """Import a directory"""
        # hardcoded to import XML file
        for file in glob(path + "/*.xml"):
            self.trades += parse_trade(file)
            self.trades = sorted(
                self.trades, key=lambda x: (x.ticker, x.transaction_date)
            )
            self.dividends += parse_dividend(file)
        self.calculate()
        for trade in self.trades:
            if DataTable.last_instance:
                DataTable.last_instance.add_row(trade.get_tuple_repr())


# pylint: disable=too-many-ancestors
class CalculationDetailLabel(MDLabel):
    """Label to show the capital gain calculation details"""

    last_instance = None

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        CalculationDetailLabel.last_instance = self


class DataTable(MDDataTable):
    """Table to show the trade transactions"""

    last_instance = None
    column_data = [
        ("ID", dp(30)),
        ("Symbol", dp(30)),
        ("Transaction Date", dp(30)),
        ("Transaction Type", dp(30)),
        ("Quantity", dp(30)),
        ("Gross Value", dp(30)),
        ("Allowable fees and Taxes", dp(30)),
        ("Capital gain (loss)", dp(30)),
    ]

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        DataTable.last_instance = self


class TableLayout(MDBoxLayout):
    """class for drawing the data table area"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        label = MDLabel(text="Transaction List", size_hint=(1, 0.1))
        self.add_widget(label)
        self.add_widget(DataTable.last_instance)


class ItemDrawer(OneLineIconListItem):
    """class for drawing the menu items"""

    icon = StringProperty()
    text_color = ListProperty((0, 0, 0, 1))


class CalculatorApp(MDApp):
    """Main application"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.calculator_control = CalculatorControl()
        self.table = DataTable(size_hint=(1, 0.9), use_pagination=True, rows_num=10)
        self.table.bind(on_row_press=self.on_row_press)

    def build(self) -> Any:
        return Builder.load_file("kivymd.kv")

    def select_directory(self) -> None:
        """Invoke Tinker for selecting import directory"""
        root = Tk()
        root.withdraw()
        file_path = filedialog.askdirectory()
        if file_path != "":
            self.calculator_control.import_folder(file_path)

    def select_file(self) -> None:
        """Invoke Tinker for selecting an import file"""
        root = Tk()
        root.withdraw()
        file_name = filedialog.askopenfilename()
        if file_name != "":
            self.calculator_control.import_file(file_name)

    def on_row_press(self, _, instance_row) -> None:
        """Called when a table row is clicked."""
        start_index, _ = instance_row.table.recycle_data[instance_row.index]["range"]
        index = int(instance_row.table.recycle_data[start_index]["text"])
        target = next(
            trade
            for trade in self.calculator_control.trades
            if trade.transaction_id == index
        )
        print(target)
        if CalculationDetailLabel.last_instance:
            CalculationDetailLabel.last_instance.text = str(target)


if __name__ == "__main__":
    CalculatorApp().run()
