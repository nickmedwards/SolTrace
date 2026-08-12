"""
Parses a C/C++ header file (enums + function-pointer typedefs, the kind of
thing that sits in an ``extern "C"`` block backing a pybind/ctypes .so or
.dll) and exposes the results as a plain Python class:

    HeaderDefs.StatusCode          -> IntEnum
    HeaderDefs.AccessFlags         -> IntEnum
    HeaderDefs.ProgressCallback    -> ctypes.CFUNCTYPE(...)
    HeaderDefs.LogCallback         -> ctypes.CFUNCTYPE(...)

Usage
-----
    from cheader_bindings import HeaderDefs

    results = [HeaderDefs.StatusCode(code) for code in raw_status_codes]
    perms   = [HeaderDefs.AccessFlags.FLAG_READ | HeaderDefs.AccessFlags.FLAG_WRITE
               for _ in range(n)]

    @HeaderDefs.LogCallback
    def _log(msg: bytes) -> None:
        print(msg.decode())

Configuration
-------------
Adjust the constants in the "Configuration" section below for your project
(header filename, dev-tree search locations, packaged/production search
locations). All of them can also be overridden per-deployment via the
``PROJECT_HEADER_PATH`` and ``PROJECT_HEADER_CACHE_DIR`` environment
variables without touching this file.
"""

from __future__ import annotations

import ctypes, enum, os, re, sys, warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

__all__ = ["HeaderDefs", "locate_header", "reload_header_defs"]

# ---------------------------------------------------------------------------
# Configuration -- edit these for your project
# ---------------------------------------------------------------------------

_HEADER_FILENAME = "extern_c_cpp_header.h"

_ENV_HEADER_PATH = "PROJECT_HEADER_PATH"       # explicit full-path override

_STAPI_V2_DIR = Path(__file__).resolve().parent.parent

def _dev_search_paths(filename: str) -> List[Path]:
    """Locations to check when running from a source checkout."""
    return [
        _STAPI_V2_DIR / filename,
        _STAPI_V2_DIR / "include" / filename,
        _STAPI_V2_DIR.parent / "include" / filename,
        _STAPI_V2_DIR.parent / "cpp" / "include" / filename,
        Path.cwd() / "include" / filename,
    ]


def _prod_search_paths(filename: str) -> List[Path]:
    """Locations to check for a pip/whl-installed production deployment."""
    return [
        # Header shipped alongside this module as package data.
        _STAPI_V2_DIR / "_include" / filename,
        # Common "installed into the environment" locations.
        Path(sys.prefix) / "include" / filename,
        Path(sys.prefix) / "share" / "project" / "include" / filename,
    ]

# ---------------------------------------------------------------------------
# Header location
# ---------------------------------------------------------------------------

def locate_header(filename: str = _HEADER_FILENAME) -> Path:
    """Find the header file, dev tree first, then production locations.

    Raises FileNotFoundError with the full search list if nothing matches.
    """
    override = os.environ.get(_ENV_HEADER_PATH)
    candidates: List[Path] = []
    if override:
        candidates.append(Path(override))
    candidates.extend(_dev_search_paths(filename))
    candidates.extend(_prod_search_paths(filename))

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    searched = "\n  ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        f"Could not locate header '{filename}'. Set {_ENV_HEADER_PATH} to an "
        f"explicit path, or place the header in one of:\n  {searched}"
    )


# ---------------------------------------------------------------------------
# ctypes type resolution
# ---------------------------------------------------------------------------

