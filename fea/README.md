# SURANG cage FEA (Stage 2)

Structural checks for the SURANG roll-cage, axle, arms and bearings. Every number is a calculation from catalogue properties and stated assumptions. Nothing has been tested yet; the Month 2 pendulum strikes and rod bend tests will check these numbers.

## Method

- **Model:** the full 2V geodesic cage (120 struts, 42 hubs) plus the carbon axle, as 3D beam elements. Each strut is split into 8 elements in the headline runs (980 elements in all).
- **Linear runs** (`linear.py`): unit loads at every hub, load cases at 1 g, 2 g and 10 g, and eigen-buckling.
- **Nonlinear impact runs** (`corot.py`, `nl_cases.py`): a co-rotational large-deflection solver pushes the cage into a rigid wall or floor until the impact energy is absorbed. The TPU caps are contact springs, and soft caps are bilinear.
- **Conservative load:** the whole 2.4 kg lands on one hub. Impact energies are 2.8 J (1.5 m/s, the gallery speed limit), 4.8 J (2 m/s wall strike) and 23.5 J (1 m free fall).
- **Materials:** GFRP rod E = 40 GPa, allowable 400 MPa (half of its 800 MPa strength). Carbon rod E = 125 GPa, allowable 600 MPa. Carbon axle tube E = 100 GPa, allowable 500 MPa.
- **Checks:** mesh convergence (1, 2, 4 and 8 elements per strut), four hub types (equator, 26.6°, 31.7° and 58.3°), axle and bearing hand checks, motor-arm FEA, prop clearance in the deformed cage, and the flight budget.

## Results (`data/summary.json`, `figures/`)

| | Stage 1: 3 mm GFRP, 10/8 axle, solid caps | Selected: 4 mm GFRP, 15/13 axle, 20 mm soft caps |
|---|---|---|
| Energy before allowable stress, equator / weakest hub | 1.7 J / 1.2 J | 5.3 J / 3.6 J |
| 1.5 m/s strike (2.8 J) | over allowable at all 4 hub types | under allowable at all 4 hub types |
| 2 m/s strike (4.8 J) | 2.2–2.8× allowable; struts break | 0.85× at the equator, 1.35× at the weakest hub (breaks above 6.9 J) |
| Axle stress, 2 m/s strike | 332 MPa | 386 MPa (allowable 500); 61802-2RS bearing, s₀ = 4.8 |
| Prop tip to cage, during the strike | 26.8 mm | 31.6 mm (≥ 20 required) |
| 1 m free fall (23.5 J) | struts break | struts break |
| Mass change | 0 | +301 g |

What it means:

- Stiffer rods on their own move the failure into the 10/8 axle (674 MPa), so the axle has to grow as well.
- No variant survives a 1 m fall onto one hub. The motors must never be cut in the air, and the struts are cheap, replaceable parts.
- The selected cage brings the CAD mass from 2.17 to 2.47 kg, so the mass target moves from 2.4 to 2.5 kg. Thrust-to-weight at minimum battery voltage is still 3.2, hover time about 6.5 min, and roll time about 30 min.
- Convergence: linear stress and deflection are the same at every mesh, because beam elements are exact for loads at the nodes. Buckling settles within 0.2 % at 4 elements per strut, and the nonlinear impact energy changes by 5–7 % from 4 to 8 elements per strut.

## Run

```bash
uv venv .venv && uv pip install -p .venv numpy scipy matplotlib scikit-fem
.venv/bin/python run_all.py     # about 12 min on 4 cores; writes data/fea_results.pkl
.venv/bin/python figures.py     # figures/*.png and data/summary.json
```
