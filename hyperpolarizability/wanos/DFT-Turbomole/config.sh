#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Name of the environment
env_name="playground_simstack"


source /home/ws/pr7831/mambaforge/etc/profile.d/conda.sh
conda activate playground_simstack


#------------------------------------------------------------------------------
# Optional: Install Additional Packages (e.g., from requirements.txt)
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




# Load turbomole
module load turbomole/7.6



# 4. Run your Python scripts
python_scripts=("run_tm.py")

run_python_script() {
    local script_name="$1"
    if [[ -f "$script_name" ]]; then
        echo "Running Python script: $script_name"
        python "$script_name"
    else
        error_exit "Python script '$script_name' not found."
    fi
}

for script in "${python_scripts[@]}"; do
    run_python_script "$script"
done

