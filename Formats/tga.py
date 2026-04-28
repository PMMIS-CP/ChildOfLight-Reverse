import struct
from typing import Tuple, Dict, Any, Optional

def _read_uint32_le(data: bytes, offset: int) -> int:
    return struct.unpack('<I', data[offset:offset+4])[0]

def _read_uint16_le(data: bytes, offset: int) -> int:
    return struct.unpack('<H', data[offset:offset+2])[0]

TGA_VALID_TYPES = {1, 2, 3, 9, 10, 11}
MAX_DIM = 16384

def _verify_tga(data: bytes) -> Tuple[bool, str, int, int]:
    if len(data) < 18:
        return False, "Too small for TGA header", 0, 0
    img_type = data[2]
    if img_type not in TGA_VALID_TYPES:
        return False, f"Unsupported TGA type {img_type}", 0, 0
    width = _read_uint16_le(data, 12)
    height = _read_uint16_le(data, 14)
    if not (0 < width <= MAX_DIM and 0 < height <= MAX_DIM):
        return False, f"Invalid dimensions {width}x{height}", 0, 0
    return True, f"TGA {width}x{height}, type {img_type}", width, height

def _verify_dds(data: bytes) -> Tuple[bool, str, int, int]:
    if len(data) < 128 or data[:4] != b'DDS ':
        return False, "Missing DDS magic or too small", 0, 0
    width = _read_uint32_le(data, 16)
    height = _read_uint32_le(data, 12)
    if not (0 < width <= MAX_DIM and 0 < height <= MAX_DIM):
        return False, f"Invalid dimensions {width}x{height}", 0, 0
    fourcc = data[80:84].decode('ascii', errors='ignore')
    return True, f"DDS {width}x{height}, {fourcc}", width, height

def _find_tga_header(data: bytes, search_limit: int = 4096) -> Optional[int]:
    # Looking for valid TGA header within first few KB
    limit = min(len(data) - 18, search_limit)
    for i in range(limit):
        img_type = data[i+2] if i+2 < len(data) else 0
        if img_type not in TGA_VALID_TYPES:
            continue
        width = _read_uint16_le(data, i+12)
        height = _read_uint16_le(data, i+14)
        if 0 < width <= MAX_DIM and 0 < height <= MAX_DIM:
            return i
    return None

def _strip_and_validate(data: bytes) -> Tuple[bool, Optional[str], Optional[bytes], Dict[str, Any]]:
    # Try DDS first, seems more common
    dds_pos = data.find(b'DDS ')
    if dds_pos != -1:
        candidate = data[dds_pos:]
        valid, msg, w, h = _verify_dds(candidate)
        if valid:
            meta = {
                'width': w, 'height': h, 'format': 'DDS',
                'message': msg, 'stripped_bytes': dds_pos
            }
            return True, '.dds', candidate, meta

    tga_start = _find_tga_header(data)
    if tga_start is not None:
        candidate = data[tga_start:]
        valid, msg, w, h = _verify_tga(candidate)
        if valid:
            meta = {
                'width': w, 'height': h, 'format': 'TGA',
                'message': msg, 'stripped_bytes': tga_start
            }
            return True, '.tga', candidate, meta

    return False, None, None, {}

def process_image_data(raw_chunk_data: bytes) -> Tuple[bool, Optional[str], Optional[bytes], Dict[str, Any]]:
    # This is kinda naive, but works for now
    return _strip_and_validate(raw_chunk_data)