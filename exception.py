"""Error handling code"""


def setting_file_not_found():
    """handling when no init file for section 104"""
    print(
        "Section104 initialization file (init.toml) not found, "
        "pool will be calculated only from trade"
    )


def section104_incorrect():
    """Handling when section104 key is incorrect or not found"""
    print(
        "Format for section 104 not found/incorrect, "
        "heading should be [['Section104']], "
        "keys are 'symbol', 'quantity', 'value'"
        "pool will be calculated only from trade"
    )


def setting_not_found():
    """Handling when setting config is incorrect or not found"""
    print("Configuration not found, will use default setting")
