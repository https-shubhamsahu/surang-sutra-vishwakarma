import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from schgen import check_saved
p = check_saved(sys.argv[1], sys.argv[2])
print(os.path.basename(sys.argv[2]), 'netlist vs design intent:', 'OK' if not p else p)
if p:
    raise SystemExit(1)
