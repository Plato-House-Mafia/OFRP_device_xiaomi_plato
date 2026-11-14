#!/usr/bin/env python3
"""Add or replace recovery using AOSP tools. Output is unsigned."""

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
import tempfile


MAX_SIZE = 64 * 1024 * 1024
MAX_FRAGMENTS = 64
PAGE_SIZE = 4096
HEADER_SIZE = 2128
ENTRY_SIZE = 108


def require(condition, message):
    if not condition:
        raise ValueError(message)


def aligned(size):
    return (size + PAGE_SIZE - 1) // PAGE_SIZE * PAGE_SIZE


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_bounded(path):
    # Reject FIFOs without blocking.
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NONBLOCK), 'rb') as stream:
        metadata = os.fstat(stream.fileno())
        require(stat.S_ISREG(metadata.st_mode), f'Input must be a regular file: {path}')
        require(metadata.st_size <= MAX_SIZE, f'Input exceeds 64 MiB: {path}')
        data = stream.read(MAX_SIZE + 1)
    require(len(data) <= MAX_SIZE, f'Input exceeds 64 MiB: {path}')
    require(data, f'Input ramdisk/image is empty: {path}')
    return data


def c_string(raw, label):
    text, separator, padding = raw.partition(b'\0')
    require(separator and not any(padding), f'Unsupported header/name encoding: {label}')
    return text.decode('ascii')


def inspect_image(data):
    """Validate the input image."""
    require(len(data) >= HEADER_SIZE and data[:8] == b'VNDRBOOT',
            'Invalid or truncated VNDRBOOT header')
    version, page, kernel, ramdisk_address, ramdisk_size = struct.unpack_from('<5I', data, 8)
    header_size, dtb_size, dtb_address = struct.unpack_from('<IIQ', data, 2096)
    require((version, page, header_size) == (4, PAGE_SIZE, HEADER_SIZE),
            'Unsupported header: require VNDRBOOT v4, 4096-byte pages, header size 2128')
    table_size, count, entry_size, config_size = struct.unpack_from('<4I', data, 2112)
    require(1 <= count <= MAX_FRAGMENTS and entry_size == ENTRY_SIZE
            and table_size == count * ENTRY_SIZE,
            'Unsupported layout: invalid fragment table dimensions (maximum 64 entries)')
    dtb_start = PAGE_SIZE + aligned(ramdisk_size)
    table_start = dtb_start + aligned(dtb_size)
    config_start = table_start + aligned(table_size)
    end = config_start + aligned(config_size)
    require(end <= len(data) <= MAX_SIZE, 'Invalid layout: sections truncated or oversized')
    require(not any(data[end:]), 'Unsupported nonzero trailer (authentication data cannot be preserved)')
    # Reject nonzero padding.
    for start, size in ((0, HEADER_SIZE), (PAGE_SIZE, ramdisk_size),
                        (dtb_start, dtb_size), (table_start, table_size),
                        (config_start, config_size)):
        require(not any(data[start + size:start + aligned(size)]),
                'Unsupported layout: nonzero section padding')

    fragments = []
    names = set()
    cursor = 0
    for index in range(count):
        size, offset, kind, raw_name, *ids = struct.unpack_from(
            '<III32s16I', data, table_start + index * ENTRY_SIZE)
        name = c_string(raw_name, 'fragment name')
        require(re.fullmatch(r'[A-Za-z0-9_.-]*', name) is not None and name != 'default',
                'Unsupported fragment name')
        require(name not in names, 'Duplicate fragment name in layout')
        names.add(name)
        require(size > 0 and offset == cursor and offset + size <= ramdisk_size,
                'Ambiguous layout: empty, overlapping, gapped or out-of-range fragment')
        require(kind in (0, 1, 2, 3), 'Unsupported layout: unknown fragment type')
        if not name:
            require(kind == 1, 'Unsupported layout: unnamed fragment must be PLATFORM type 1')
        if name == 'recovery' or kind == 2:
            require(name == 'recovery' and kind == 2,
                    'Ambiguous recovery layout: only name recovery with type 2 is supported')
        payload = data[PAGE_SIZE + offset:PAGE_SIZE + offset + size]
        fragments.append({'index': index, 'name': name, 'type': kind,
                          'board_ids': ids, 'size': size, 'offset': offset,
                          'sha256': sha256(payload)})
        cursor += size
    require(cursor == ramdisk_size and '' in names,
            'Unsupported layout: require exactly one unnamed PLATFORM and complete fragment coverage')
    return {'header_version': version, 'page_size': page, 'kernel_address': kernel,
            'ramdisk_address': ramdisk_address,
            'tags_address': struct.unpack_from('<I', data, 2076)[0],
            'dtb_address': dtb_address, 'cmdline': c_string(data[28:2076], 'cmdline'),
            'board': c_string(data[2080:2096], 'board'),
            'dtb_size': dtb_size, 'dtb_sha256': sha256(data[dtb_start:dtb_start + dtb_size]),
            'bootconfig_size': config_size,
            'bootconfig_sha256': sha256(data[config_start:config_start + config_size]),
            'fragments': fragments}


def check_output(output, inputs):
    for source in inputs:
        require(output.resolve() != source.resolve()
                and not (output.exists() and os.path.samefile(output, source)),
                f'Output cannot alias input: {source}')
    require(not output.is_symlink(), 'Output must not be a symlink')
    require(not output.exists() or output.is_file(), 'Output must be a regular file')


