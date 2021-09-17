class RequestRejectedError(Exception):
    """The XML download request is rejected by IB server"""

    def __init__(self, code, message):
        self.message = f'''ERROR: XML request is rejected.
                    Error Code: {code}
                    Error Message: {message}'''
        super().__init__(self.message)


class RequestTimeoutError(Exception):
    """XML request aborted as retry limit reached"""

    def __init__(self):
        self.message = f"""XML file cannot be generated after retry limit reached. 
        Please increase retry limit in xml_import.py or reduce the scope of the XML report"""
        super().__init__(self.message)
