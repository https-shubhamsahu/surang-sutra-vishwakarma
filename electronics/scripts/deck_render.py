"""Recolour the KiCad SVG exports to the deck palette and render large PNGs."""
import re, os, subprocess
X = os.path.join(os.path.dirname(__file__), '..', 'exports')
MAP = {'F5F4EF': 'FFFFFF', 'FFFFC2': 'F8FAFC', '840000': '0F172A', 'A90000': '475569', '006464': '475569',
       '009600': '1D4ED8', '0000C2': '0F172A', '000084': '1D4ED8', 'DC090D': 'DC2626', '0F0F0F': '15803D'}
for name, width in [('sutra-puck', 4800), ('surang-avionics', 7000)]:
    svg = open(os.path.join(X, f'{name}.svg')).read()
    for a, b in MAP.items():
        svg = re.sub('#' + a, '#' + b, svg, flags=re.I)
    out = os.path.join(X, f'{name}-deck.svg')
    open(out, 'w').write(svg)
    png = os.path.join(X, f'{name}-deck.png')
    subprocess.run(['rsvg-convert', '-w', str(width), '-b', 'white', out, '-o', png], check=True)
    print('rendered', png)
