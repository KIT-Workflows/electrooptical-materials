import os
import re
import yaml
import ase.io
import numpy as np
from pymatgen.io import xyz
from pymatgen.io.gaussian import GaussianInput
import turbomole_functions as tm
from hyperpol_tensors import hyper_main



################################################################
###                                                          ###
### prerequisite files: rendered_wano.yml, initial_structure ###
###                                                          ###
################################################################

DISP_DICT = {
    'None': 'off',
    'D2': 'old',
    'D3': 'on',
    'D3-BJ': 'bj',
    'D4': 'd4'
}


def extract_number(filename: str) -> int:
    """
    Extracts a number from the given filename following the pattern '(number)_real.cub'.
    Returns the extracted integer or None if not found.
    """
    match = re.search(r'(\d+)_real\.cub', filename)
    return int(match.group(1)) if match else None


def update_dict_incrementally(file_path: str, results_dict: dict, key: str) -> None:
    """
    Updates the given dictionary (`results_dict`) by reading the contents of the file at `file_path`
    and storing them as a string under `results_dict[key]`.
    """
    results_dict[key] = ""
    with open(file_path, 'r') as file:
        for line in file:
            results_dict[key] += line


def find_cub_files() -> list:
    """
    Finds all files in the current directory that match the '_real.cub' suffix.
    Expects exactly two such files to be present and returns a list of their filenames.
    Raises a ValueError if a different number of matching files is found.
    """
    cub_files = [f for f in os.listdir('.') if f.endswith('_real.cub')]
    if len(cub_files) != 2:
        raise ValueError("There should be exactly two '.cub' files in the current directory.")
    return cub_files


def process_cub_files(results_dict: dict) -> None:
    """
    Processes HOMO and LUMO cube files found in the current directory. Identifies the correct
    files as HOMO or LUMO based on their filenames and updates the `results_dict` with their contents.
    """
    # Find the .cub files
    file1_path, file2_path = find_cub_files()

    # Extract numbers from filenames
    file1_number = extract_number(file1_path)
    file2_number = extract_number(file2_path)

    # Determine which file is HOMO and which is LUMO based on the extracted numbers
    if file1_number is not None and file2_number is not None:
        if file1_number < file2_number:
            homo_file_path = file1_path
            lumo_file_path = file2_path
        else:
            homo_file_path = file2_path
            lumo_file_path = file1_path
    else:
        raise ValueError("Couldn't extract numbers from the HOMO/LUMO filenames.")

    # Update the dictionary incrementally with HOMO and LUMO file contents
    update_dict_incrementally(homo_file_path, results_dict, "homo-orb")
    update_dict_incrementally(lumo_file_path, results_dict, "lumo-orb")


def get_settings_from_rendered_wano(filename: str = 'rendered_wano.yml') -> dict:
    """
    Reads and parses the YAML configuration file `rendered_wano.yml` to retrieve settings.
    Returns a dictionary containing the settings needed for subsequent computations.
    """
    with open(filename) as infile:
        wano_file = yaml.full_load(infile)

    settings = {
        'title': wano_file['Title'],
        'follow-up': wano_file['Follow-up calculation'],
        'structure file type': wano_file['Molecular structure']['Structure file type'],
        'int coord': wano_file['Molecular structure']['Internal coordinates'],
        'basis set': wano_file['Basis set']['Basis set type'],
        'use old mos': wano_file['Initial guess']['Use old orbitals'],
        'charge from file': wano_file['Initial guess']['G1']['Use charge and multiplicity from input file'],
        'charge': wano_file['Initial guess']['G1']['Charge'],
        'multiplicity': wano_file['Initial guess']['G1']['Multiplicity'],
        'scf iter': 500,
        'max scf iter': wano_file['DFT options']['Max SCF iterations'],
        'use ri': wano_file['DFT options']['Use RI'],
        'ricore': wano_file['DFT options']['Memory for RI'],
        'functional': wano_file['DFT options']['Functional'],
        'grid size': wano_file['DFT options']['Integration grid'],
        'disp': DISP_DICT[wano_file['DFT options']['vdW correction']],
        'cosmo': wano_file['DFT options']['COSMO calculation'],
        'epsilon': wano_file['DFT options']['Rel permittivity'],
        'opt': wano_file['Type of calculation']['Structure optimisation'],
        'opt cyc': 300,
        'max opt cyc': wano_file['Type of calculation']['Max optimization cycles'],
        'hyperpol': wano_file['Type of calculation']['Hyperpolarizability'],
        'plt_orbts': wano_file['Type of calculation']['Plot Homo-Lumo Orbt'],
        'freq_hyper': [a_dict["frequency (nm)"] for a_dict in wano_file['Type of calculation']["First hyperpolarizability"]],
        'freq': wano_file['Type of calculation']['Frequency calculation'],
        'tddft': wano_file['Type of calculation']['Excited states calculation'],
        'mp2': wano_file['Type of calculation']['MP2'],
        'exc state type': wano_file['Type of calculation']['TDDFT options']['Type of excited states'],
        'num exc states': wano_file['Type of calculation']['TDDFT options']['Number of excited states'],
        'opt exc state': wano_file['Type of calculation']['TDDFT options']['Optimised state']
    }
    return settings


