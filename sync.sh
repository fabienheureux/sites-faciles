# Install deps
pip install pyyaml

# Clone repo fresh
git clone --depth 1 --branch v2.0.0 git@github.com:numerique-gouv/sites-faciles.git sites_faciles_temp
cd sites_faciles_temp

# Run refactor
../packagify.py -v

# Cleanup
cd ..
rm -rf sites_faciles_temp
