#!/usr/bin/env python3
"""
Simple script to patch feedparser to work with Python 3.13
"""

import os
import sys
import site
from pathlib import Path

# Path to the feedparser encodings.py file
feedparser_path = Path(site.getsitepackages()[0]) / "feedparser" / "encodings.py"

# The content to replace the entire file with
new_content = """# -*- coding: utf-8 -*-

# Patched for Python 3.13 compatibility (cgi module removed in Python 3.13)

import codecs
import re

# Simple replacement for the cgi module
class _DummyCgi:
    class parse_header:
        @staticmethod
        def __call__(line):
            if not line:
                return '', {}
            parts = line.split(';')
            key = parts[0].strip()
            params = {}
            for part in parts[1:]:
                if '=' in part:
                    name, value = part.split('=', 1)
                    name = name.strip()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    params[name] = value
            return key, params
    parse_header = parse_header()

cgi = _DummyCgi()

try:
    codecs.lookup('utf-32be')
except LookupError:
    # Some versions of Python (particularly on mobile or embedded platforms)
    # don't have the utf-32 codecs
    _UTF32_AVAILABLE = False
else:
    _UTF32_AVAILABLE = True

bytes_types = (bytes, bytearray)

# Each marker represents a sequence that starts with a byte with the high
# bit set (0x80) and ends with a byte with the high bit not set.
_enc_pattern = re.compile(b'[\x80-\xFF][\x00-\x7F]+')


def convert_to_utf8(http_headers, data, result):
    '''Attempt to decode an octet stream as utf-8, then
       attempt to perform content type encoding from headers if that fails.
       This function doesn't care about the result.  The caller is responsible
       for handling failure from different parts of the response or any
       partial failures from this function.

       Args:
           http_headers:     dict or list, data structure that supports .get()
           data:       the octet stream as bytes
           result:     a results dict that supports [].  Key names will be unique.

       Notes:
           This function is here to consolidate special case code from three places.
    '''
    # Check for specified encoding
    result['encoding'] = http_headers.get('content-type', '')
    charset = _get_charset(result['encoding'])
    result['encoding'] = charset

    # These are technically incorrect. Specified encoding actually takes precedence
    # over any encoding determined by sniffing, but the sniffing code is currently
    # more accurate and the specified encoding can be wrong.

    # Check for BOM encodings
    if data and data[:2] in (b'\xfe\xff', b'\xff\xfe'):
        if not _UTF32_AVAILABLE:
            # Replace trailing \r with \r\n if we do CR-only newlines
            envelope = data
            if (data[:2] == b'\xfe\xff' and
                    len(data) >= 4 and
                    data[2:4] != b'\x00\r' and
                    data[2:4] != b'\x00\n' and
                    b'\x00\r' in data and
                    b'\x00\n' not in data):
                envelope = data.replace(b'\x00\r', b'\x00\r\x00\n')
            elif (data[:2] == b'\xff\xfe' and
                  len(data) >= 4 and
                  data[2:4] != b'\r\x00' and
                  data[2:4] != b'\n\x00' and
                  b'\r\x00' in data and
                  b'\n\x00' not in data):
                envelope = data.replace(b'\r\x00', b'\r\x00\n\x00')
            if envelope != data:
                data = envelope
                result['bozo'] = True
                result['bozo_exception'] = (
                    'line endings could not be normalized for UTF-16')

        # Encoded as UTF-16, little or big endian (BOM present)
        if data[:2] == b'\xfe\xff':
            if _UTF32_AVAILABLE and data[:4] in (b'\xfe\xff\x00\x00', b'\xfe\xff\x00['):
                # Encoded as UTF-32, big endian (BOM present)
                data = data.decode('utf-32be').encode('utf-8')
            else:
                # Encoded as UTF-16, big endian (BOM present)
                data = data.decode('utf-16be').encode('utf-8')
        elif data[:2] == b'\xff\xfe':
            if _UTF32_AVAILABLE and data[:4] in (b'\xff\xfe\x00\x00', b'\xff\xfe[\x00'):
                # Encoded as UTF-32, little endian (BOM present)
                data = data.decode('utf-32le').encode('utf-8')
            else:
                # Encoded as UTF-16, little endian (BOM present)
                data = data.decode('utf-16le').encode('utf-8')
        # Update result
        result['encoding'] = 'utf-8'

    #: First let's try to detect UTF-8.  We're going to look for an encoding marker.
    #: UTF-8 has a marker that can use 2-4 0x80+ bytes if we're lucky, and more
    #: 0x80+ bytes if we're really lucky.  But we can't look for those if it's english
    #: because the only ascii chars in the encoding regex is the first (start) and the
    #: last (stop) characters in the byte string.
    # Check for UTF-8 encoding signature
    if data and charset != 'utf-8' and charset != 'us-ascii':
        #: Let's look for one 0x80+ byte followed by one ascii (< 0x80) byte.
        #: That should match the marker.
        matches = _enc_pattern.findall(data)
        # TODO: get more data and retry?
        if matches:
            #: We might have a unicode BOM on the front, which is ok.  Let's strip
            #: that off.
            if data and data.startswith(codecs.BOM_UTF8):
                data = data[len(codecs.BOM_UTF8):]
            #: Ok, is there a high probability that we have unicode?
            try:
                data = data.decode('utf-8').encode('utf-8')
                result['encoding'] = 'utf-8'
            except (UnicodeDecodeError, LookupError):
                pass

    # Attempt to decode with the encoding that was specified in the headers
    if charset and charset != 'utf-8':
        try:
            data = data.decode(charset).encode('utf-8')
            result['encoding'] = 'utf-8'
        except (UnicodeDecodeError, LookupError):
            pass

    # Try to get lucky with a guesstimate if all else fails
    if isinstance(data, bytes_types) and charset != 'utf-8':
        try:
            data = data.decode('utf-8').encode('utf-8')
            result['encoding'] = 'utf-8'
        except UnicodeDecodeError:
            pass

    return data


def _get_charset(content_type_header):
    '''
    >>> _get_charset('text/html; charset=iso8859-1')
    'iso8859-1'
    >>> _get_charset('text/html; charset=utf-8')
    'utf-8'
    >>> _get_charset('text/html; charset=ISO-8859-1')
    'iso8859-1'
    >>> _get_charset('text/html')
    ''
    '''
    dummy_content_type, params = cgi.parse_header(content_type_header)
    return params.get('charset', '').lower()
"""

# Write the new content
with open(feedparser_path, "w") as f:
    print(f"Patching {feedparser_path}")
    f.write(new_content)
    print("Done!") 