_BASE_CTYPES: Dict[str, Optional[type]] = {
    "void":               None,
    "char":               ctypes.c_char,
    "signed char":        ctypes.c_byte,
    "unsigned char":      ctypes.c_ubyte,
    "short":              ctypes.c_short,
    "short int":          ctypes.c_short,
    "unsigned short":     ctypes.c_ushort,
    "unsigned short int": ctypes.c_ushort,
    "int":                ctypes.c_int,
    "unsigned int":       ctypes.c_uint,
    "unsigned":           ctypes.c_uint,
    "long":               ctypes.c_long,
    "unsigned long":      ctypes.c_ulong,
    "long long":          ctypes.c_longlong,
    "unsigned long long": ctypes.c_ulonglong,
    "float":              ctypes.c_float,
    "double":             ctypes.c_double,
    "long double":        ctypes.c_longdouble,
    "bool":               ctypes.c_bool,
    "_Bool":              ctypes.c_bool,
    "size_t":             ctypes.c_size_t,
    "ssize_t":            ctypes.c_ssize_t,
    "int8_t":             ctypes.c_int8,
    "uint8_t":            ctypes.c_uint8,
    "int16_t":            ctypes.c_int16,
    "uint16_t":           ctypes.c_uint16,
    "int32_t":            ctypes.c_int32,
    "uint32_t":           ctypes.c_uint32,
    "int64_t":            ctypes.c_int64,
    "uint64_t":           ctypes.c_uint64,
    "int_fast8_t":        ctypes.c_int8,
    "uint_fast8_t":       ctypes.c_uint8,
    "int_fast16_t":       ctypes.c_int16,
    "uint_fast16_t":      ctypes.c_uint16,
    "int_fast32_t":       ctypes.c_int32,
    "uint_fast32_t":      ctypes.c_uint32,
    "int_fast64_t":       ctypes.c_int64,
    "uint_fast64_t":      ctypes.c_uint64,
}

_WS_RE = re.compile(r"\s+")
_QUALIFIER_RE = re.compile(r"\b(const|volatile)\b")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_]\w*$")


def _strip_param_name(arg: str) -> str:
    """Turn 'const char* message' / 'int count' into just the type part,
    while leaving bare types like 'unsigned int' or 'StatusCode' untouched."""
    s = re.sub(r"\*", " * ", arg.strip())
    tokens = s.split()
    if len(tokens) <= 1:
        return arg.strip()
    last = tokens[-1]
    if last == "*" or last in ("const", "volatile"):
        return arg.strip()
    if _IDENTIFIER_RE.match(last) and last not in _BASE_CTYPES:
        tokens = tokens[:-1]
        return " ".join(tokens)
    return arg.strip()


def _resolve_ctype(type_str: str, enum_names: Dict[str, type]):
    """Map a C type string (possibly with '*') to a ctypes type."""
    s = _QUALIFIER_RE.sub("", type_str).strip()
    ptr_count = s.count("*")
    s = _WS_RE.sub(" ", s.replace("*", " ")).strip()
    base = s

    if base == "void":
        if ptr_count == 0:
            return None
        ctype = ctypes.c_void_p
        for _ in range(ptr_count - 1):
            ctype = ctypes.POINTER(ctype)
        return ctype

    if base == "char" and ptr_count == 1:
        return ctypes.c_char_p

    if base in enum_names:
        ctype = ctypes.c_int  # C enums are int-sized by default
    elif base in _BASE_CTYPES and _BASE_CTYPES[base] is not None:
        ctype = _BASE_CTYPES[base]
    else:
        # Unknown / opaque type (forward-declared struct, etc.) -- treat as
        # an opaque pointer-sized handle; this keeps parsing resilient
        # instead of failing the whole header on one exotic typedef.
        if ptr_count == 0:
            warnings.warn(
                f"cheader_bindings: unknown non-pointer type '{type_str}', "
                f"treating as opaque void*-sized value.",
                stacklevel=2,
            )
        ctype = ctypes.c_void_p
        ptr_count = max(ptr_count - 1, 0)

    for _ in range(ptr_count):
        ctype = ctypes.POINTER(ctype)
    return ctype


# ---------------------------------------------------------------------------
# Header text -> intermediate parsed data (plain dicts/tuples, picklable)
# ---------------------------------------------------------------------------