def sanitize_multiplicity(multiplicity: int, n_el: int) -> int:
    """
    Ensures the provided multiplicity is valid for the number of electrons `n_el`.
    If the multiplicity is not physically possible, it is adjusted to the nearest valid value.
    If an adjustment is made, the `rendered_wano.yml` file is updated accordingly.
    """
    multi_min = n_el % 2 + 1

    if multiplicity < 1:
        print(f'Attention: a multiplicity of {multiplicity} is not possible.')
    elif n_el % 2 and multiplicity % 2:
        print(f'Attention: a multiplicity of {multiplicity} is not possible for an odd number of electrons.')
        multiplicity -= 1
    elif not n_el % 2 and not multiplicity % 2:
        print(f'Attention: a multiplicity of {multiplicity} is not possible for an even number of electrons.')
        multiplicity -= 1

    corrected_multiplicity = max(multiplicity, multi_min)
    if corrected_multiplicity != multiplicity:
        print(f'The multiplicity was set to {corrected_multiplicity} by default.')
        with open('rendered_wano.yml') as infile:
            wano_file = yaml.full_load(infile)
        wano_file['Initial guess']['Multiplicity'] = int(corrected_multiplicity)
        with open('rendered_wano.yml', 'w') as outfile:
            yaml.dump(wano_file, outfile)

    return corrected_multiplicity


def main() -> None:
    """
    Main workflow function for the script.
    Reads settings from 'rendered_wano.yml', prepares files, runs TURBOMOLE calculations,
    and gathers results into 'turbomole_results.yml'.
    """
    coord_file = 'coord_0'
    settings = get_settings_from_rendered_wano()
    # --- drop any DFT functional for pure MP2 jobs -------------
    if settings.get("mp2"):
        settings["functional"] = "None"

    # Properties are stored in results_dict
    results_dict = {'title': settings['title'], 'energy_unit': 'Hartree'}

    if settings['follow-up']:
        os.system('mkdir old_results; tar -xf old_calc.tar.xz -C old_results')
        os.system(f'cp old_results/coord {coord_file}')
        old_settings = get_settings_from_rendered_wano(filename='old_results/rendered_wano.yml')
        settings['title'] = old_settings['title']
        if settings['use old mos']:
            settings['multiplicity'] = old_settings['multiplicity']
    else:
        old_settings = None
        handle_structure_file(settings, coord_file)

    if not settings['use old mos']:
        if settings['charge from file'] and settings['structure file type'] == 'Gaussian input':
            ginp = GaussianInput.from_file('initial_structure')
            settings['charge'], settings['multiplicity'] = ginp.charge, ginp.spin_multiplicity
        else:
            n_el = sum(ase.io.read(coord_file).numbers) - settings['charge']
            settings['multiplicity'] = sanitize_multiplicity(settings['multiplicity'], n_el)

    tm.input_preparation('define', tm.make_define_string(settings, coord_file))
    if settings['follow-up']:
        os.system('rm -rf old_results')

    prepare_cosmo(settings, old_settings)
    handle_tddft(settings)
    handle_mp2_settings(settings)

    tm.single_point_calculation(settings)

    handle_hyperpol(settings, results_dict)
    handle_orbitals(settings, results_dict)

    if settings['opt']:
        tm.jobex(settings)

    if settings['freq']:
        handle_frequency(settings, results_dict)

    gather_results(results_dict, settings)
    write_output_files(results_dict)
    prepare_output_files()


def handle_structure_file(settings: dict, coord_file: str) -> None:
    """
    Handles the preparation of the coordinate file from the initial structure, depending on the input structure file type.
    """
    if settings['structure file type'] == 'Turbomole coord':
        os.rename('initial_structure', coord_file)
    else:
        if settings['structure file type'] == 'Gaussian input':
            ginp = GaussianInput.from_file('initial_structure')
            xyz.XYZ(ginp.molecule).write_file('initial_structure')
        os.system(f'x2t initial_structure > {coord_file}')


