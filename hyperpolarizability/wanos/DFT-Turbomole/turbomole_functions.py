import os
import glob
import sys
import yaml
import subprocess
import numpy as np
from typing import Tuple


def utf8_enc(var: str) -> bytes:
    """
    Encode the given string in UTF-8 encoding.
    Compatible with Python 2 and 3.
    """
    if sys.version_info >= (3, 0):
        return var.encode('utf-8')
    else:
        return var


def utf8_dec(var: bytes) -> str:
    """
    Decode the given bytes object using UTF-8 encoding.
    Compatible with Python 2 and 3.
    """
    if sys.version_info >= (3, 0):
        return var.decode('utf-8')
    else:
        return var


# def homo_lumo_numbers_from_orbitals(file_name: str, search_string: str) -> tuple:
#     """
#     Searches for the given string in the specified file and returns the HOMO and LUMO orbital numbers.
#     """
#     line_number = 0
#     list_of_results = []
#     with open(file_name, 'r') as read_obj:
#         for line in read_obj:
#             if search_string in line:
#                 list_of_results.append((line_number, line.rstrip()))
#             line_number += 1

#     with open(file_name, 'r') as file:
#         content = file.readlines()

#     homo_line = int(content[list_of_results[0][0] + 1].split()[2])
#     lumo_line = int(content[list_of_results[0][0] + 2].split()[2])

#     return homo_line, lumo_line

def homo_lumo_numbers_from_orbitals(file_name: str, search_string: str) -> Tuple[int, int]:
    """Return the integer indices of the HOMO and LUMO orbitals found in *file_name*.

    The caller can derive neighbouring orbitals (HOMO‑1, LUMO+1, …) from these values.
    """
    line_number = 0
    matches = []
    with open(file_name, "r") as fh:
        for line in fh:
            if search_string in line:
                matches.append((line_number, line.rstrip()))
            line_number += 1

    if not matches:
        raise ValueError(f"'{search_string}' not found in {file_name}")

    with open(file_name, "r") as fh:
        lines = fh.readlines()

    homo = int(lines[matches[0][0] + 1].split()[2])
    lumo = int(lines[matches[0][0] + 2].split()[2])

    return homo, lumo


def make_define_string(settings: dict, coord: str) -> str:
    """
    Creates and returns the 'define' input string for the TURBOMOLE calculation based on the provided settings and coordinate file.
    """
    if settings['use old mos']:
        with open('old_results/rendered_wano.yml') as infile:
            old_settings = yaml.full_load(infile)
        same_basis = old_settings['Basis set']['Basis set type'] == settings['basis set']

    if not (settings['use old mos'] and same_basis):
        define_string = '\n%s\na %s\n' % (settings['title'], coord)
        # Implement symmetry
        if settings['int coord']:
            define_string += 'ired\n*\n'
        else:
            define_string += '*\nno\n'

        define_string += 'b all %s\n*\n' % (settings['basis set'])
        # Add options for basis sets (different for different atoms)

        if not settings['use old mos']:
            define_string += 'eht\n\n'
            define_string += '%i\n' % (settings['charge'])
            # Implement symmetry
            if settings['multiplicity'] < 3:
                define_string += '\n\n\n'
            else:
                define_string += 'n\nu %i\n*\n\n' % (settings['multiplicity'] - 1)
        else:
            define_string += 'use old_results/control\n\n'

        define_string += 'scf\niter\n%i\n\n' % (settings['scf iter'])
        if settings['use ri']:
            define_string += 'ri\non\nm %i\n\n' % (settings['ricore'])
        if settings['functional'] != 'None':
            define_string += 'dft\non\nfunc %s\ngrid %s\n\n' % (
                settings['functional'], settings['grid size']
            )
        if settings['disp'] != 'off':
            define_string += 'dsp\n%s\n\n' % (settings['disp'])

        if settings['tddft']:
            define_string += 'ex\n'
            if settings['multiplicity'] > 1:
                define_string += 'urpa\n*\n'
            else:
                define_string += 'rpa%s\n*\n' % (settings['exc state type'][0].lower())
            define_string += 'a %i\n*\n' % (settings['num exc states'])
            define_string += '*\n\n'
            # Implement symmetry
        define_string += '*\n'

    else:
        output_files = ['alpha', 'auxbasis', 'basis', 'beta', 'control', 'hessapprox', 'mos']
        for filename in output_files:
            if os.path.isfile('old_results/%s' % (filename)):
                os.system('cp old_results/%s .' % (filename))
        os.system('cp coord_0 coord')
        define_string = '\n\n\n\n\n'
        if settings['use ri']:
            define_string += 'ri\non\nm %i\n\n' % (settings['ricore'])
        else:
            define_string += 'ri\noff\n\n'
        if settings['functional'] != 'None':
            define_string += 'dft\non\nfunc %s\ngrid %s\n\n' % (
                settings['functional'], settings['grid size']
            )
        else:
            define_string += 'dft\noff\n\n'
        define_string += 'dsp\n%s\n\n' % (settings['disp'])

        if not settings['tddft']:
            if old_settings['Type of calculation']['Excited states calculation']:
                os.system("sed -i 's/#$max/$max/g' control")
                for dg in ['soes', 'scfinstab', 'rpacor', 'denconv']:
                    os.system('kdg %s' % (dg))

        elif not old_settings['Type of calculation']['Excited states calculation']:
            define_string += 'ex\n'
            if settings['multiplicity'] > 1:
                define_string += 'urpa\n*\n'
            else:
                define_string += 'rpa%s\n*\n' % (settings['exc state type'][0].lower())
            define_string += 'a %i\n*\n' % (settings['num exc states'])
            define_string += '*\n\n'
            # Implement symmetry
        else:
            define_string += 'ex\n'
            if old_settings['Type of calculation']['TDDFT options']['Type of excited states'] != settings['exc state type']:
                if settings['multiplicity'] > 1:
                    define_string += 'urpa\n'
                else:
                    define_string += 'rpa%s\n' % (settings['exc state type'][0].lower())
            define_string += '*\n'
            define_string += 'a %i\n*\n' % (settings['num exc states'])
            define_string += '*\n\n'

        define_string += '*\n'

    return define_string


