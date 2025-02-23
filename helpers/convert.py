"""
Conversion Module

This module provides a utility function to convert integers into 
hexadecimal strings with a specified length, ensuring consistent 
zero-padding.

Functions:
    to_padded_hex(integer: int, desired_len: int = 2) -> str
        Converts an integer to a zero-padded hexadecimal string.
"""

def to_padded_hex(integer: int, desired_len: int = 2) -> str:
    """Convert an integer to a zero-padded hexadecimal string.

    Args:
        integer (int): The integer to convert.
        desired_len (int, optional): The length of the hex digits (excluding '0x'). Defaults to 2.

    Returns:
        str: The formatted hexadecimal string with '0x' prefix.
    """
    return f"0x{integer:0{desired_len}x}"
