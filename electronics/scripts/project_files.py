"""Write KiCad project files (kicad_pro, project lib tables, custom symbol lib)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import custom_symbols as cs

OUT = os.path.join(os.path.dirname(__file__), '..', 'kicad', 'surang-sutra')
SYMLIBS = ['Device', 'power', 'Connector', 'Connector_Generic', 'Battery_Management', 'Regulator_Linear', 'RF_Module',
           'Switch', 'Power_Protection', 'Motor', 'Transistor_FET', 'Diode']
FPLIBS = ['Resistor_SMD', 'Capacitor_SMD', 'Capacitor_THT', 'LED_SMD', 'LED_THT', 'Connector_USB', 'Connector_JST', 'Connector_Coaxial',
          'Connector_Wire', 'Connector_AMASS', 'Connector_PinHeader_2.54mm', 'RF_Module', 'Package_TO_SOT_SMD', 'Button_Switch_SMD',
          'TestPoint', 'Fuse', 'Diode_SMD', 'Module']


def main():
    os.makedirs(OUT, exist_ok=True)
    cs.write_lib(os.path.join(OUT, 'surang-sutra.kicad_sym'))
    rows = ''.join(f'\t(lib (name "{n}")(type "KiCad")(uri "/usr/share/kicad/symbols/{n}.kicad_sym")(options "")(descr ""))\n'
                   for n in SYMLIBS)
    rows += '\t(lib (name "surang-sutra")(type "KiCad")(uri "${KIPRJMOD}/surang-sutra.kicad_sym")(options "")(descr "SURANG-SUTRA custom symbols"))\n'
    open(os.path.join(OUT, 'sym-lib-table'), 'w').write(f'(sym_lib_table\n\t(version 7)\n{rows})\n')
    rows = ''.join(f'\t(lib (name "{n}")(type "KiCad")(uri "/usr/share/kicad/footprints/{n}.pretty")(options "")(descr ""))\n'
                   for n in FPLIBS)
    open(os.path.join(OUT, 'fp-lib-table'), 'w').write(f'(fp_lib_table\n\t(version 7)\n{rows})\n')
    for name in ('sutra-puck', 'surang-avionics'):
        pro = {
            "meta": {"filename": f"{name}.kicad_pro", "version": 3},
            "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
            "erc": {"erc_exclusions": [], "meta": {"version": 0}, "pin_map": [], "rule_severities": {}},
            "sheets": [], "text_variables": {}, "boards": [], "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        }
        open(os.path.join(OUT, f'{name}.kicad_pro'), 'w').write(json.dumps(pro, indent=2))


if __name__ == '__main__':
    main()
