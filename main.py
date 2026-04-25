import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from ckd_parser import parse_ckd
from formats.tga import process_image_data

def _is_printable_text(data: bytes, threshold: float = 0.95) -> bool:
    sample = data[:512]
    if not sample:
        return False
    printable = sum(1 for b in sample if 32 <= b <= 126 or b in (9, 10, 13))
    return (printable / len(sample)) >= threshold

def _detect_extension_by_tag(tag: str) -> str:
    tag = tag.upper().strip()
    # This mapping might need updates if new formats show up
    mapping = {
        'A3D': '.a3d',
        'ACT': '.act',
        'ANM': '.anm',
        'ASC': '.asc',
        'FCG': '.fcg',
        'FRT': '.frt',
        'GMT': '.gmt',
        'ISC': '.isc',
        'ISG': '.isg',
        'M3D': '.m3d',
        'MCD': '.mcd',
        'MCLOTH': '.mcloth',
        'MSH': '.msh',
        'PBK': '.pbk',
        'PNG': '.png',
        'S3D': '.s3d',
        'SGS': '.sgs',
        'SKL': '.skl',
        'TFN': '.tfn',
        'TGA': '.tga',
        'TPL': '.tpl',
        'TSC': '.tsc',
    }
    return mapping.get(tag, '.bin')

def _get_output_extension(tag: str, data: bytes, image_ext: Optional[str]) -> str:
    # If we already know it's an image, just use that extension
    if image_ext:
        return image_ext
    ext = _detect_extension_by_tag(tag)
    if ext == '.bin' and _is_printable_text(data):
        return '.txt'
    return ext

def _prepare_output_data(data: bytes, image_result: Tuple[bool, Optional[str], Optional[bytes], Dict[str, Any]]) -> Tuple[bytes, str, bool]:
    success, ext, cleaned_data, meta = image_result
    if success and cleaned_data:
        stripped = meta.get('stripped_bytes', 0)
        print(f"   stripped {stripped} bytes of wrapper crap (got {meta['format']})")
        return cleaned_data, meta['message'], True
    else:
        return data, f"raw ({len(data)} bytes)", len(data) > 0

def extract_ckd(file_path: str, output_dir: Optional[str] = None):
    file_path = Path(file_path)
    out_path = Path(output_dir) if output_dir else Path(file_path.stem + "_extracted")
    out_path.mkdir(parents=True, exist_ok=True)

    chunks = parse_ckd(file_path)
    base_name = file_path.stem
    saved_files = []

    for idx, chunk in enumerate(chunks):
        tag = chunk['tag']
        data = chunk['data']
        offset = chunk['offset']

        image_result = process_image_data(data)
        final_data, health_msg, is_valid = _prepare_output_data(data, image_result)
        ext = _get_output_extension(tag, data, image_result[1] if image_result[0] else None)

        # Single chunk? just use base name
        if len(chunks) == 1:
            out_name = base_name + ext
        else:
            out_name = f"{base_name}_{tag}_{offset:06x}{ext}"

        out_file = out_path / out_name
        with open(out_file, 'wb') as f:
            f.write(final_data)

        status = "OK" if is_valid else "WARN"
        print(f"{status} {out_file}")
        print(f"   tag={tag}, size={len(final_data):,} bytes, offset=0x{offset:x}")
        print(f"   health: {health_msg}")
        saved_files.append(str(out_file))

    return saved_files

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract CKD containers (specific formats only)")
    parser.add_argument('input', help='Input CKD file')
    parser.add_argument('-o', '--output', help='Output directory')
    args = parser.parse_args()

    try:
        saved = extract_ckd(args.input, args.output)
        print(f"\nDone. Extracted {len(saved)} file(s).")
    except Exception as e:
        print(f"Something broke: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()