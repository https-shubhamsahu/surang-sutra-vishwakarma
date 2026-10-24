"""SURANG-SUTRA key design parameters (mm). Single Python source for build_surang.py and
analysis_clearance.py; build_surang.py copies these into the 'Params' spreadsheet of
SURANG-SUTRA.FCStd and binds the model to them with expressions.

Every value is a design TARGET from DESIGN-BASELINE.md (or a layout choice made in CAD),
never a measurement.
"""
P = dict(
    # --- geodesic cage (2V icosahedral, vertex on +/-Y poles)
    cage_R=290.0,          # hub-centre sphere radius (Ø580)
    cage_phase=18.0,       # roll angle of the cage about Y used for the model (rest pose: two equator hubs down)
    strut_d=3.0,           # pultruded GFRP rod
    hub_d=18.0, hub_h=12.0,  # printed PA12 hub, axis radial
    cap_h=4.0,             # TPU 95A dome on the hub's outer face
    socket_depth=7.0,      # rod socket depth into the hub side wall
    pole_hub_d=32.0, pole_hub_h=20.0, pole_cap_h=5.0,
    bearing_od=19.0, bearing_id=10.0, bearing_w=5.0,   # 6800-2RS
    # --- axle
    axle_od=10.0, axle_id=8.0, axle_clamp_y=40.0,
    # --- inner 7-inch X frame
    frame_diag=295.0, arm_w=25.0, arm_t=5.0, arm_root=22.0,
    plate_t=2.0, plate_w=100.0,
    plate_bot_z=-16.0,     # underside of the bottom sandwich plate (axle centreline is z = 0)
    deck_z=10.0,           # underside of the avionics deck plate
    deck_l=86.0, deck_w=56.0,
    # --- propulsion
    motor_d=34.0, motor_h=20.0,
    prop_d=177.8,          # 7.0 in
    prop_hub_h=8.0,
    prop_blade_half_t=3.0,  # +/- envelope of blade thickness/pitch about the rotor plane
    # --- core
    batt_l=140.0, batt_w=43.0, batt_h=38.0,
    batt_x=0.0,            # overwritten by the CG balance step in build_surang.py
    # --- SUTRA puck + cassette
    puck_d=56.0, puck_h=20.0, puck_shell_d=52.0, n_pucks=5,
    tube_wall=1.2, tube_clear=1.0,
    cassette_y=54.0,       # cassette axis offset along +Y (axle direction); see README, puck exit
    cassette_top_z=-23.0,
    cassette_len=105.0,
)
# derived
P['prop_z'] = P['plate_bot_z'] + P['plate_t'] + P['arm_t'] + P['motor_h'] + P['prop_hub_h'] / 2  # rotor plane
P['cassette_exit_z'] = P['cassette_top_z'] - P['cassette_len']
