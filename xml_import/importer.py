""" Import functions for Interactive Brokers flex queries """
from __future__ import annotations

import logging
import time
import urllib.parse
import urllib.request
from xml.etree import ElementTree

from xml_import.exception import RequestRejectedError, RequestTimeoutError

logger = logging.getLogger(__name__)

REQUEST_VERSION = "3"
XML_VERSION = "3"
INITIAL_WAIT = 5  # Waiting time for first attempt
RETRY = 7  # number of retry before aborting
RETRY_INCREMENT = 10  # amount of wait time increase for each failed attempt
BASE_URL = (
    "https://gdcdyn.interactivebrokers.com"
    "/Universal/servlet/FlexStatementService.SendRequest"
)


def find_text(root: ElementTree.ElementTree | ElementTree.Element, target: str) -> str:
    """Helper function to handle case when the search return None"""
    result = root.find(target)
    if result is not None:
        return result.text if result.text else ""
    else:
        return ""


def _make_xml_request(
    token: str, report_number: str, version: str
) -> ElementTree.Element:
    """Step 1 : Request IB to generate the flex query file by giving a request
     with the token
    note that the server is not always up, and sometimes it is down on Sat/Sun"""
    url_values = urllib.parse.urlencode({"t": token, "q": report_number, "v": version})
    full_url = BASE_URL + "?" + url_values
    with urllib.request.urlopen(full_url) as xml_request_response:
        root = ElementTree.fromstring(xml_request_response.read())
        status = find_text(root, "Status")
        logger.info("XML request Status: %s", status)
        if status == "Success":
            return root
        else:
            error_code = find_text(root, "ErrorCode")
            error_message = find_text(root, "ErrorMessage")
            raise RequestRejectedError(error_code, error_message)


def _get_xml(
    base_url: str, reference_code: str, token: str, version: str
) -> ElementTree.Element:
    """Step 2: After the request is accepted,
    you need to wait until the file is ready to download."""
    xml_url_values = urllib.parse.urlencode(
        {"q": reference_code, "t": token, "v": version}
    )
    xml_full_url = base_url + "?" + xml_url_values
    retry = 0
    while retry < RETRY:
        timer = retry * RETRY_INCREMENT + INITIAL_WAIT
        logger.info("Waiting %i seconds before fetching XML", timer)
        time.sleep(timer)
        with urllib.request.urlopen(xml_full_url) as xml_data:
            root = ElementTree.fromstring(xml_data.read())
            if root[0].tag == "FlexStatements":
                logger.info("XML download is successful.")
                return root
            elif (
                find_text(root, "ErrorCode") == "1019"
            ):  # statement generation in process, retry later
                logger.info("XML is not yet ready.")
                retry += 1
            else:
                error_code = find_text(root, "ErrorCode")
                error_message = find_text(root, "ErrorMessage")
                raise RequestRejectedError(error_code, error_message)
    raise RequestTimeoutError()


def download_xml(token: str, report_number: str, filename: str = "data.xml") -> None:
    """
    Flex query report number is generated when you create a flex query.
    https://www.interactivebrokers.com.hk/
    en/software/am/am/reports/activityflexqueries.htm

    Please refer to the link below on how to get the token
    https://www.interactivebrokers.com.hk
    /en/software/am/am/reports/flex_web_service_version_3.htm
    """
    xml_reply = _make_xml_request(token, report_number, REQUEST_VERSION)
    xml_result = _get_xml(
        find_text(xml_reply, "Url"),
        find_text(xml_reply, "ReferenceCode"),
        token,
        XML_VERSION,
    )
    tree = ElementTree.ElementTree(xml_result)
    # the response is actually a xml file that you can write directly to a file
    with open(filename, "wb") as file:
        tree.write(file)
