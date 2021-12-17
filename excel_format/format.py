""" Formatting control for the Excel output file """
from openpyxl.styles import Alignment
from openpyxl.worksheet.worksheet import Worksheet


class ExcelFormatter:
    """Helper class to format excel sheet"""

    @staticmethod
    def format_cell(sheet: Worksheet, cell_range: str, date_format: str) -> None:
        """
        Set format of Dates/number in selected column
        :param sheet: Openpyxl Worksheet object
        :param cell_range: Range of cell to be formatted
        :param date_format: Date in excel notation e.g. 'DD/MM/YY'
        """
        if ":" in cell_range:
            for row in sheet[cell_range]:
                for cell in row:
                    cell.number_format = date_format
        else:
            for cell in sheet[cell_range]:
                cell.number_format = date_format

    @staticmethod
    def auto_size_column(sheet: Worksheet) -> None:
        """
        Set size of column according to longest length of string in that column
        :param sheet: Openpyxl Worksheet object
        """
        # calculate suitable column width length+2 * 1.2
        dims: dict[str, float] = {}
        for row in sheet.rows:
            for cell in row:
                if cell.value:
                    dims[cell.column_letter] = max(
                        (
                            dims.get(cell.column_letter, 0),
                            (len(str(cell.value)) + 2) * 1.2,
                        )
                    )
        for col, value in dims.items():
            sheet.column_dimensions[col].width = value

    @staticmethod
    def set_alignment(
        sheet: Worksheet, cell_range: str, horizontal_alignment: str
    ) -> None:
        """
        set horizontal alignment of cells
        :param sheet: Openpyxl Worksheet object
        :param cell_range: Range of cell to be formatted
        :param horizontal_alignment:
        """
        if ":" in cell_range:
            for row in sheet[cell_range]:
                for cell in row:
                    cell.alignment = Alignment(horizontal=horizontal_alignment)
        else:
            for cell in sheet[cell_range]:
                cell.alignment = Alignment(horizontal=horizontal_alignment)