def prepare_cosmo(settings: dict, old_settings: dict = None) -> None:
    """
    Prepares and runs the COSMO calculations if requested. If this is a follow-up calculation
    and old COSMO settings are found, updates them accordingly.
    """
    if settings['cosmo']:
        if settings['follow-up'] and old_settings:
            if old_settings['cosmo']:
                tm.input_preparation('cosmoprep', f'u\n{settings["epsilon"]}\n\n\n\n\n\n\n\n\n\n\n*\n\n\n')
            else:
                tm.input_preparation('cosmoprep', f'{settings["epsilon"]}\n\n\n\n\n\n\n\n\n\n\nr all b\n*\n\n\n')
        else:
            tm.input_preparation('cosmoprep', f'{settings["epsilon"]}\n\n\n\n\n\n\n\n\n\n\nr all b\n*\n\n\n')
    elif settings['follow-up'] and old_settings and old_settings['cosmo']:
        for datagroup in ['cosmo', 'cosmo_atoms', 'cosmo_out']:
            os.system(f'kdg {datagroup}')


def handle_tddft(settings: dict) -> None:
    """
    Handles TDDFT-related settings. If excited-state optimization with COSMO is requested,
    it prints a message stating it is not implemented and skips optimization.
    """
    if settings['tddft'] and settings['opt']:
        if not settings['cosmo']:
            os.system(f'adg exopt {settings["opt exc state"]}')
        else:
            print("Excited state optimisations with COSMO not yet implemented in TURBOMOLE's egrad. \
                  A single-point calculation is performed instead.")
            settings['opt'] = False

def handle_mp2_settings(settings: dict) -> None:
    """
    • Remove any obsolete $dft section (MP2 must start from HF, not DFT)
    • Add a valid $ricc2 section *above the final $end*.
    • Ensure $denconv is present for SCF convergence.
    """
    if not settings.get("mp2"):
        return                                    # not an MP2 job → leave

    # 1. read control once
    with open("control", "r") as fh:
        lines = fh.readlines()

    # 2. delete *all* $dft … $end blocks
    clean = []
    skip = False
    for ln in lines:
        tag = ln.strip().lower()
        if tag.startswith("$dft"):
            skip = True
            continue
        if skip and tag.startswith("$end"):
            skip = False
            continue
        if not skip:
            clean.append(ln)
    lines = clean

    # 3. quit if a $ricc2 block is already there
    if any("$ricc2" in ln.lower() for ln in lines):
        # but still check $denconv!
        if not any("$denconv" in ln.lower() for ln in lines):
            try:
                end_idx = max(i for i, ln in enumerate(lines)
                            if ln.strip().lower() == "$end")
            except ValueError:
                end_idx = len(lines)
            lines.insert(end_idx, "$denconv    1d-7\n")
            with open("control", "w") as fh:
                fh.writelines(lines)
        return

    # 4. locate the *final* $end
    try:
        end_idx = max(i for i, ln in enumerate(lines)
                      if ln.strip().lower() == "$end")
    except ValueError:
        end_idx = len(lines)                   # none found → append at EOF

    # 5. insert $denconv if not present already
    if not any("$denconv" in ln.lower() for ln in lines):
        lines.insert(end_idx, "$denconv    1d-7\n")

    # 6. build $ricc2 block
    block = ["$ricc2\n"]
    if settings.get("opt"):
        block.append("mp2 geoopt model=mp2\n")
    else:
        block.append("mp2\n")

    # insert before the final $end
    lines[end_idx:end_idx] = block

    # 7. rewrite control
    with open("control", "w") as fh:
        fh.writelines(lines)


def handle_hyperpol(settings: dict, results_dict: dict) -> None:
    """
    Handles hyperpolarizability calculations if requested.
    Updates the control file with required settings and retrieves the results.
    """
    if settings['hyperpol'] and os.path.exists('control'):
        with open("control", "r") as in_file:
            buf = in_file.readlines()

        with open("control", "w") as out_file:
            for line in buf:
                if line.strip("\n") != "$end":
                    out_file.write(line)
            out_file.write("$scfinstab hyperpol nm\n")

            # If the first frequency is not zero, we insert a placeholder value (like 45560000000.0)
            # This placeholder is likely specific to the domain logic for calculations.
            if settings['freq_hyper'][0] != 0:
                settings['freq_hyper'].insert(0, 45560000000.0)

            for freq_h in settings['freq_hyper']:
                if freq_h != 0:
                    out_file.write(f'{freq_h}\n')
            out_file.write("$end")

        tm.hyper_polarizability_calculation()

        #beta = tm.get_hyper_polarizability_2nd_pair().tolist()
        dipole = tm.get_dipole_moment().tolist()

        results_dict['dipole'] = dipole
        #results_dict['beta(10E-30 esu)'] = beta
        
        results_dict['1st beta zzz (10E-30 esu)'] = float(hyper_main(pair_number=1))
        results_dict['2nd beta zzz (10E-30 esu)'] = float(hyper_main(pair_number=2))
        results_dict['3rd beta zzz (10E-30 esu)'] = float(hyper_main(pair_number=3))


