# AHMIDIProcessor
> [!CAUTION]
> **This processor is still a work in progress**

AHMIDIProcessor is a Python-based MIDI processing tool designed for interfacing with Allen & Heath digital audio mixers. It processes MIDI messages, converts them into OSC (Open Sound Control) messages, and facilitates communication between MIDI controllers and compatible audio software.

## Features

- **MIDI Message Handling**: Receives and processes MIDI messages, including SysEx and NRPN messages.
- **OSC Communication**: Translates MIDI messages into OSC messages and sends them to configured targets.
- **Configurable Logging**: Supports logging levels and application name configuration.
- **Flexible Template System**: Utilizes JSON templates for defining MIDI message structures.
- **Multi-Target Support**: Sends OSC messages to multiple targets concurrently.

> [!NOTE]
> There are currently some limitations for message processing, further support will be added later:
> * Sending OSC messages only supports MMC messages
> * NRPN messages decoding is not currently implemented

## Installation

### Prerequisites
- Python 3.10+
- A supported MIDI device (Allen & Heath Qu Mixing Console)
- Required Python dependencies

### Setup
1. Clone the repository:
   ```sh
   git clone https://github.com/ellisdickinson46/AHMIDIProcessor.git
   cd AHMIDIProcessor
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

Run the application using:
```sh
python main.py
```
By default, the application reads configurations from `app_config.json` and `templates.json`.

### Configuration

Modify `app_config.json` to adjust MIDI and OSC settings:

```json
{
  "app_options": {
    "application_name": "AHMIDIProcessor",
    "log_level": "INFO"
  },
  "midi_options": {
    "control_port_name": "MIDI Control 1",
    "queue_size_limit": 10240
  },
  "osc_options": {
    "listen": {
      "address": "0.0.0.0",
      "port": 8080
    },
    "targets": {
      "target_0": {
        "address": "127.0.0.1",
        "port": 8000
      }
    }
  }
}
```

## Project Structure

```
.
├── helpers/               # Helper modules for MIDI, JSON, OSC, and conversion
│   ├── communicator.py    # MIDI communication setup
│   ├── convert.py         # Utility for data conversion
│   ├── json_handler.py    # JSON configuration handling
│   ├── osc.py             # OSC message handling
├── main.py                # Entry point for AHMIDIProcessor
├── templates.json         # MIDI message structure definitions
├── app_config.json        # Application and communication settings
├── requirements.txt       # Python dependencies
├── LICENSE                # GNU General Public License v3.0
```

## License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.

## Author

Developed by [Ellis Dickinson](https://github.com/ellisdickinson46). Contributions are welcome!