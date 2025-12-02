#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status.

#------------------------------------------------------------------------------
# 1. Helper Functions
#------------------------------------------------------------------------------

# Check if a command exists on PATH
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Source the conda/mamba "activate" script in a given base directory
initialize_conda() {
    local conda_base_dir="$1"
    if [[ -f "$conda_base_dir/etc/profile.d/conda.sh" ]]; then
        # Shellcheck disable=SC1090
        source "$conda_base_dir/etc/profile.d/conda.sh"
    else
        echo "ERROR: Could not find conda.sh in $conda_base_dir/etc/profile.d/"
        exit 1
    fi
}

#------------------------------------------------------------------------------
# 2. Detect Environment Manager (mamba or conda)
#------------------------------------------------------------------------------

CONDA_BASE=""
ENV_MANAGER=""

if command_exists mamba; then
    ENV_MANAGER="mamba"
    CONDA_BASE="$($ENV_MANAGER info --base | grep '^/')"
    initialize_conda "$CONDA_BASE"
    echo "Using mamba as the environment manager."
elif command_exists conda; then
    ENV_MANAGER="conda"
    CONDA_BASE="$(conda info --base)"
    initialize_conda "$CONDA_BASE"
    echo "Using conda as the environment manager."
else
    echo "ERROR: Neither mamba nor conda found on this system."
    echo "Please install one of them or ensure it is on your PATH."
    exit 1
fi

#------------------------------------------------------------------------------
# 3. Check/Create "playground_simstack" Environment
#------------------------------------------------------------------------------

# If the environment "playground_simstack" does not exist, clone from "simstack_server_v6"
if $ENV_MANAGER env list | grep -qE "^[^#]*playground_simstack\s"; then
    echo "Environment 'playground_simstack' already exists."
else
    echo "Environment 'playground_simstack' does NOT exist. Creating it by cloning 'simstack_server_v6'."
    $ENV_MANAGER create -n playground_simstack --clone simstack_server_v6 -y
fi

#------------------------------------------------------------------------------
# 4. Activate the Environment
#------------------------------------------------------------------------------

echo "Activating environment 'playground_simstack'."
# Safest universal approach is to source the 'activate' script from the base directory:
source "$CONDA_BASE/bin/activate" playground_simstack

#------------------------------------------------------------------------------
# 5. Optional: Install Additional Packages (e.g., from requirements.txt)
#------------------------------------------------------------------------------

if [[ -f requirements.txt ]]; then
    echo "Installing packages from requirements.txt..."
    while read -r package; do
        # Skip empty lines and comment lines
        if [[ -z "$package" ]] || [[ "$package" == \#* ]]; then
            continue
        fi

        # Extract the raw package name without version spec
        package_name=$(echo "$package" | sed 's/[<>=!].*//')

        # Check if it's already installed in this environment
        if ! pip show "$package_name" >/dev/null 2>&1; then
            echo "Package '$package' not installed. Installing..."
            pip install "$package"
        else
            echo "Package '$package_name' is already installed."
        fi
    done < requirements.txt
else
    echo "No requirements.txt found. Skipping pip installations."
fi

echo "Environment setup script finished successfully."
