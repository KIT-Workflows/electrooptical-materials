import numpy as np
from pathlib import Path

###############################################################################
#                          MINIMAL NECESSARY FUNCTIONS                        #
###############################################################################

def check_file_exists(filename):
    """Checks whether a given file path actually exists."""
    if filename is None:
        return False
    if not Path(filename).is_file():
        print(f"Warning: File {filename} does not exist.")
        return False
    else:
        return True


def get_dipole_vector(filename):
    """
    Extracts the x, y, z dipole components from a Turbomole ridft.out file,
    returning them as (x, y, z). Each is a small array, from which we later
    pick the 3rd column in tmole_vectors_to_3d_vec() if needed.
    """
    with open(filename, "r") as inf:
        reading_dipole = False
        x = y = z = None
        for line in inf:
            if "dipole moment" in line:
                # Start reading lines for x, y, z
                reading_dipole = True
                continue

            if reading_dipole:
                parts = line.split()
                # Typically something like: " x   0.000000  0.000000  0.529177 "
                if len(parts) == 4 and parts[0] in ["x", "y", "z"]:
                    coord = parts[0]
                    vals = np.array(parts[1:], dtype=float)
                    if coord == "x":
                        x = vals
                    elif coord == "y":
                        y = vals
                    elif coord == "z":
                        z = vals

                # If all three found, return
                if x is not None and y is not None and z is not None:
                    return x, y, z

    return None


def tmole_vectors_to_3d_vec(x, y, z):
    """
    For Turbomole's typical dipole array, we often want just the 3rd element
    (index=2) from each of (x, y, z). Adjust if your ridft.out is different.
    """
    print("Warning: Only using the 3rd component from each dipole array (x,y,z).")
    return np.array([x[2], y[2], z[2]])


def Rzyx(alpha, beta, gamma):
    """
    Builds a rotation matrix for angles:
      - alpha around z
      - beta  around y
      - gamma around x
    Then multiplies in the order R = Rx(gamma) @ Ry(beta) @ Rz(alpha).
    """
    Rz = np.array([
        [np.cos(alpha), -np.sin(alpha), 0],
        [np.sin(alpha),  np.cos(alpha),  0],
        [0,              0,             1],
    ])
    Rx = np.array([
        [1,             0,              0],
        [0, np.cos(gamma), -np.sin(gamma)],
        [0, np.sin(gamma),  np.cos(gamma)],
    ])
    Ry = np.array([
        [ np.cos(beta), 0, np.sin(beta)],
        [ 0,            1,           0],
        [-np.sin(beta), 0, np.cos(beta)],
    ])

    return Rx @ Ry @ Rz


def calculate_angles_to_rotate_dipole_vector_on_z_axis(dipole_vector):
    """
    Determines angles alpha, beta, gamma so that
    rotating the input dipole vector with Rzyx(-alpha, -beta, -gamma)
    will align it to the z-axis.

    alpha = arctan2(dy, dx)
    beta  = arctan2(rotated_dx, rotated_dz)
    gamma = 0 (not used here).
    """
    alpha = np.arctan2(dipole_vector[1], dipole_vector[0])

    # Rotate around z by -alpha, see how that affects (x, y, z)
    rotated_vector = np.dot(Rzyx(-alpha, 0.0, 0.0), dipole_vector)

    # Then compute beta so that rotation around y will put the vector onto z
    beta = np.arctan2(rotated_vector[0], rotated_vector[2])
    gamma = 0.0

    return alpha, beta, gamma


###############################################################################
#                 NEW FUNCTION: EXTRACT SPECIFIC PAIR FROM "hyperpols"        #
###############################################################################

