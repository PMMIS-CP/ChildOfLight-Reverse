import struct
from pathlib import Path
from typing import List, Dict, Any

def read_uint32_be(data: bytes, offset: int) -> int:
    return struct.unpack('>I', data[offset:offset+4])[0]

def read_uint32_le(data: bytes, offset: int) -> int:
    return struct.unpack('<I', data[offset:offset+4])[0]

def parse_ckd(file_path: str) -> List[Dict[str, Any]]:
    # Quick and dirty parser, might need tweaking for edge cases
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'rb') as f:
        raw_data = f.read()
    file_size = len(raw_data)

    chunks = []
    offset = 0
    MIN_HEADER = 12

    while offset <= file_size - MIN_HEADER:
        header_size = read_uint32_be(raw_data, offset)
        if header_size != 12:
            remaining = raw_data[offset:]
            if remaining:
                chunks.append({'tag': 'RAW', 'data': remaining, 'offset': offset})
            break

        tag_bytes = raw_data[offset+4:offset+8]
        try:
            tag = tag_bytes.decode('ascii').strip()
        except UnicodeDecodeError:
            tag = 'RAW'

        chunk_size = read_uint32_be(raw_data, offset+8)
        data_start = offset + header_size
        data_end = data_start + chunk_size

        if chunk_size == 0 or data_end > file_size:
            remaining = raw_data[offset:]
            if remaining:
                chunks.append({'tag': 'RAW', 'data': remaining, 'offset': offset})
            break

        chunk_data = raw_data[data_start:data_end]
        chunks.append({'tag': tag, 'data': chunk_data, 'offset': offset})
        offset = data_end

        # Handle leftover bytes that don't form a proper chunk
        if offset < file_size:
            if offset + 12 <= file_size:
                next_hsize = read_uint32_be(raw_data, offset)
                if next_hsize != 12:
                    extra = raw_data[offset:]
                    if extra:
                        chunks[-1]['data'] += extra
                    break
            else:
                extra = raw_data[offset:]
                if extra:
                    chunks[-1]['data'] += extra
                break

    if not chunks:
        chunks = [{'tag': 'RAW', 'data': raw_data, 'offset': 0}]

    return chunks