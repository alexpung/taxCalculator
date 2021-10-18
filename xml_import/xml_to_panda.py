import glob
import pandas


def read_all_xml(xpath: str) -> pandas.DataFrame:
    """
    read all the xml files in the folder and return all selected xpath elements in pandas dataframe
    :param xpath: the xpath to select elements from the xml files
    """
    df = None
    for file in glob.glob("*.xml"):
        xml_data = pandas.read_xml(file, xpath)
        if df is None:
            df = xml_data
        else:
            df = pandas.concat([df, xml_data], ignore_index=True)
    return df
