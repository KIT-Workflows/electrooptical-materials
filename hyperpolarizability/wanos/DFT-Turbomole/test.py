import numpy as np
import yaml, re

DISP_DICT = {
    'None': 'off',
    'D2': 'old',
    'D3': 'on',
    'D3-BJ': 'bj',
    'D4': 'd4'
}

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
        'scf iter': 200,
        'max scf iter': wano_file['DFT options']['Max SCF iterations'],
        'use ri': wano_file['DFT options']['Use RI'],
        'ricore': wano_file['DFT options']['Memory for RI'],
        'functional': wano_file['DFT options']['Functional'],
        'grid size': wano_file['DFT options']['Integration grid'],
        'disp': DISP_DICT[wano_file['DFT options']['vdW correction']],
        'cosmo': wano_file['DFT options']['COSMO calculation'],
        'epsilon': wano_file['DFT options']['Rel permittivity'],
        'opt': wano_file['Type of calculation']['Structure optimisation'],
        'opt cyc': 100,
        'max opt cyc': wano_file['Type of calculation']['Max optimization cycles'],
        'hyperpol': wano_file['Type of calculation']['Hyperpolarizability'],
        'plt_orbts': wano_file['Type of calculation']['Plot Homo-Lumo Orbt'],
        'freq_hyper': [a_dict["frequency (nm)"] for a_dict in wano_file['Type of calculation']["First hyperpolarizability"]],
        'freq': wano_file['Type of calculation']['Frequency calculation'],
        'tddft': wano_file['Type of calculation']['Excited states calculation'],
        'exc state type': wano_file['Type of calculation']['TDDFT options']['Type of excited states'],
        'num exc states': wano_file['Type of calculation']['TDDFT options']['Number of excited states'],
        'opt exc state': wano_file['Type of calculation']['TDDFT options']['Optimised state']
    }
    return settings

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



settings = get_settings_from_rendered_wano()
results_dict = {'title': settings['title'], 'energy_unit': 'Hartree'}  


gather_results(results_dict, settings)

print(results_dict)