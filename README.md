# MAX3107 SPI Decoder

A [Logic 2](https://www.saleae.com/downloads/) High Level Analyzer (HLA) extension that decodes SPI transactions to and from a MAX3107 UART bridge IC.

## Overview

The MAX3107 is a UART-to-SPI bridge. Its SPI protocol encodes register reads and writes in each chip-select transaction: the first byte carries the direction bit (bit 7) and a 7-bit register address, followed by one or more data bytes. This extension decodes that framing and annotates each transaction with a human-readable register name and value directly on the waveform.

## Frame types

| Type | Display | Description |
|------|---------|-------------|
| `thr_write` | `A`, `\r`, `\x1B` … | Byte written to the TX holding register (THR, address `0x00`) — data being pushed into the UART TX FIFO |
| `rhr_read` | `A`, `\r`, `\x1B` … | Byte read from the RX holding register (RHR, address `0x00`) — data being drained from the UART RX FIFO |
| `reg_write` | `W MODE1: 0x0E` | Write to any other register; burst writes emit one frame per byte with the address auto-incremented |
| `reg_read` | `R TxFIFOLvl: 0x03` | Read from any other register; burst reads emit one frame per byte with the address auto-incremented |

## Notes

- `thr_write` and `rhr_read` bytes are formatted using `_fmt_byte`: printable ASCII characters are shown as-is; common control characters (`\r`, `\n`, `\t`) are shown as escape sequences; all other bytes are shown as `\xNN`.
- Register values for `reg_write` and `reg_read` frames are pre-formatted as hex. The Logic 2 global number display base affects `thr_write` and `rhr_read` single-byte values.
- Burst transactions (multi-byte reads or writes to registers other than `0x00`) emit one frame per byte. The MAX3107 auto-increments the register address on each byte, and this is reflected in the frame annotations.
