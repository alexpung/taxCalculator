from __future__ import annotations

import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from .exception import RequestRejectedError, RequestTimeoutError
import logging
logger = logging.getLogger(__name__)

REQUEST_VERSION = '3'
XML_VERSION = '3'
INITIAL_WAIT = 5  # Waiting time for first attempt
RETRY = 7  # number of retry before aborting
RETRY_INCREMENT = 10  # amount of wait time increase for each failed attempt
BASE_URL = 'https://gdcdyn.interactivebrokers.com/Universal/servlet/FlexStatementService.SendRequest'


def _make_xml_request(token: str, report_number: str, version: str) -> ET.Element:
    """Step 1 : Request IB to generate the flex query file by giving a request with the token
        note that the server is not always up and sometimes it is down on Sat/Sun"""
    url_values = urllib.parse.urlencode({'t': token, 'q': report_number, 'v': version})
    full_url = BASE_URL + '?' + url_values
    with urllib.request.urlopen(full_url) as xml_request_response:
        root = ET.fromstring(xml_request_response.read())
        status = root.find('Status').text
        logger.info(f'XML request Status: {status}')
        if status == 'Success':
            return root
        else:
            error_code = root.find('ErrorCode').text
            error_message = root.find('ErrorMessage').text
            raise RequestRejectedError(error_code, error_message)


def _get_xml(base_url: str, reference_code: str, token: str, version: str) -> ET.Element:
    """Step 2: After the request is accepted, you need to wait until the file is ready to download."""
    xml_url_values = urllib.parse.urlencode({'q': reference_code, 't': token, 'v': version})
    xml_full_url = base_url + '?' + xml_url_values
    retry = 0
    while retry < RETRY:
        timer = retry * RETRY_INCREMENT + INITIAL_WAIT
        logger.info(f'Waiting {timer} seconds before fetching XML')
        time.sleep(timer)
        with urllib.request.urlopen(xml_full_url) as xml_data:
            root = ET.fromstring(xml_data.read())
            if root[0].tag == 'FlexStatements':
                logger.info('XML download is successful.')
                return root
            elif root.find('ErrorCode').text == '1019':  # statement generation in process, retry later
                logger.info('XML is not yet ready.')
                retry += 1
            else:
                error_code = root.find('ErrorCode').text
                error_message = root.find('ErrorMessage').text
                raise RequestRejectedError(error_code, error_message)
    raise RequestTimeoutError()


def download_xml(token, report_number, filename='data.xml'):
    """
    Flex query report number is generated when you create a flex query.
    https://www.interactivebrokers.com.hk/en/software/am/am/reports/activityflexqueries.htm

    Please refer to the link below on how to get the token
    https://www.interactivebrokers.com.hk/en/software/am/am/reports/flex_web_service_version_3.htm
    """
    xml_reply = _make_xml_request(token, report_number, REQUEST_VERSION)
    xml_result = _get_xml(xml_reply.find('Url').text, xml_reply.find('ReferenceCode').text, token, XML_VERSION)
    tree = ET.ElementTree(xml_result)
    # the response is actually an xml file that you can write directly to a file
    with open(filename, 'wb') as f:
        tree.write(f)