def prepare(args):
    base, recovery_path, output = args.base, args.recovery, args.output
    check_output(output, (base, recovery_path))
    for tool in ('unpack_bootimg.py', 'mkbootimg.py'):
        require((args.tools / tool).is_file(), f'Missing AOSP tool: {args.tools / tool}')
    base_data = read_bounded(base)
    recovery_data = read_bounded(recovery_path)
    stripped_avb = False
    if base_data[-64:-60] == b'AVBf':
        require(getattr(args, 'strip_avb_footer', False), 'AVB footer present: use --strip-avb-footer to explicitly produce unsigned output')
        magic, major, minor, original, offset, size, reserved = struct.unpack('>4sIIQQQ28s', base_data[-64:])
        require(major == 1 and minor == 0 and not any(reserved), 'Unsupported AVB footer')
        require(HEADER_SIZE <= original <= offset and size >= 256
                and offset + size <= len(base_data) - 64
                and base_data[offset:offset + 4] == b'AVB0', 'Invalid AVB footer bounds or vbmeta magic')
        base_data = base_data[:original]
        stripped_avb = True
    before = inspect_image(base_data)
    expected_fragments = [dict(fragment) for fragment in before['fragments']]
    replacement = next((item for item in expected_fragments if item['name'] == 'recovery'), None)
    action = 'replace' if replacement is not None else 'append'
    if replacement is None:
        require(len(expected_fragments) < MAX_FRAGMENTS, 'Unsupported layout: maximum 64 fragments')
        replacement = {'index': len(expected_fragments), 'name': 'recovery',
                       'type': 2, 'board_ids': [0] * 16}
        expected_fragments.append(replacement)
    replacement.update(size=len(recovery_data), sha256=sha256(recovery_data))
    cursor = 0
    for fragment in expected_fragments:
        fragment['offset'] = cursor
        cursor += fragment['size']
    projected_size = (PAGE_SIZE + aligned(cursor) + aligned(before['dtb_size'])
                      + aligned(len(expected_fragments) * ENTRY_SIZE)
                      + aligned(before['bootconfig_size']))
    require(projected_size <= MAX_SIZE, 'Prepared image would exceed 64 MiB')

    # Keep bytecode out of the source trees.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('aosp_unpack_bootimg', args.tools / 'unpack_bootimg.py')
    unpacker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(unpacker)
    # Keep the final rename atomic.
    with tempfile.TemporaryDirectory(prefix='.prepare-vendor-boot-', dir=output.parent) as temporary:
        work = Path(temporary)
        unpacked = work / 'unpacked'
        info = unpacker.unpack_vendor_boot_image(io.BytesIO(base_data), str(unpacked))
        for fragment in before['fragments']:
            extracted = unpacked / info.vendor_ramdisk_table[fragment['index']][0]
            require(sha256(read_bounded(extracted)) == fragment['sha256'],
                    'AOSP unpack verification failed: fragment payload changed')
        recovery_name = f"vendor_ramdisk{replacement['index']:02}"
        (unpacked / recovery_name).write_bytes(recovery_data)
        if action == 'append':
            info.vendor_ramdisk_table.append((recovery_name, len(recovery_data),
                                             replacement['offset'], 2, 'recovery', (0,) * 16))
        staged = work / 'prepared.img'
        command = [sys.executable, '-B', str(args.tools / 'mkbootimg.py'),
                   *info.format_mkbootimg_argument(), '--vendor_boot', str(staged)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        require(result.returncode == 0, f'AOSP mkbootimg failed: {result.stderr.strip()}')
        prepared_data = read_bounded(staged)
        after = inspect_image(prepared_data)
        expected = dict(before, fragments=expected_fragments)
        require(after == expected and len(prepared_data) == projected_size,
                'Prepared image verification failed: metadata or payload preservation mismatch')
        report = {'action': action, 'check_only': args.check_only, 'avb_footer_stripped': stripped_avb, 'output_unsigned': True,
                  'base': dict(before, size=len(base_data), sha256=sha256(base_data)),
                  'recovery': {'size': len(recovery_data), 'sha256': sha256(recovery_data)},
                  'output': dict(after, size=len(prepared_data), sha256=sha256(prepared_data))}
        if not args.check_only:
            check_output(output, (base, recovery_path))
            os.replace(staged, output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--tools', type=Path, required=True, help='Directory containing trusted AOSP tools')
    parser.add_argument('--base', type=Path, required=True, help='Read-only source vendor_boot image')
    parser.add_argument('--recovery', type=Path, required=True, help='Nonempty recovery ramdisk payload')
    parser.add_argument('--output', type=Path, required=True, help='New host artifact; cannot alias either input')
    parser.add_argument('--strip-avb-footer', action='store_true', help='Explicitly remove a recognized AVB trailer; output is unsigned')
    parser.add_argument('--check-only', action='store_true', help='Build and verify without publishing output')
    args = parser.parse_args()
    try:
        report = prepare(args)
    except (OSError, ValueError, UnicodeError, struct.error, ImportError,
            AttributeError, subprocess.SubprocessError) as error:
        parser.exit(1, f'prepare_vendor_boot: {error}\n')
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
