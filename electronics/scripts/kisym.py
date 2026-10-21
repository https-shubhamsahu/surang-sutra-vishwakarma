"""Minimal KiCad S-expression helpers: tokenise/parse, extract + flatten library symbols, pin geometry."""
import re, os

LIBDIR = "/usr/share/kicad/symbols"

def tokenize(s):
    i, n = 0, len(s)
    out = []
    while i < n:
        c = s[i]
        if c in ' \t\r\n':
            i += 1
        elif c == '(' or c == ')':
            out.append(c); i += 1
        elif c == '"':
            j = i + 1; buf = []
            while s[j] != '"':
                if s[j] == '\\':
                    buf.append(s[j:j+2]); j += 2
                else:
                    buf.append(s[j]); j += 1
            out.append(('S', ''.join(buf))); i = j + 1
        else:
            j = i
            while j < n and s[j] not in ' \t\r\n()':
                j += 1
            out.append(s[i:j]); i = j
    return out

def parse(s):
    toks = tokenize(s)
    stack = [[]]
    for t in toks:
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t)
    return stack[0]

def q(x):
    return '"' + x.replace('\\', '\\\\').replace('"', '\\"') + '"' if not x.startswith('"') else x

def dump(node, ind=0):
    if isinstance(node, tuple):
        return '"' + node[1] + '"'   # keep escapes as read
    if isinstance(node, str):
        return node
    parts = [dump(c, ind + 1) for c in node]
    simple = all(not isinstance(c, list) for c in node)
    if simple:
        return '(' + ' '.join(parts) + ')'
    out = '(' + parts[0]
    for c, p in zip(node[1:], parts[1:]):
        if isinstance(c, list):
            out += '\n' + '\t' * (ind + 1) + p
        else:
            out += ' ' + p
    return out + ')'

def val(x):
    return x[1] if isinstance(x, tuple) else x

def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

def find1(node, key):
    r = find(node, key)
    return r[0] if r else None

_libcache = {}
def load_lib(lib):
    if lib not in _libcache:
        path = lib if lib.endswith('.kicad_sym') else os.path.join(LIBDIR, lib + '.kicad_sym')
        tree = parse(open(path).read())[0]
        syms = {val(c[1]): c for c in find(tree, 'symbol')}
        _libcache[lib] = syms
    return _libcache[lib]

def flatten(lib, name):
    """Return a flattened symbol node (no 'extends'), named lib:name, sub-units renamed."""
    import copy
    syms = load_lib(lib)
    node = copy.deepcopy(syms[name])
    ext = find1(node, 'extends')
    if ext:
        parent = flatten(lib, val(ext[1]))  # already named lib:parent
        pname = val(ext[1])
        # take parent's body, override properties from child
        newnode = ['symbol', ('S', f'{lib}:{name}')]
        child_props = {val(p[1]): p for p in find(node, 'property')}
        for c in parent[2:]:
            if isinstance(c, list) and c[0] == 'property':
                k = val(c[1])
                newnode.append(child_props.pop(k, c))
            elif isinstance(c, list) and c[0] == 'symbol':
                sub = copy.deepcopy(c)
                sub[1] = ('S', val(sub[1]).replace(pname, name, 1))
                newnode.append(sub)
            else:
                newnode.append(c)
        # extra child props
        idx = max(i for i, c in enumerate(newnode) if isinstance(c, list) and c[0] == 'property')
        for p in child_props.values():
            idx += 1; newnode.insert(idx, p)
        return newnode
    node[1] = ('S', f'{lib}:{name}')
    return node

def pins(symnode):
    """list of dicts: number, name, type, x, y, angle, length, unit, hidden"""
    out = []
    for sub in find(symnode, 'symbol'):
        sname = val(sub[1])
        m = re.search(r'_(\d+)_(\d+)$', sname)
        unit = int(m.group(1)) if m else 1
        for p in find(sub, 'pin'):
            at = find1(p, 'at'); ln = find1(p, 'length')
            nm = find1(p, 'name'); nu = find1(p, 'number')
            hide = find1(p, 'hide')
            out.append(dict(type=p[1], number=val(nu[1]), name=val(nm[1]), x=float(at[1]), y=float(at[2]),
                            angle=int(float(at[3])) if len(at) > 3 else 0, length=float(ln[1]), unit=unit,
                            hidden=bool(hide and 'yes' in hide) or ('hide' in p)))
    return out

def is_power(symnode):
    return find1(symnode, 'power') is not None
