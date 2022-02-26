""" Prototype UI for the App """
from glob import glob
import re
from tkinter import Tk, filedialog
from typing import Any, Final, List

from kivy.config import Config
from kivy.lang import Builder

# pylint bug, disable checking kivy.properties
# pylint: disable=no-name-in-module
from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineIconListItem
from tomlkit import parse
from tomlkit.container import Container
from tomlkit.exceptions import NonExistentKey

from capital_gain.calculator import CgtCalculator
import capital_gain.capital_summary as summary
from capital_gain.model import Dividend, Section104
from gui.table_display import convert_table_header, get_colored_table_row
import gui.table_presentation as table_presentation
from statement_parser.ibkr import parse_corp_action, parse_dividend, parse_trade

Config.set("input", "mouse", "mouse,multitouch_on_demand")


class CapitalGainSummaryLabel(MDLabel):
    """Layout for showing capital gain summary"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()
        self.app.bind(trades=self.calculate_summary)
        self.app.bind(date_range=self.calculate_summary)

    def calculate_summary(self, *_args):
        """To calculate the capital gain tax summary"""
        self.text = summary.get_text_summary(
            self.app.trades,
            self.app.date_range.start_date,
            self.app.date_range.end_date,
        )


class TableLayout(MDBoxLayout):
    """class for drawing the data table area
    Unfortunately Datatable cannot be initialized in .kv file so
    it is created in python and added here.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        column_data = convert_table_header(table_presentation.trade_header, 30)
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

    _CONFIG_FILE: Final = "init.toml"
    trade_description = StringProperty()
    trade_table_data = ListProperty()
    trades = ListProperty()
    corp_actions = ListProperty()
    date_range = ObjectProperty()
    section_104 = ObjectProperty()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.dividends: List[Dividend] = []
        self.section104: Section104
        try:
            with open(self._CONFIG_FILE, encoding="utf-8") as config_file:
                parsed_content = parse(config_file.read())
                self.section104_init = Section104()
                if not isinstance(parsed_content["Section104"], Container):
                    raise ImportError(
                        "Heading incorrect: " "heading should be '[[Section104]]'"
                    )
                for entry in parsed_content["Section104"].value:
                    self.section104_init.add_to_section104(
                        entry["symbol"], entry["quantity"], entry["value"]
                    )
        except FileNotFoundError:
            print(
                "Section104 initialization file (init.toml) not found, "
                "pool will be calculated only from trade"
            )
        except NonExistentKey:
            print(
                "Key for section 104 not found/incorrect, "
                "heading should be [['Section104']], "
                "keys are 'symbol', 'quantity', 'value'"
            )

    def build(self) -> Any:
        return Builder.load_file("kivymd.kv")

    def select_directory(self) -> None:
        """Invoke Tinker for selecting import directory"""
        root = Tk()
        root.withdraw()
        file_path = filedialog.askdirectory()
        if file_path != "":
            for file in glob(file_path + "/*.xml"):
                self.calculate(file)

    def select_file(self) -> None:
        """Invoke Tinker for selecting an import file"""
        root = Tk()
        root.withdraw()
        file_name = filedialog.askopenfilename()
        if file_name != "":
            self.calculate(file_name)

    def calculate(self, file: str) -> None:
        """invoke calculation of capital gain"""
        self.trades.extend(parse_trade(file))
        self.corp_actions.extend(parse_corp_action(file))
        self.dividends.extend(parse_dividend(file))
        calculator = CgtCalculator(self.trades, self.corp_actions, self.section104_init)
        calculator.calculate_tax()
        self.section_104 = calculator.get_section104()
        self.update_table()

    def on_row_press(self, _, instance_row) -> None:
        """Called when a table row is clicked."""
        start_index, _ = instance_row.table.recycle_data[instance_row.index]["range"]
        cell = instance_row.table.recycle_data[start_index]["text"]
        index = int(re.sub("[[].*?[]]", "", cell))
        self.trade_description = str(
            next(trade for trade in self.trades if trade.transaction_id == index)
        )

    def update_table(self) -> None:
        """called when the data table needs to be updated"""
        table_data = [*self.trades, *self.corp_actions]
        table_data = sorted(table_data, key=lambda x: (x.ticker, x.transaction_date))
        self.trade_table_data = get_colored_table_row(
            table_data, self.date_range.start_date, self.date_range.end_date
        )

    def on_date_range(self, *_args):
        """called when the date range is changed"""
        self.update_table()


if __name__ == "__main__":
    CalculatorApp().run()
