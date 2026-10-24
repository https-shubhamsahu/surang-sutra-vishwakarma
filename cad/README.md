# SURANG-SUTRA CAD (Stage 2)

Parametric FreeCAD 1.1 model of the SURANG scout and the SUTRA relay puck. Stage 2 is a design stage: every number here is a design target or a calculation. Nothing has been built, weighed or measured.

## Files

| File | What it is |
|---|---|
| `SURANG-SUTRA.FCStd` | The model. The `Params` spreadsheet drives every dimension; the feature tree is named by part. |
| `step/` | STEP exports: full assembly, cage, 5- and 6-socket hubs, pole hub, frame, cassette, puck |
| `stl/` | Printable parts: hubs, pole hub, TPU caps, puck shell base, lid and bumper |
| `mesh/` | Per-part meshes used by `../renders/render.py` |
| `params.py`, `geodesic.py` | Design parameters and the 2V geodesic cage geometry |
| `build_surang.py` | Builds the whole model headless and writes everything above |
| `analysis_clearance.py` → `analysis.json` | Prop clearance, cage hull, puck exit window, roll-over check |
| `mass_report.py` → `mass-properties.md` | Mass, CG and inertia per part and per subsystem |
| `clearance-internal.json` | Prop-to-part distances and part-to-part overlaps |

Rebuild:

```bash
freecadcmd -c "exec(open('cad/build_surang.py').read())"
python3 cad/analysis_clearance.py && python3 cad/mass_report.py
```

## Key results (calculated)

- **Cage:** 2V icosahedral geodesic, Ø580 mm hub-centre sphere (Ø600 over the TPU caps). 42 hubs, 120 struts in two chord lengths, 158.5 and 179.2 mm. Every face opening has a clear incircle of 91 mm or more.
- **All-up mass:** 2.17 kg against the 2.40 kg cap. The cage (+55 g) and the cassette with 5 pucks (+59 g) are over their allocations; the rest is under. Detail in `mass-properties.md`.
- **Prop clearance:** 32.3 mm from the prop tips to the cage inner hull, and 37.3 mm to the nearest rod or hub at any cage roll angle (target ≥ 20 mm).
- **Centre of gravity:** the hanging core sits 15.7 mm below the axle, so it stays level like a pendulum while the cage rolls.
- **Puck exit:** a drop line through the centre is blocked by the equator strut ring at every cage angle. With the cassette moved to y = +54 mm the Ø56 puck falls through an open face, with 20.4 mm and 13.5 mm of margin at the two floor rest poses.
- **Roll-over:** a 20 mm puck under the resting cage would be struck (18 mm interference), so the scout hops in fly mode after each drop.
- **SUTRA puck:** 34.5 g as drawn (target ≤ 30 g). Thinner walls (1.0 mm) and a 1.0 mm PCB bring it to about 29 g. Its CG is 8.0 mm above the base, so the dome does not self-right; the tag goes on both faces.

## Open items for CAD revision B

`clearance-internal.json` lists four small overlaps to fix before printing:

- Pi 5 board vs the stack standoffs (250 mm³)
- Escapement cam vs the MG90S servo body (30 mm³)
- Capture pin vs the second puck's TPU bumper (7 mm³)
- Nose bracket vs the MLX90640 thermal camera (4 mm³)

The FEA in `../fea/` recommends 4 mm GFRP struts, a 15/13 mm carbon axle and softer TPU caps. Those changes go into revision B as well.
