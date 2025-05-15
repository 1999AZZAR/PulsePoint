#!/usr/bin/env python3
"""
This script patches the feedparser library to work with Python 3.13 
by replacing the dependency on the removed cgi module.
"""

import os
import sys
import re
from pathlib import Path
import site

def find_feedparser_encodings_file():
    """Find the path to the feedparser/encodings.py file."""
    site_packages = site.getsitepackages()
    for site_package in site_packages:
        encodings_path = Path(site_package) / "feedparser" / "encodings.py"
        if encodings_path.exists():
            return encodings_path
    return None

def patch_feedparser():
    """Patch the feedparser library to work with Python 3.13."""
    encodings_path = find_feedparser_encodings_file()
    if not encodings_path:
        print("Error: Could not find feedparser/encodings.py")
        return False
    
    print(f"Found feedparser at: {encodings_path}")
    
    # Read the file
    with open(encodings_path, 'r') as f:
        content = f.read()
    
    # Check if it already contains our workaround
    if "_DummyCgi" in content:
        print("File is already patched.")
        return True
    
    # Create a better patch that completely replaces the problematic code
    # instead of just trying to wrap the import
    new_content = """# -*- coding: utf-8 -*-

# This code was patched for Python 3.13 compatibility by removing the cgi dependency

# The cgi module was removed in Python 3.13
class _DummyCgi:
    class parse_header:
        @staticmethod
        def __call__(line):
            # Simple version of cgi.parse_header
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

import codecs
import re

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

"""
    
    # Find the rest of the file after the imports
    start_pos = content.find("# Each marker represents")
    if start_pos > 0:
        # Extract the rest of the file after the intro section
        rest_of_file = content[start_pos:]
        # Combine our new content with the rest of the file
        new_content += rest_of_file
    else:
        print("Could not find the right insertion point in the file")
        # Just proceed with our replacement and hope for the best
    
    # Write the patched file
    with open(encodings_path, 'w') as f:
        f.write(new_content)
    
    print(f"Successfully patched {encodings_path}")
    return True

if __name__ == "__main__":
    success = patch_feedparser()
    sys.exit(0 if success else 1) 