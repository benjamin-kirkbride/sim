def compress_multiline_string(input_str: str) -> str:
    r"""Compresses whitespace in a given string.

    This function replaces multiple spaces, tabs and single new lines with a single space,
    while preserving double new lines. It also removes any leading or trailing whitespace.

    Args:
        input_str (str): The string to compress.

    Returns:
        str: The compressed string.

    Raises:
        TypeError: If the input_str is not of type string.

    Examples:
    >>> compress_multiline_string("foo  bar\n     baz\n\nbuz")
    'foo bar baz\n\nbuz'

    >>> compress_multiline_string("ayy\n   lmao\tfoo\n\nbar")
    'ayy lmao foo\n\nbar'

    >>> compress_multiline_string('''
    ... foo bar
    ...      baz
    ...
    ... buz
    ... ''')
    'foo bar baz\n\nbuz'
    """

    def compress_whitespace(string: str) -> str:
        # Split the string by white spaces (including new lines),
        # then join back with a space to compress the white spaces
        return " ".join(string.split())

    # Split the input string by double new lines,
    # then apply the compress_whitespace function to each part,
    # then join back with double new lines
    return "\n\n".join(map(compress_whitespace, input_str.split("\n\n"))).strip()
