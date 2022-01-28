""" Prototype UI for the App """
from collections import defaultdict
import datetime
from glob import glob
import re
from tkinter import Tk, filedialog
from typing import Any, Final, List, Tuple

from kivy.config import Config
from kivy.lang import Builder

# pylint bug, disable checking kivy.properties
# pylint: disable=no-name-in-module
from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineIconListItem
from kivymd.uix.pickers import MDDatePicker

from capital_gain.calculator import CgtCalculator
from capital_gain.model import Dividend, Section104, Trade
from gui.table_display import convert_table_header, get_colored_table_row
from statement_parser.ibkr import parse_dividend, parse_trade

# pylint bug, disable checking kivy.properties
# pylint: disable=no-name-in-module

Config.set("input", "mouse", "mouse,multitouch_on_demand")


class TaxYearWidget(MDBoxLayout):
    """Layout containing the control of tax year selection"""

    tax_year = StringProperty()
    date_range = ObjectProperty()
    LABEL_CUSTOM: Final[str] = "Custom"
    """ To control the display of the tax year """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tax_year = str(datetime.datetime.now().year - 1)
        self.date_range = self.get_tax_year_date(int(self.tax_year))
        app = MDApp.get_running_app()
        # Initialize here so the main app know the default tax date range
        (app.tax_start_date, app.tax_end_date) = self.date_range

    def on_press_left(self):
        """left button pressed: subtract a year"""
        if self.tax_year == self.LABEL_CUSTOM:
            self.tax_year = str(datetime.datetime.now().year)
        else:
            self.tax_year = str(int(self.tax_year) - 1)
        self.date_range = self.get_tax_year_date(int(self.tax_year))

    def on_press_right(self):
        """right button pressed: add a year"""
        if self.tax_year == self.LABEL_CUSTOM:
            self.tax_year = str(datetime.datetime.now().year)
        else:
            self.tax_year = str(int(self.tax_year) + 1)
        self.date_range = self.get_tax_year_date(int(self.tax_year))

    @staticmethod
    def get_tax_year_date(year: int) -> Tuple[datetime.date, ...]:
        """helper function to get start and end date of tax year"""
        return datetime.date(year, 4, 6), datetime.date(year + 1, 4, 5)

    def on_save(self, _1, _2, date_range):
        """Events called when the "OK" dialog box button is clicked."""
        if len(date_range) < 2:
            toast("Please select a valid date range with start and end date")
        else:
            self.date_range = (date_range[0], date_range[-1])
            self.tax_year = self.LABEL_CUSTOM

    def show_date_picker(self):
        """show the custom tax date picker"""
        date_dialog = MDDatePicker(mode="range", min_year=2000)
        date_dialog.bind(on_save=self.on_save)
        date_dialog.open()


class TableLayout(MDBoxLayout):
    """class for drawing the data table area
    Unfortunately Datatable cannot be initialized in .kv file so
    it is created in python and added here.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        column_data = convert_table_header(Trade.table_header, 30)
        self.table = MDDataTable(
            use_pagination=True, rows_num=10, column_data=column_data
        )
        label = MDLabel(text="Transaction List", size_hint=(1, 0.1))
        self.table.bind(on_row_press=MDApp.get_running_app().on_row_press)
        MDApp.get_running_app().bind(trade_table_data=self.table.update_row_data)
        self.add_widget(label)
        self.add_widget(self.table)


class ItemDrawer(OneLineIconListItem):
    """class for drawing the menu items"""

    icon = StringProperty()
    text_color = ListProperty((0, 0, 0, 1))


class CalculatorApp(MDApp):
    """Main application"""

    trade_description = StringProperty()
    trade_table_data = ListProperty()
    trades = ListProperty()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.dividends: List[Dividend] = []
        self.section104: List[Section104] = []

    def build(self) -> Any:
        return Builder.load_file("kivymd.kv")

    def select_directory(self) -> None:
        """Invoke Tinker for selecting import directory"""
        root = Tk()
        root.withdraw()
        file_path = filedialog.askdirectory()
        if file_path != "":
            self.import_folder(file_path)

    def select_file(self) -> None:
        """Invoke Tinker for selecting an import file"""
        root = Tk()
        root.withdraw()
        file_name = filedialog.askopenfilename()
        if file_name != "":
            self.import_file(file_name)

    def calculate(self, file: str) -> None:
        """invoke calculation of capital gain"""
        self.trades.extend(parse_trade(file))
        self.dividends.extend(parse_dividend(file))
        trade_bucket = defaultdict(list)
        # put trades with the same symbol together and calculate tax
        for trade in self.trades:
            trade_bucket[trade.ticker].append(trade)
        for _, trade_list in trade_bucket.items():
            section104_single = CgtCalculator(trade_list).calculate_tax()
            if section104_single.quantity > 0:
                self.section104.append(section104_single)
        # sort the results and put it in the table
        self.trades = sorted(self.trades, key=lambda x: (x.ticker, x.transaction_date))
        self.update_table((self.tax_start_date, self.tax_end_date))

    def import_file(self, file: str) -> None:
        """Import a single file"""
        self.calculate(file)

    def import_folder(self, path: str) -> None:
        """Import a directory"""
        # hardcoded to import XML file
        for file in glob(path + "/*.xml"):
            self.calculate(file)

    def on_row_press(self, _, instance_row) -> None:
        """Called when a table row is clicked."""
        start_index, _ = instance_row.table.recycle_data[instance_row.index]["range"]
        cell = instance_row.table.recycle_data[start_index]["text"]
        index = int(re.sub("[[].*?[]]", "", cell))
        self.trade_description = str(
            next(trade for trade in self.trades if trade.transaction_id == index)
        )

    def update_table(self, date_range: Tuple[datetime.date, datetime.date]) -> None:
        """called when the data table needs to be updated"""
        (self.tax_start_date, self.tax_end_date) = date_range
        self.trade_table_data = get_colored_table_row(
            list(self.trades), self.tax_start_date, self.tax_end_date
        )


if __name__ == "__main__":
    CalculatorApp().run()