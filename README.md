# AHMIDIProcessor

> [!CAUTION]  
> **This processor is still a work in progress**  

AHMIDIProcessor is a Python-based MIDI processing tool designed for interfacing with Allen & Heath digital audio mixers. It processes MIDI messages, converts them into OSC (Open Sound Control) messages, and facilitates communication between MIDI controllers and compatible audio software. The application also supports service discovery via mDNS.

## Features

- **MIDI Message Handling**: Receives and processes various MIDI messages, including:
  - SysEx (System Exclusive) messages
  - NRPN (Non-Registered Parameter Number) messages
  - Control Change (CC) messages
- **OSC Communication**: Translates MIDI messages into OSC messages and sends them to configured targets.
- **Configurable Logging**: Supports different logging levels and allows application name customization.
- **Flexible Message Templates**: Utilizes JSON templates for defining MIDI message structures.
- **Multi-Target Support**: Sends OSC messages to multiple targets concurrently.
- **Service Discovery (mDNS)**: Registers the application for automatic network discovery.

> [!NOTE]  
> Current limitations in message processing:
> - Sending OSC messages currently supports only MMC (MIDI Machine Control) messages and implemented SysEx messages
> - NRPN message processing is implemented but limited in scope.
> - Some SysEx messages might not be fully supported yet.

## Installation

### Prerequisites

- Python 3.10+
- A supported MIDI device (e.g., Allen & Heath Qu Mixing Console)
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
    "log_level": "DEBUG"
  },
  "midi_options": {
    "control_port_name": "MIDI Control 1 0",
    "midi_in_name": "Allen and Heath Processor",
    "queue_size_limit": 10240
  },
  "osc_options": {
    "listen": {
      "svc_port": 8080,
      "svc_name": "AHMIDIProcessor OSC",
      "svc_addr": "ahmidi.local",
      "svc_type": "_osc._udp.local.",
      "svc_props": {},
      "svc_ipver": "v4"
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
│   ├── cc.py              # Control Change handling
│   ├── data.py            # Application data structures
│   ├── hex.py             # Hexadecimal conversion utilities
│   ├── json.py            # JSON configuration handling
│   ├── mdns.py            # mDNS service registration
│   ├── midi.py            # MIDI interface and processing
│   ├── nrpn.py            # NRPN message handling
│   ├── osc.py             # OSC message handling
│   ├── sysex.py           # SysEx message processing
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
