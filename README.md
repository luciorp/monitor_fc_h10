# Heart Rate Monitor — Polar H10 / XOSS / BLE GATT

A Python desktop application that connects to Bluetooth Low Energy (BLE) heart rate chest straps and logs heart rate readings to a CSV file with timestamps.

Compatible with any device that implements the standard **BLE GATT Heart Rate Service (0x180D)**, including Polar H10, XOSS H1/X1, Wahoo TICKR, Garmin HRM, and others.

---

## Features

- Interactive CLI — no command-line arguments needed; guides the user step by step
- Automatic BLE device scan with numbered selection
- Configurable test duration (in minutes) or unlimited run
- Logs one reading per second to a CSV file
- Timestamps every entry with date and time (YYYY-MM-DD HH:MM:SS)
- Flush-on-write: no data loss if the program is closed unexpectedly
- Standalone Windows executable available (no Python required to run)

---

## Requirements

- Python 3.9 or higher
- Windows 10/11 with Bluetooth 4.0+ adapter
- [`bleak`](https://github.com/hbldh/bleak) library

---

## Installation

```bash
pip install -r requirements.txt
```

Or install the dependency directly:

```bash
pip install bleak
```

---

## Usage

Run the script:

```bash
python monitor_h10.py
```

The program will guide you through three steps:

**Step 1 — Device address**
Press `Enter` to scan for nearby BLE devices (takes ~10 seconds), then select your heart rate monitor by number. Alternatively, type the address directly (e.g. `A0:B1:C2:D3:E4:F5`).

**Step 2 — Test duration**
Enter the duration in minutes (e.g. `10` for 10 minutes, `5.5` for 5 min 30 s). Press `Enter` to run indefinitely and stop with `Ctrl+C`.

**Step 3 — Monitoring**
The program connects to the device and starts logging. Output example:

```
------------------------------------------------------
  TEST IN PROGRESS
------------------------------------------------------

  Duration  : 10m 0s  (600s total)
  Interval  : 1 second
  File      : hr_20260611_085500.csv

  [08:55:01]    72 bpm   (reading #1)
  [08:55:02]    74 bpm   (reading #2)
  [08:55:03]    73 bpm   (reading #3)
  ...
```

---

## Output

A CSV file is created automatically in the same directory as the script (or executable), named `hr_YYYYMMDD_HHMMSS.csv`:

```
data,hora,bpm
2026-06-11,08:55:01,72
2026-06-11,08:55:02,74
2026-06-11,08:55:03,73
```

---

## Building the Windows Executable

To produce a standalone `.exe` that runs without Python installed:

**1. Install build dependencies**

```bash
pip install bleak pyinstaller
```

**2. Run PyInstaller**

```bash
pyinstaller --onefile --console --name "Monitor_FC_H10" \
  --collect-all bleak \
  --collect-all winrt \
  --hidden-import bleak.backends.winrt \
  --hidden-import bleak.backends.winrt.scanner \
  --hidden-import bleak.backends.winrt.client \
  monitor_h10.py
```

The executable is generated at `dist/Monitor_FC_H10.exe`. Deliver only that file to end users — no Python installation required.

---

## Protocol

This application uses the standard **Bluetooth GATT Heart Rate Service**:

| Item | Value |
|------|-------|
| Service UUID | `0000180d-0000-1000-8000-00805f9b34fb` |
| Characteristic UUID | `00002a37-0000-1000-8000-00805f9b34fb` |
| Transport | BLE (Bluetooth Low Energy) |

No proprietary SDKs or vendor-specific protocols are required.

---

## Compatible Devices (tested or expected)

| Device | Protocol | Expected to work |
|--------|----------|-----------------|
| Polar H10 | BLE GATT HRS + ANT+ | ✅ |
| XOSS H1 / X1 | BLE GATT HRS + ANT+ | ✅ |
| Wahoo TICKR | BLE GATT HRS + ANT+ | ✅ |
| Garmin HRM-Pro | BLE GATT HRS + ANT+ | ✅ |
| Any BLE GATT HRS device | BLE GATT HRS | ✅ |

---

## License

MIT