def get_hyper_polarizability_for_pair(pair_number: int, filename: str = "hyperpols") -> np.ndarray:
    """
    Reads the file 'hyperpols' and returns a 3x3x3 NumPy array of hyperpolarizability
    tensor components (in atomic units) for the chosen frequency pair (1st, 2nd, or 3rd).

    It looks for lines of the form "1st pair of frequencies", "2nd pair of frequencies",
    etc., then skips the next 4 lines of frequency data, then reads the 9 lines of
    hyperpolarizability components such as "xxx  value  yxx  value  zxx  value" etc.

    Note: This function returns values in a.u.; do NOT multiply by any factor here
    if you will convert them later in your main code.
    """
    def ordinal(n):
        """Convert an integer into its ordinal string: 1->'1st', 2->'2nd', 3->'3rd', etc."""
        return (
            f"{n}st" if (n % 10 == 1 and n % 100 != 11) else
            f"{n}nd" if (n % 10 == 2 and n % 100 != 12) else
            f"{n}rd" if (n % 10 == 3 and n % 100 != 13) else
            f"{n}th"
        )

    with open(filename, "r") as infile:
        lines = infile.readlines()

    target_string = f"{ordinal(pair_number)} pair of frequencies"
    pair_line_index = None

    # Find the line containing "1st pair of frequencies", etc.
    for i, line in enumerate(lines):
        if target_string in line:
            pair_line_index = i
            break

    if pair_line_index is None:
        raise ValueError(f"Could not find '{target_string}' in file '{filename}'.")

    # Skip this line + 4 lines of frequency info
    start_index = pair_line_index + 5
    end_index = start_index + 9  # The next 9 lines contain hyperpolarizability data

    hyperpol_lines = lines[start_index:end_index]
    if len(hyperpol_lines) < 9:
        raise ValueError(
            f"Could not extract the 9 lines of hyperpolarizability data after '{target_string}'."
        )

    # Create a 3x3x3 zero array
    beta = np.zeros((3, 3, 3))

    # Map 'x','y','z' -> 0,1,2
    char_to_index = {'x': 0, 'y': 1, 'z': 2}

    # Parse each line containing 3 sets of (component, value)
    for line in hyperpol_lines:
        tokens = line.strip().split()
        # Example: ['xxx','193.63','yxx','-60.27','zxx','-683.79']
        for j in range(0, len(tokens), 2):
            component = tokens[j]          # e.g. 'xxx'
            val = float(tokens[j + 1])     # parse as float (still in a.u.)

            # Convert 'xxx' -> (0,0,0), 'yxx'->(1,0,0), etc.
            i0 = char_to_index[component[0]]
            i1 = char_to_index[component[1]]
            i2 = char_to_index[component[2]]

            beta[i0, i1, i2] = val

    return beta


###############################################################################
#                  HELPER FOR CONVERTING FROM a.u. TO 10^-30 ESU              #
###############################################################################

def au_to_esu(value_au):
    """
    Converts hyperpolarizability from a.u. to 10^-30 esu in decimal form (no 'e-3').
    1 a.u. = 8.6393e-33 esu, but multiplied by 1e30 => 8.6393e-3,
    which we represent here as 0.0086393 to avoid scientific notation.
    """
    return value_au * 0.0086393


###############################################################################
#                           MAIN FUNCTION STARTS HERE                         #
###############################################################################

def hyper_main(pair_number=2):
    """
    Minimal demonstration:
      1) Checks for 'ridft.out' and 'hyperpols' in the current folder.
      2) Extracts and aligns the dipole to z.
      3) Loads the chosen hyperpolarizability pair (in a.u.) from 'hyperpols' using get_hyper_polarizability_for_pair().
      4) Converts it to 10^-30 esu, rotates it by the same angles, and returns beta_zzz.
    """

    dip_file = "ridft.out"
    hyper_file = "hyperpols"

    # Check file existence
    if not (check_file_exists(dip_file) and check_file_exists(hyper_file)):
        print("Hyperpolarizability zzz component (aligned z with molecular dipole) not accessible.")
        return None

    # Get the dipole (x, y, z) from ridft.out
    dip_data = get_dipole_vector(dip_file)
    if dip_data is None:
        print("Could not parse dipole from ridft.out.")
        return None

    # Convert the Turbomole arrays to a single 3D vector
    x, y, z = dip_data
    dipole_vector = tmole_vectors_to_3d_vec(x, y, z)

    # Calculate angles to align dipole_vector onto z-axis
    alpha, beta, gamma = calculate_angles_to_rotate_dipole_vector_on_z_axis(dipole_vector)

    # Extract the chosen hyperpolarizability (in a.u.) from 'hyperpols'
    hyper_tensor_au = get_hyper_polarizability_for_pair(pair_number, hyper_file)

    # Convert from a.u. to 10^-30 esu
    hyper_tensor_esu = np.vectorize(au_to_esu)(hyper_tensor_au)

    # Build rotation matrix for -alpha, -beta, -gamma
    R = Rzyx(-alpha, -beta, -gamma)

    # Rotate hyperpolarizability tensor:
    # T'_{i j k} = \sum_{p, q, r} R_{i p} R_{j q} R_{k r} T_{p q r}
    hyper_tensor_esu_rot = np.einsum('ip,jq,kr,pqr->ijk', R, R, R, hyper_tensor_esu)

    # Finally, extract beta_zzz in the rotated coordinate system
    beta_zzz = hyper_tensor_esu_rot[2, 2, 2]

    return beta_zzz


# result = hyper_main(pair_number=3)
# print(result)

# Example of how you might call it:
# if __name__ == "__main__":
#     result = hyper_main(pair_number=2)
#     if result is not None:
#         print(f"Hyperpolarizability zzz (aligned) for pair #2 = {result:.2f} x 10^-30 esu")
