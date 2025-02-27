from collections import deque

def hexify(message_data: list[int]) -> deque[str]:
    """Convert a list of decimal values to a list of hexadecimal values

    Args:
        message_data (list): The decimal-formatted message to convert each index in the list
                                should be one byte of data
    Returns:
        list: A hexadecimal-formatted message
    """
    hex_message = deque(maxlen=128)
    for item in message_data:
        hex_message.extend([to_padded_hex(item)])
    return hex_message

def to_padded_hex(integer: int, desired_len: int = 2) -> str:
    """Convert an integer to a zero-padded hexadecimal string.

    Args:
        integer (int): The integer to convert.
        desired_len (int, optional): The length of the hex digits (excluding '0x'). Defaults to 2.

    Returns:
        str: The formatted hexadecimal string with '0x' prefix.
    """
    return f"0x{integer:0{desired_len}x}"