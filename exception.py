"""Error handling code"""


def section_104_init_not_found():
    """handling when no init file for section 104"""
    print(
        "Section104 initialization file (init.toml) not found, "
        "pool will be calculated only from trade"
    )


def section104_key_incorrect_or_not_found():
    """Handling when section104 key is incorrect or not found"""
    print(
        "Key for section 104 not found/incorrect, "
        "heading should be [['Section104']], "
        "keys are 'symbol', 'quantity', 'value'"
    )


def toml_heading_incorrect():
    """Handling when toml heading is not correct"""
    raise ImportError("Heading incorrect: " "heading should be '[[Section104]]'")
