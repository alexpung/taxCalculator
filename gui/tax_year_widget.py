""" Control for the widget that allow user to specify the date for the report """
from dataclasses import dataclass
import datetime
from typing import Final

# pylint bug, disable checking kivy.properties
# pylint: disable=no-name-in-module
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.pickers import MDDatePicker


@dataclass
class Daterange:
    """To store date range for tax calculation"""

    start_date: datetime.date
    end_date: datetime.date


class TaxYearWidget(MDBoxLayout):
    """Layout containing the control of tax year selection"""

    display = StringProperty()
    LABEL_CUSTOM: Final[str] = "Custom"
    """ To control the display of the tax year """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()
        self.display = str(datetime.datetime.now().year - 1)
        self.app.date_range = self.get_tax_year_date(int(self.display))

    def on_press_left(self):
        """left button pressed: subtract a year"""
        if self.display == self.LABEL_CUSTOM:
            self.display = str(datetime.datetime.now().year)
        else:
            self.display = str(int(self.display) - 1)
        self.app.date_range = self.get_tax_year_date(int(self.display))

    def on_press_right(self):
        """right button pressed: add a year"""
        if self.display == self.LABEL_CUSTOM:
            self.display = str(datetime.datetime.now().year)
        else:
            self.display = str(int(self.display) + 1)
        self.app.date_range = self.get_tax_year_date(int(self.display))

    @staticmethod
    def get_tax_year_date(year: int) -> Daterange:
        """helper function to get start and end date of tax year"""
        return Daterange(datetime.date(year, 4, 6), datetime.date(year + 1, 4, 5))

    def on_save(self, _1, _2, date_range):
        """Events called when the "OK" dialog box button is clicked."""
        if len(date_range) < 2:
            toast("Please select a valid date range with start and end date")
        else:
            self.app.date_range = Daterange(date_range[0], date_range[-1])
            self.display = self.LABEL_CUSTOM

    def show_date_picker(self):
        """show the custom tax date picker"""
        date_dialog = MDDatePicker(mode="range", min_year=2000)
        date_dialog.bind(on_save=self.on_save)
        date_dialog.open()