# def handle_orbitals(settings: dict, results_dict: dict) -> None:
#     """
#     Handles orbital plot generation if requested.
#     Updates 'control' to request HOMO and LUMO orbitals.
#     """
#     if settings['plt_orbts'] and os.path.exists('control'):
#         tm.plot_homo_lumo_orbitals()
#         homo_l, lumo_l = tm.homo_lumo_numbers_from_orbitals('eiger.out', 'HOMO-LUMO Separation')

#         with open("control", "r") as f:
#             lines = f.readlines()
#         with open("control", "w") as f:
#             for line in lines:
#                 if line.strip("\n") != "$rij":
#                     f.write(line)
#                 else:
#                     f.write('$rij\n')
#                     f.write('$pointvalper fmt=cub\n')
#                     f.write('orbs 2\n')
#                     f.write(f'k 1 1 1 a {homo_l}\n')
#                     f.write(f'k 1 1 1 a {lumo_l}\n')

#         tm.plot_homo_lumo_orbitals()
#         #process_cub_files(results_dict)

def handle_orbitals(settings: dict, results_dict: dict) -> None:
    """Generate .cub files for HOMO‑1, HOMO, LUMO and LUMO+1 if requested.

    Workflow
    --------
    1. Ensure up‑to‑date MO information by running *riper* once.
    2. Rewrite *control* so that *pointval* exports the four orbitals.
    3. Run *riper* again – this time .cub files are written.
    """
    if settings.get("plt_orbts") and os.path.exists("control"):
        # Step 1 – make sure orbital information is present
        tm.plot_homo_lumo_orbitals()

        homo, lumo = tm.homo_lumo_numbers_from_orbitals(
            "eiger.out", "HOMO-LUMO Separation"
        )
        orbitals = [homo - 1, homo, lumo, lumo + 1]

        # Step 2 – amend *control*
        with open("control", "r") as f:
            lines = f.readlines()

        with open("control", "w") as f:
            for line in lines:
                if line.rstrip("\n") != "$rij":
                    f.write(line)
                else:
                    f.write("$rij\n")
                    f.write("$pointvalper fmt=cub\n")
                    f.write(f"orbs {len(orbitals)}\n")
                    for orb in orbitals:
                        f.write(f"k 1 1 1 a {orb}\n")

        # Optional: expose indices for downstream use
        results_dict.update(
            {
                "homo_m1": orbitals[0],
                "homo": orbitals[1],
                "lumo": orbitals[2],
                "lumo_p1": orbitals[3],
            }
        )

        # Step 3 – generate the .cub files
        tm.plot_homo_lumo_orbitals()



def handle_frequency(settings: dict, results_dict: dict) -> None:
    """
    Handles vibrational frequency calculations if requested and feasible.
    For ground-state calculations, runs 'aoforce' and retrieves the frequencies and zero-point energy (ZPE).
    For excited states, prints a message stating it's not implemented.
    """
    if settings['tddft']:
        print('Frequency calculations for excited states are not yet implemented.')
        exit(0)
    else:
        tm.run_aoforce()

    vib_freq = []
    with open('aoforce.out') as infile:
        ao_lines = infile.readlines()
    for ao_line in ao_lines:
        if 'frequency  ' in ao_line:
            for freq in ao_line.split()[1:]:
                if 'i' in freq:
                    vib_freq.append(-float(freq.replace('i', '')))
                else:
                    vib_freq.append(float(freq))
        if 'zero point' in ao_line:
            results_dict['ZPE'] = float(ao_line.split()[6])
    results_dict['vibrational frequencies'] = vib_freq