_COMMENT_RE = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)
_ENUM_RE = re.compile(
    r"typedef\s+enum\s*(?:[A-Za-z_]\w*)?\s*\{(?P<body>[^}]*)\}\s*(?P<name>[A-Za-z_]\w*)\s*;",
    re.DOTALL,
)
_FUNCPTR_RE = re.compile(
    r"typedef\s+(?P<ret>[A-Za-z_][\w\s]*?\**)\s*\(\s*\*\s*(?P<name>[A-Za-z_]\w*)\s*\)"
    r"\s*\(\s*(?P<args>[^)]*)\)\s*;",
)


def _strip_comments(text: str) -> str:
    return _COMMENT_RE.sub(" ", text)


def _parse_enum_body(body: str) -> Dict[str, int]:
    members: Dict[str, int] = {}
    next_value = 0
    for raw_entry in body.split(","):
        entry = raw_entry.strip()
        if not entry:
            continue
        if "=" in entry:
            name, expr = entry.split("=", 1)
            name = name.strip()
            expr = expr.strip()
            try:
                value = eval(expr, {"__builtins__": {}}, dict(members))  # noqa: S307
            except Exception:
                warnings.warn(
                    f"cheader_bindings: could not evaluate enum expression "
                    f"'{expr}' for member '{name}'; using auto-increment.",
                    stacklevel=2,
                )
                value = next_value
        else:
            name = entry
            value = next_value
        members[name] = value
        next_value = value + 1
    return members


def _parse_funcptr_args(args: str) -> List[str]:
    args = args.strip()
    if args == "" or args == "void":
        return []
    return [a.strip() for a in args.split(",")]


class _ParsedHeader:
    __slots__ = ("enums", "funcptrs")

    def __init__(self, enums: Dict[str, Dict[str, int]],
                 funcptrs: Dict[str, Tuple[str, List[str]]]):
        self.enums = enums
        self.funcptrs = funcptrs


def _parse_header_text(header_path: Path) -> _ParsedHeader:
    text = header_path.read_bytes().decode("utf-8", errors="replace")
    clean = _strip_comments(text)

    enums: Dict[str, Dict[str, int]] = {}
    for match in _ENUM_RE.finditer(clean):
        enums[match.group("name")] = _parse_enum_body(match.group("body"))

    funcptrs: Dict[str, Tuple[str, List[str]]] = {}
    for match in _FUNCPTR_RE.finditer(clean):
        ret = match.group("ret").strip()
        name = match.group("name")
        args = _parse_funcptr_args(match.group("args"))
        funcptrs[name] = (ret, args)

    return _ParsedHeader(enums, funcptrs)

# ---------------------------------------------------------------------------
# Build the Python-facing namespace class from parsed data
# ---------------------------------------------------------------------------

def _build_namespace(parsed: _ParsedHeader, class_name: str = "HeaderDefs") -> type:
    enum_classes: Dict[str, type] = {
        name: enum.IntEnum(name, members)
        for name, members in parsed.enums.items()
    }

    funcptr_types: Dict[str, type] = {}
    for name, (ret_str, arg_strs) in parsed.funcptrs.items():
        ret_ctype = _resolve_ctype(ret_str, parsed.enums)
        arg_ctypes = [_resolve_ctype(_strip_param_name(a), parsed.enums) for a in arg_strs]
        funcptr_types[name] = ctypes.CFUNCTYPE(ret_ctype, *arg_ctypes)

    namespace = {**enum_classes, **funcptr_types, "__slots__": ()}
    return type(class_name, (object,), namespace)

_header_path = locate_header()
_parsed = _parse_header_text(_header_path)
HeaderDefs = _build_namespace(_parsed)

if __name__ == "__main__":
    print(f"Parsed header: {_header_path}")
    print("Enums:")
    for ename, ecls in _parsed.enums.items():
        members = ", ".join(f"{m}={v}" for m, v in ecls.items())
        print(f"  {ename}: {members}")
    print("Function pointer typedefs:")
    for fname, (ret, args) in _parsed.funcptrs.items():
        print(f"  {fname}: {ret} (*)({', '.join(args) or 'void'})")
