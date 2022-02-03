""" Control for the widget that control import and export data """
import codecs
from enum import Enum

# pylint bug, disable checking kivy.properties
# pylint: disable=no-name-in-module
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu

from capital_gain.capital_summary import CgtTaxSummary
from capital_gain.dividend_summary import DividendSummary
from capital_gain.section104 import show_section104_and_short


class FormatOption(Enum):
    """Export format that is available"""

    PLAIN_TEXT = "Plain text"
    EXCEL = "Excel"


class ImportExportWidget(MDBoxLayout):
    """Layout for controlling the import and export of trade data"""

    selected_format = ObjectProperty(FormatOption.PLAIN_TEXT, rebind=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dropdown = None
        self.app = MDApp.get_running_app()
        self.options = [
            {
                "viewclass": "OneLineListItem",
                "text": FormatOption.PLAIN_TEXT.value,
                "on_release": lambda x=FormatOption.PLAIN_TEXT: self.set_export_format(
                    x
                ),
            },
            {
                "viewclass": "OneLineListItem",
                "text": FormatOption.EXCEL.value,
                "on_release": lambda x=FormatOption.EXCEL: self.set_export_format(x),
            },
        ]

    def on_kv_post(self, base_widget):
        """called after kv string load so id can be accessed"""
        caller = self.ids.export_format
        self.dropdown = MDDropdownMenu(caller=caller, items=self.options, width_mult=4)

    def set_export_format(self, selected_format: FormatOption) -> None:
        """Called when the export format is selected from dropdown menu"""
        self.selected_format = selected_format
        self.dropdown.dismiss()

    def export_all(self):
        """Called to export all trade transactions"""
        if self.selected_format == FormatOption.EXCEL:
            toast("Excel format is not supported yet")
        elif self.selected_format == FormatOption.PLAIN_TEXT:
            with codecs.open("output.txt", "w", encoding="utf8") as file:
                dividend_summary = DividendSummary(
                    self.app.dividends,
                    self.app.date_range.start_date,
                    self.app.date_range.end_date,
                )
                file.write(dividend_summary.show_dividend_by_country())
                file.write(dividend_summary.show_dividend_total())
                file.write(
                    CgtTaxSummary.get_text_summary(
                        self.app.trades,
                        self.app.date_range.start_date,
                        self.app.date_range.end_date,
                    )
                )
                file.write(
                    show_section104_and_short(self.app.trades, self.app.section104)
                )
                for trade in self.app.trades:
                    file.write(str(trade))
                toast(f"{len(self.app.trades)} trade(s) exported")