def gather_results(results_dict: dict, settings: dict) -> None:
    """
    Gathers the results of the calculations, including energy, HOMO/LUMO levels, and (if available) excited-state energies.
    Stores these results into `results_dict`.
    """
    # Process 'energy' file
    with open('energy') as infile:
        energy_lines = infile.readlines()
        energy_value = None

        # Try to extract the energy value using the original method
        if len(energy_lines) >= 2:
            try:
                energy_value = float(energy_lines[-2].split()[1])
            except (IndexError, ValueError):
                pass  # Proceed to try regex method

        # If the above method fails, try using regex to find the energy value
        if energy_value is None:
            for line in energy_lines:
                match = re.search(r'(Total energy|Total Energy|E=)\s*=\s*([-+]?\d*\.\d+|\d+)', line)
                if match:
                    energy_value = float(match.group(2))
                    break

        if energy_value is None:
            raise ValueError("The 'energy' file is missing expected data.")

        results_dict['energy'] = energy_value

    # Process 'eiger.out' file
    with open('eiger.out') as infile:
        content = infile.readlines()

    # Initialize variables
    homo_energy = None
    lumo_energy = None
    gap_energy = None

    # Use regex to find HOMO, LUMO, and Gap energies
    for line in content:
        stripped_line = line.strip()
        if stripped_line.startswith('HOMO:'):
            match = re.search(r'HOMO:\s*\d+\.\s*\d+\s*\w+\s*([-+]?\d*\.\d+)', line)
            if match:
                homo_energy = float(match.group(1))
        elif stripped_line.startswith('LUMO:'):
            match = re.search(r'LUMO:\s*\d+\.\s*\d+\s*\w+\s*([-+]?\d*\.\d+)', line)
            if match:
                lumo_energy = float(match.group(1))
        elif stripped_line.startswith('Gap :'):
            match = re.search(r'Gap\s*:\s*([-+]?\d*\.\d+)', line)
            if match:
                gap_energy = float(match.group(1))

    if homo_energy is None or lumo_energy is None or gap_energy is None:
        raise ValueError("The 'eiger.out' file is missing expected HOMO/LUMO data.")

    results_dict['homo'] = homo_energy
    results_dict['lumo'] = lumo_energy
    results_dict['homo-lumo gap'] = gap_energy

    # Process 'exspectrum' file if tddft is True
    if settings.get('tddft'):
        results_dict['exc_type'] = settings.get('exc state type')
        exc_energies = []
        with open('exspectrum') as infile:
            exc_lines = infile.readlines()
        num_exc_states = settings.get('num exc states', 0)
        if num_exc_states > len(exc_lines):
            raise ValueError("The 'exspectrum' file has fewer lines than the number of excitation states requested.")
        relevant_exc_lines = exc_lines[-num_exc_states:]
        for exc_line in relevant_exc_lines:
            parts = exc_line.split()
            if len(parts) < 3:
                raise ValueError("The 'exspectrum' line does not contain valid excitation data.")
            try:
                exc_energy = float(parts[2])
                exc_energies.append(exc_energy)
            except ValueError:
                raise ValueError("Invalid excitation energy value in 'exspectrum' file.")
        results_dict['exc_energies'] = exc_energies


def write_output_files(results_dict: dict) -> None:
    """
    Writes the results dictionary to a YAML file named 'turbomole_results.yml'.
    """
    with open('turbomole_results.yml', 'w') as outfile:
        yaml.dump(results_dict, outfile, default_flow_style=False)


def prepare_output_files() -> None:
    """
    Prepares and packages the output files generated by the TURBOMOLE calculation.
    Creates a 'results.tar.xz' archive containing relevant files and produces a 'final_structure.xyz' from the coordinate file.
    """
    output_files = [
        'alpha', 'auxbasis', 'basis', 'beta', 'control', 'coord', 'energy',
        'forceapprox', 'gradient', 'hessapprox', 'mos', 'optinfo', 'rendered_wano.yml',
        'sing_a', 'trip_a', 'unrs_a', 'eiger.out', 'final_structure.xyz', 'rendered_wano.yml', 
        'turbomole_results.yml', 'job.last', 'exspectrum', 'escf.out', 'escf.out', 'hyperpols',
        'dscf.out','vibspectrum']
    existing_files = [filename for filename in output_files if os.path.isfile(filename)]
    if existing_files:
        os.system(f'tar -cf results.tar.xz {" ".join(existing_files)}')
    else:
        print("No additional output files found to package.")

    if os.path.isfile('coord'):
        os.system('t2x coord > final_structure.xyz')
    else:
        print("Coordinate file 'coord' not found. Cannot create 'final_structure.xyz'.")


if __name__ == '__main__':
    main()