""" Functions for imported xml file handling"""

import glob

import pandas


def read_all_xml(xpath: str) -> pandas.DataFrame:
    """
    read all the xml files in the folder and
    return all selected xpath elements in pandas dataframe
    :param xpath: the xpath to select elements from the xml files
    """
    data_frame = None
    for file in glob.glob("*.xml"):
        xml_data = pandas.read_xml(file, xpath)
        data_frame = (
            xml_data
            if data_frame is None
            else pandas.concat([data_frame, xml_data], ignore_index=True)
        )
    return data_frame
