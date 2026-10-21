#!/bin/bash
# Regenerate both schematics, run ERC, export PDF/SVG/PNG, netlists and the KiCad BOM.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
EL="$HERE/.."
K="$EL/kicad/surang-sutra"
X="$EL/exports"
mkdir -p "$X"
python3 "$HERE/project_files.py"
python3 "$HERE/build_puck.py"
python3 "$HERE/build_avionics.py"
cd "$K"
for n in sutra-puck surang-avionics; do
  short=${n#sutra-}; short=${short#surang-}
  kicad-cli sch erc --severity-all -o "$EL/erc-$short.rpt" "$n.kicad_sch"
  kicad-cli sch erc --severity-all --format json -o "$EL/erc-$short.json" "$n.kicad_sch"
  kicad-cli sch export pdf -o "$X/$n.pdf" "$n.kicad_sch"
  kicad-cli sch export svg -o "$X" "$n.kicad_sch"
  kicad-cli sch export netlist -o "$X/$n.net" "$n.kicad_sch"
  python3 "$HERE/check_netlist.py" "$HERE/${short}_intent.pkl" "$X/$n.net"
done
kicad-cli sch export bom -o "$X/sutra-puck-bom-kicad.csv" \
  --fields 'Reference,Value,MPN,Footprint,${QUANTITY},${DNP}' --labels 'Refs,Value,MPN,Footprint,Qty,DNP' \
  --group-by 'Value,MPN,Footprint,${DNP}' --ref-range-delimiter '' sutra-puck.kicad_sch
kicad-cli sch export bom -o "$X/surang-avionics-bom-kicad.csv" \
  --fields 'Reference,Value,MPN,Footprint,${QUANTITY},${DNP}' --labels 'Refs,Value,MPN,Footprint,Qty,DNP' \
  --group-by 'Value,MPN,Footprint,${DNP}' --ref-range-delimiter '' surang-avionics.kicad_sch
python3 "$HERE/deck_render.py"
echo "exports done"
