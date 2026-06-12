from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame

# MAX3107 register map (address -> name)
REGISTERS = {
    0x00: 'THR/RHR',
    0x01: 'IRQEn',
    0x02: 'ISR',
    0x03: 'LSRIntEn',
    0x04: 'LSR',
    0x05: 'SpclChrIntEn',
    0x06: 'SpclCharInt',
    0x07: 'STSIntEn',
    0x08: 'STSInt',
    0x09: 'MODE1',
    0x0A: 'MODE2',
    0x0B: 'LCR',
    0x0C: 'RxTimeOut',
    0x0D: 'HDplxDelay',
    0x0E: 'IrDA',
    0x0F: 'FlowLvl',
    0x10: 'FIFOTrgLvl',
    0x11: 'TxFIFOLvl',
    0x12: 'RxFIFOLvl',
    0x13: 'FlowCtrl',
    0x14: 'XON1',
    0x15: 'XON2',
    0x16: 'XOFF1',
    0x17: 'XOFF2',
    0x18: 'GPIOConfg',
    0x19: 'GPIOData',
    0x1A: 'PLLConfig',
    0x1B: 'BRGConfig',
    0x1C: 'DIVLSB',
    0x1D: 'DIVMSB',
    0x1E: 'CLKSource',
    0x1F: 'RevID',
}


def _fmt_byte(val):
    if 0x20 <= val < 0x7F:
        return chr(val)
    if val == 0x0D:
        return '\\r'
    if val == 0x0A:
        return '\\n'
    if val == 0x09:
        return '\\t'
    return f'\\x{val:02X}'


class MAX3107Decoder(HighLevelAnalyzer):
    result_types = {
        'thr_write': {
            'format': '{{data.value}}'
        },
        'rhr_read': {
            'format': '{{data.value}}'
        },
        'reg_read': {
            'format': 'R {{data.reg}}: {{data.value}}'
        },
        'reg_write': {
            'format': 'W {{data.reg}}: {{data.value}}'
        },
    }

    def __init__(self):
        # Each entry: (mosi_int, miso_int, start_time, end_time)
        self._bytes = []

    def decode(self, frame: AnalyzerFrame):
        if frame.type == 'enable':
            self._bytes = []
            return None

        if frame.type == 'result':
            mosi = frame.data.get('mosi', b'\x00')
            miso = frame.data.get('miso', b'\x00')
            mosi_val = mosi[0] if mosi else 0
            miso_val = miso[0] if miso else 0
            self._bytes.append((mosi_val, miso_val, frame.start_time, frame.end_time))
            return None

        if frame.type == 'disable':
            return self._process_transaction()

        return None

    def _process_transaction(self):
        if len(self._bytes) < 2:
            return None

        cmd      = self._bytes[0][0]
        is_write = bool(cmd & 0x80)
        addr     = cmd & 0x7F
        payload  = self._bytes[1:]

        if addr == 0x00:
            out = []
            if is_write:
                # Burst write to THR — each byte is UART TX data
                for mosi_val, _, start, end in payload:
                    out.append(AnalyzerFrame('thr_write', start, end, {
                        'value': _fmt_byte(mosi_val),
                    }))
            else:
                # Burst read from RHR — each byte is UART RX data
                for _, miso_val, start, end in payload:
                    out.append(AnalyzerFrame('rhr_read', start, end, {
                        'value': _fmt_byte(miso_val),
                    }))
            return out

        out = []
        for i, (mosi_val, miso_val, start, end) in enumerate(payload):
            current_addr = (addr + i) & 0x7F
            current_reg = REGISTERS.get(current_addr, f'0x{current_addr:02X}')
            if is_write:
                out.append(AnalyzerFrame('reg_write', start, end, {
                    'reg': current_reg,
                    'value': f'0x{mosi_val:02X}',
                }))
            else:
                out.append(AnalyzerFrame('reg_read', start, end, {
                    'reg': current_reg,
                    'value': f'0x{miso_val:02X}',
                }))
        return out
