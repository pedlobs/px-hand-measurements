# PX Hand Measurements

PX Hand Measurements is a prototype for acquiring hand sensor data. The repository currently contains STM32 firmware, an incomplete Python desktop application, KiCad board-design files, and a NestJS starter project.

> **Current status:** the firmware and Python application are not yet integrated into a working end-to-end workflow. In particular, the firmware's serial output format is not accepted by the Python serial parser, and the desktop application's UI and some referenced types/configuration are incomplete.

## Overview

The diagram below shows the intended measurement flow and the current implementation boundary. Solid arrows indicate data the firmware emits; dashed arrows are the intended host-app path, which is not yet functional end to end.

```text
Sensors / analog circuit
          |
          v
STM32WB55 firmware
  ADC: C0-C3; PWM outputs
          |
          | USB CDC: "C0=... C1=... C2=... C3=..."
          v
      USB serial
          |
          | - - - format mismatch: SerialWorker does not parse C0=... lines
          v
host_app / SerialWorker - - -> telemetry queue - - -> Tkinter UI [incomplete]
                                                       |
                                                       | intended capture
                                                       v
                                                 DataLogger
                                                       |
                                                       | .xlsx
                                                       v
                                                 DataMerger
                                                       |
                                                       v
                                               consolidated .csv

hardware/kicad_project: schematic and PCB for the electronics
API-Testing--main: NestJS starter configuration, not an implemented API
```

The host application's serial, UI, logging, and consolidation pieces are not currently integrated into a working workflow.

## Repository structure

| Path | Contents |
| --- | --- |
| `4_sensors_4_led_working/UART_Example/` | STM32CubeIDE/CubeMX project for the STM32WB55 |
| `4_sensors_4_led_working/UART_Example/Core/Src/main.c` | ADC acquisition, USB CDC output, and PWM updates |
| `4_sensors_4_led_working/UART_Example/UART_Example.ioc` | STM32CubeMX peripheral and pin configuration |
| `host_app/src/main.py` | Python desktop application entry point using Tkinter |
| `host_app/src/config.py` | Serial, hardware, and UI configuration dataclasses |
| `host_app/src/models/telemetry.py` | Telemetry data model |
| `host_app/src/services/serial_worker.py` | Serial-port reading, parsing, and simulated telemetry |
| `host_app/src/services/data_logger.py` | Excel capture service |
| `host_app/src/services/data_merger.py` | Excel-to-CSV consolidation service |
| `host_app/requirements.txt` | Python dependency file; currently empty |
| `hardware/kicad_project/` | KiCad schematic, PCB layout, and project |
| `hardware/kicad_project/pcb projet-backups/` | KiCad board backups |
| `API-Testing--main/API-Testing--main/` | NestJS project configuration; no application source is currently present |

Generated STM32 build files are under `4_sensors_4_led_working/UART_Example/Debug/`. Treat them as build outputs rather than the primary source to edit.

## STM32 firmware

The firmware project targets the **STM32WB55RGVx** and is configured for STM32CubeWB **V1.23.0**. Its `.ioc` file configures ADC1 for four conversions:

| Firmware label | MCU pin | ADC channel |
| --- | --- | --- |
| `C0` | `PC0` | 1 |
| `C1` | `PC1` | 2 |
| `C2` | `PA0` | 5 |
| `C3` | `PA1` | 6 |

The firmware sends one text line over USB CDC approximately every 200 ms, for example:

```text
C0=2345  C1=2301  C2=2198  C3=2450
```

It also updates four PWM channels from the ADC readings. The output pins and peripheral configuration are recorded in `UART_Example.ioc`.

### Build and flash

1. Install **STM32CubeIDE** and the matching STM32WB firmware package.
2. Open `4_sensors_4_led_working/UART_Example/` as an existing STM32CubeIDE project.
3. Check the target and build settings, then build in the IDE.
4. Connect the board and flash it using the procedure for your board and programmer.

The checked-in `Debug` build files may include environment-specific settings. Use STM32CubeIDE to regenerate or configure the build for your machine rather than assuming the generated makefile is portable.

## Python desktop application

The Python application is under `host_app/` and is structured as a Tkinter desktop app with serial and data services. Its current source includes:

- Serial port enumeration and reading at a configurable baud rate (default `115200`).
- A parser for JSON telemetry (`s`/`sensors` and optional `l`/`leds` fields) and whitespace-separated numeric readings.
- A simulation mode that generates four sensor and four LED values.
- Services intended to save capture samples to `.xlsx` and consolidate spreadsheets into a semicolon-separated CSV.

The data logger's legacy spreadsheet columns are:

```text
Timestamp, Name, DOB, Age, Description, Movement, Finger, C0, C1, C2, C3
```

The merger groups records by movement and finger. It uses `C3` for `Push` and `Pull`; for other movement values it calculates statistics for `C0`, `C1`, and `C2`.

### Current implementation gaps

The desktop application is **not currently runnable as a complete application**:

- `host_app/src/ui/app_window.py` is empty, although `main.py` imports `PxHandAppWindow` from it.
- The logger and merger import `LoggingConfig`, which is not defined in `host_app/src/config.py`.
- The logger imports `TrialMetadata`, which is not defined in `host_app/src/models/telemetry.py`.
- `host_app/requirements.txt` is empty, although the services import third-party packages such as `pyserial`, `openpyxl`, and `pandas`.
- The firmware emits labeled values such as `C0=2345`, but `SerialWorker` currently parses JSON or whitespace-separated numbers. The firmware's current output therefore will not be parsed by that worker.

These items need to be resolved before documenting a supported run command or end-to-end data-capture workflow. The app code should be treated as an incomplete prototype, not a released workflow.

## KiCad board design

The KiCad project files are in `hardware/kicad_project/`:

- `pcb projet.kicad_pro` - project settings
- `pcb projet.kicad_sch` - schematic
- `pcb projet.kicad_pcb` - PCB layout

Open the `.kicad_pro` file in KiCad to inspect the schematic and board together. Check the component pin assignments, power, connectors, and consistency with the firmware before manufacturing or changing the hardware.

## NestJS starter project

`API-Testing--main/API-Testing--main/` contains NestJS configuration and package manifests, but no `src/` or test directory is present in the current repository tree. It is not currently an implemented measurement API.
