"""
Communications Helper

This module provides a function to manage MIDI communication using the 
rtmidi library, including opening and configuring a MIDI input port.

Functions:
    open_communication(control_input_name: str, app_logger: Logger, queue_size_limit: int = 1024, sysex_disable: bool = False) -> rtmidi.MidiIn | None
        Initializes and returns an rtmidi.MidiIn instance for receiving MIDI messages.
"""

from typing import Optional
import rtmidi
from logbook import Logger


def open_communication(control_input_name: str, app_logger: Logger, 
                       queue_size_limit: int = 1024, sysex_disable: bool = False) -> Optional[rtmidi.MidiIn]:
    """Initialize and return a MIDI input instance using rtmidi.

    Args:
        control_input_name (str): The name of the MIDI input port to open.
        app_logger (Logger): Logger instance for debugging and error reporting.
        queue_size_limit (int, optional): The size limit of the MIDI message queue. Defaults to 1024.
        sysex_disable (bool, optional): Whether to disable SysEx message reception. Defaults to False.

    Returns:
        Optional[rtmidi.MidiIn]: An rtmidi.MidiIn instance if successful, otherwise None.
    """

    # Initialize MIDI Input with specified queue size limit
    try:
        midi_instance = rtmidi.MidiIn(name=control_input_name, queue_size_limit=queue_size_limit)
    except Exception as e:
        app_logger.error(f"Failed to initialize MIDI input: {e}")
        return None

    # Configure MIDI instance to ignore SysEx messages if specified
    midi_instance.ignore_types(sysex=sysex_disable)

    # List available MIDI ports
    available_ports = midi_instance.get_ports()
    app_logger.debug("Available MIDI Ports:")
    for port in available_ports:
        app_logger.debug(f" --> '{port}'")

    if not available_ports:
        app_logger.error("No available MIDI input ports.")
        return None

    if control_input_name in available_ports:
        port_index = available_ports.index(control_input_name)
    else:
        app_logger.error(f"MIDI port '{control_input_name}' not found among available ports.")
        return None

    # Open the specified MIDI input port
    try:
        midi_instance.open_port(port_index)
        app_logger.info(f"Opened MIDI port -> '{control_input_name}'")
        return midi_instance
    except Exception as e:
        app_logger.error(f"Failed to open MIDI port '{control_input_name}': {e}")
        return None
