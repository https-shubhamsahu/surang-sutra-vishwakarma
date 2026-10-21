# SURANG-SUTRA: Stage 2 design files

**Vishwakarma Awards 2026-27 · Application ID VK26-AU-PAI-0065**
Theme 7: Physical AI for Resilience & Inclusion · Sub-theme: Autonomous Search, Rescue & Tactical Robotics
Team Palanteen · Thakur Shyamnarayan Engineering College (TSEC), Mumbai

SURANG is a collision-tolerant scout. An X-quad sits inside a single-axis rotating geodesic cage, so it rolls on a sound floor and flies over debris or water. SUTRA is a cassette of five communication-only relay pucks. The scout drops one before each bend, so the operator link survives through a dark, GPS-denied gallery.

**Status: Stage 2 design.** No hardware has been built or measured yet. Every number in these files is a target or a calculation. Testing is limited to gas-free mock galleries; the design is not intrinsically safe and not DGMS / ATEX / IECEx certified.

| Folder | Contents |
|---|---|
| `DESIGN-BASELINE.md` | Single source of truth for the dimensions and parts |
| `cad/` | FreeCAD 1.1 parametric model (`.FCStd`), build scripts, STEP / STL exports, mass properties |
| `renders/` | Assembly, exploded and section renders |
| `fea/` | Cage space-frame FEA, arm and axle checks, convergence study, flight-budget calculations (Python) |
| `electronics/` | KiCad 10 schematics (SUTRA puck PCB, SURANG avionics interconnect), ERC reports, pin map, power budget, BOM |

AI tools assisted with the CAD scripting, the analysis code and the renders; visuals made that way are labelled "AI Generated" in our Stage 2 deck. The design decisions, review and fabrication are the team's.