def input_preparation(program: str, input_string: str) -> None:
    """
    Runs the specified TURBOMOLE program with the given input string.
    Captures output into an .out file and prints errors if they occur.
    """
    outfilename = '%s.out' % program
    process = subprocess.Popen(
        [program], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = process.communicate(input=utf8_enc(input_string))

    with open(outfilename, 'w') as outfile:
        outfile.write(utf8_dec(out))

    if 'normally' not in utf8_dec(err).split():
        print(f'An error occurred when running {program}:')
        with open(outfilename) as infile:
            lines = infile.readlines()
        for line in lines:
            print(line)


def single_point_calculation(settings: dict, tmp: bool = False) -> None:
    """
    Performs a single-point calculation.

    * MP2 + optimisation      → we skip the pre-SCF entirely (jobex will do it)
    * MP2 single-point only   → ridft (RI-HF)  +  ricc2
    * Every other job         → old logic (ridft or dscf)
    """

    # --- skip pre-SCF when jobex will follow -------------------------
    if settings.get("mp2") and settings.get("opt") and not tmp:
        return                                # jobex will start from scratch

    # --- choose the reference code -----------------------------------
    if settings.get("mp2"):                   # MP2 single point
        scf_program = "ridft" if settings["use ri"] else "dscf"
    else:                                     # anything else
        scf_program = "ridft" if settings["use ri"] else "dscf"

    suffix = "_tmp" if tmp else ("_0" if settings["opt"] else "")

    output = scf_program + suffix + '.out'

    num_iter = 0
    done = False
    while not done:
        run_turbomole(scf_program, output)
        os.system('eiger > eiger.out')
        done, err = check_scf(output)
        if not done:
            if err == 'not converged':
                num_iter += settings['scf iter']
                if num_iter > settings['max scf iter']:
                    print(
                        f'SCF not converged in maximum number of iterations ({settings["max scf iter"]})'
                    )
                    sys.exit(0)
            elif err == 'negative HLG':
                print('Attention: negative HOMO-LUMO gap found - please check manually')
                sys.exit(0)

    if settings.get("mp2"):
        ricc2_output = "ricc2" + suffix + ".out"
        run_turbomole("ricc2", ricc2_output)

    if settings['tddft']:
        escf_output = 'escf' + suffix + '.out'
        run_turbomole('escf', escf_output)
        done, err = check_escf(output)
        if not done:
            print('Problem with escf calculation found - please check manually')
            sys.exit(0)

def run_aoforce() -> None:
    """
    Runs a vibrational frequency calculation using the aoforce module.
    """
    run_turbomole('aoforce', 'aoforce.out')



def plot_homo_lumo_orbitals() -> None:
    """
    Runs the riper module (Real-time iper) for visualization of the HOMO-LUMO orbitals.
    """
    run_turbomole('riper -proper', 'riper.out')


def hyper_polarizability_calculation() -> None:
    """
    Runs an excited state calculation using 'escf' for hyperpolarizability calculations.
    """
    run_turbomole('escf', 'escf.out')


def jobex(settings: dict) -> None:
    """
    Performs a geometry optimization using the jobex script from TURBOMOLE.
    SCF and, optionally, excited-state optimizations are configured based on the settings.
    """
    options = ''
    # use  -ri  only for pure DFT/HF jobs — NOT for MP2
    if settings['use ri'] and not settings.get("mp2"):
        options += ' -ri'

    if settings['tddft']:
        options += ' -ex %i' % (settings['opt exc state'])

    # tell jobex to obtain gradients from ricc2 for MP2
    if settings.get("mp2"):
        options += ' -ricc2'

    options += ' -c %i' % (settings['opt cyc'])


    num_cycles = 0
    done = False

    while not done:
        run_turbomole('jobex%s' % (options))
        os.system('eiger > eiger.out')
        done, err = check_opt()

        if not done:
            if err == 'opt not converged':
                num_cycles += settings['opt cyc']
                if num_cycles > settings['max opt cyc']:
                    print(
                        f'Structure optimisation not converged in maximum number of cycles ({settings["max opt cyc"]})'
                    )
                    sys.exit(0)
            elif err.startswith('scf problem'):
                num_cycles += int(err.split()[-1])
                single_point_calculation(settings, tmp=True)
            else:
                print('An error occurred during the structure optimisation - please check manually')
                sys.exit(0)
            # Additional error handling can be implemented here
        elif not settings['tddft']:
            scf_done, err = check_scf('job.last')
            if not scf_done:
                print('The structure optimisations converged but the last SCF run showed an error.')
                sys.exit(0)


# def run_turbomole(command: str, outfile: str = None) -> None:
#     """
#     Runs a TURBOMOLE command with optional output redirection to a specified outfile.
#     If outfile is not provided, it defaults to '<command>.out'.
#     """
#     if outfile is None:
#         outfile = command.split()[0] + '.out'

#     proc_cmd = ['nohup'] + command.split()
#     if not command.startswith('jobex'):
#         proc_cmd += ['>', outfile]

#     with open(outfile, 'w') as tm_out:
#         tm_process = subprocess.Popen(proc_cmd, stdout=tm_out, stderr=subprocess.PIPE)
#         out, err = tm_process.communicate()

#     err_decoded = utf8_dec(err)
#     if 'normally' not in err_decoded.split():
#         print(f'Error while running {command.split()[0]}:')
#         print(err_decoded)
#         sys.exit(0)


def run_turbomole(command: str, outfile: str = None) -> None:
    """
    Runs a TURBOMOLE command with shell=True so we can use nohup and redirection.
    E.g., command='nohup riper -proper > riper.out 2>&1 &'.
    """
    if outfile is None:
        outfile = command.split()[0] + '.out'

    # For shell usage, we must craft the entire string ourselves:
    # If you want to background it:
    #   shell_cmd = f"nohup {command} > {outfile} 2>&1 &"
    #
    # If you want to *wait* for it to finish:
    #   shell_cmd = f"nohup {command} > {outfile} 2>&1"
    #
    # We'll do the synchronous version here:
    shell_cmd = f"nohup {command} > {outfile} 2>&1"

    print(f"Running in shell: {shell_cmd}")
    process = subprocess.Popen(shell_cmd, shell=True, stderr=subprocess.PIPE)
    _, err = process.communicate()

    if process.returncode != 0:
        # parse error message if needed
        err_decoded = err.decode(errors='replace')
        print(f"Error while running {command}, retcode={process.returncode}:")
        print(err_decoded)
        sys.exit(process.returncode)

    print(f"{command} ended normally, see {outfile}")



def check_scf(output_file: str) -> tuple:
    """
    Checks if the SCF calculation has converged by analyzing the output file.
    Returns a tuple (converged, error_message).
    """
    converged = False
    with open(output_file, 'r') as infile:
        for line in infile:
            if 'convergence criteria cannot be satisfied' in line:
                converged = False
                break
            if 'convergence criteria satisfied' in line:
                converged = True
                break

    if not converged:
        return False, 'not converged'
    else:
        hlg = None
        with open('eiger.out', 'r') as infile:
            for line in infile:
                if 'Gap' in line:
                    hlg = float(line.split()[-2])
                    break
        if hlg is not None and hlg < 0:
            return False, 'negative HLG'
        else:
            return True, None


def check_escf(output_file: str) -> tuple:
    """
    Checks if the excited state calculation using escf has successfully completed.
    Returns a tuple (done, error_message).
    """
    done = False
    with open(output_file, 'r') as infile:
        for line in infile:
            if 'all done' in line:
                done = True
                break
    return done, None


def check_opt() -> tuple:
    """
    Checks if the geometry optimization converged by examining the presence of certain files.
    Returns a tuple (converged, error_message).
    """
    converged = os.path.isfile('GEO_OPT_CONVERGED')
    error_message = ''

    if not converged:
        if os.path.isfile('GEO_OPT_RUNNING'):
            error_message = 'jobex did not end properly'
        else:
            with open('GEO_OPT_FAILED', 'r') as infile:
                for line in infile:
                    if 'OPTIMIZATION DID NOT CONVERGE' in line:
                        error_message = 'opt not converged'
                        break
                    if 'your energy calculation did not converge' in line:
                        step_nr = glob.glob('job.[123456789]')[0].split('.')[-1] if glob.glob('job.[123456789]') else 'unknown'
                        error_message = f'scf problem during step nr. {step_nr}'
                        break
    return converged, error_message


# def get_hyper_polarizability_2nd_pair() -> np.ndarray:
#     """
#     Extracts and returns the electronic dipole hyperpolarizability tensor for the 2nd pair of frequencies from 'escf.out'.
#     """
#     with open("escf.out", "r") as infile:
#         escf_data = infile.readlines()

#     # Variables to keep track of the sections
#     in_2nd_pair = False
#     begin_hyper_pol = None
#     for i, line in enumerate(escf_data):
#         if "2nd pair of frequencies" in line:
#             in_2nd_pair = True
#         elif "Electronic dipole hyperpolarizability" in line and in_2nd_pair:
#             begin_hyper_pol = i + 4  # The data starts 4 lines after this line
#             break
#         elif "3rd pair of frequencies" in line:
#             # We've moved past the 2nd pair without finding the hyperpolarizability data
#             break

#     if begin_hyper_pol is None:
#         raise ValueError("Electronic dipole hyperpolarizability section for 2nd pair not found in escf.out")

#     # Initialize the hyperpolarizability tensor (3x3x3)
#     beta = np.zeros((3, 3, 3))

#     # Extract the 9 lines containing the tensor components
#     lines = escf_data[begin_hyper_pol:begin_hyper_pol + 9]

#     # Mapping from component letters to indices
#     char_to_index = {'x': 0, 'y': 1, 'z': 2}

#     for line in lines:
#         tokens = line.strip().split()
#         for j in range(0, len(tokens), 2):
#             component = tokens[j]  # e.g., 'xxx', 'yxx', etc.
#             value = float(tokens[j + 1])*8.6393*1E-3 

#             # Convert component letters to tensor indices
#             a = char_to_index[component[0]]
#             b = char_to_index[component[1]]
#             c = char_to_index[component[2]]

#             # Assign the value to the tensor
#             beta[a, b, c] = value

#     return beta

def get_hyper_polarizability_for_pair(pair_number: int, filename: str = "hyperpols") -> np.ndarray:
    """
    Extracts and returns the electronic dipole hyperpolarizability tensor for the specified pair of frequencies
    (1st, 2nd, or 3rd) from the given file "hyperpols".

    The file format is expected to have a line like:
        "1st pair of frequencies"
    followed by 4 lines of frequency information, then 9 lines containing the hyperpolarizability data
    in columns such as:
        xxx   [val]   yxx  [val]   zxx  [val]
        xyx   [val]   yyx  [val]   zyx  [val]
        ...
    etc.

    Parameters
    ----------
    pair_number : int
        The frequency pair number to extract (e.g., 1 for '1st pair of frequencies', 2 for '2nd', etc.).
    filename : str, optional
        The path to the file to read from; defaults to "hyperpols".

    Returns
    -------
    np.ndarray
        A 3x3x3 NumPy array containing the electronic dipole hyperpolarizability tensor for the requested frequency pair.
    """

    def ordinal(n: int) -> str:
        """Convert an integer into its ordinal string (1 -> '1st', 2 -> '2nd', 3 -> '3rd', etc.)."""
        return (
            f"{n}st" if (n % 10 == 1 and n % 100 != 11) else
            f"{n}nd" if (n % 10 == 2 and n % 100 != 12) else
            f"{n}rd" if (n % 10 == 3 and n % 100 != 13) else
            f"{n}th"
        )

    # Read all lines from the file
    with open(filename, "r") as infile:
        lines = infile.readlines()

    # Prepare the string like "1st pair of frequencies"
    target_pair_string = f"{ordinal(pair_number)} pair of frequencies"

    # Locate the starting line for the requested pair
    pair_line_index = None
    for i, line in enumerate(lines):
        if target_pair_string in line:
            pair_line_index = i
            break

    if pair_line_index is None:
        raise ValueError(f"Could not find '{target_pair_string}' in the file '{filename}'.")

    # Skip the pair header + 4 lines of frequency information
    start_index = pair_line_index + 5
    end_index = start_index + 9  # The next 9 lines contain the tensor data

    hyperpol_lines = lines[start_index:end_index]
    if len(hyperpol_lines) < 9:
        raise ValueError(
            f"Could not extract the 9 lines of hyperpolarizability data after '{target_pair_string}' in '{filename}'."
        )

    # Initialize the 3×3×3 hyperpolarizability tensor
    beta = np.zeros((3, 3, 3))

    # Mapping from component letters to indices
    char_to_index = {'x': 0, 'y': 1, 'z': 2}

    # Parse each of the 9 lines for hyperpolarizability components
    for line in hyperpol_lines:
        tokens = line.strip().split()
        # Example tokens: ['xxx','193.63592354297','yxx','-60.270120554117','zxx','-683.79315920614']
        for j in range(0, len(tokens), 2):
            component = tokens[j]     # e.g., 'xxx', 'yxx', 'zxx'
            # Use a decimal constant to avoid scientific notation
            value = float(tokens[j + 1]) * 0.0086393

            # Convert component letters to indices
            a = char_to_index[component[0]]  # x -> 0, y -> 1, z -> 2
            b = char_to_index[component[1]]
            c = char_to_index[component[2]]

            # Fill in the tensor
            beta[a, b, c] = value

    return beta


def get_dipole_moment() -> np.ndarray:
    """
    Retrieves the dipole moment vector from the 'control' file in the current working directory.
    """
    with open("control", "r") as infile:
        control_data = infile.readlines()

    begin_dipole = None
    for i, line in enumerate(control_data):
        if "$dipole" in line:
            begin_dipole = i + 1
            break
    if begin_dipole is None:
        raise ValueError("Dipole moment section not found in control file.")

    dipole_line = control_data[begin_dipole].strip()
    tokens = dipole_line.split()

    dipole_dict = {}
    i = 0
    while i < len(tokens):
        if tokens[i] in ['x', 'y', 'z']:
            label = tokens[i]
            i += 1
            if i < len(tokens):
                try:
                    value = float(tokens[i])
                    dipole_dict[label] = value
                except ValueError:
                    raise ValueError(f"Expected a float after {label}, but got {tokens[i]}")
            else:
                raise ValueError(f"Expected a value after {label}, but reached end of line.")
        i += 1

    if len(dipole_dict) != 3:
        raise ValueError("Dipole moment components not properly found.")

    dipole = np.array([dipole_dict['x'], dipole_dict['y'], dipole_dict['z']])
    return dipole
