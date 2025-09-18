# Install deps

# Clone fresh repo
git clone --quiet -c advice.detachedHead=false --branch v2.1.0 --depth 1 git@github.com:numerique-gouv/sites-faciles.git sites_faciles_temp
cd sites_faciles_temp

# Run refactor
../packagify.py -v

# Cleanup
cd ..
rm -rf sites_faciles
mv sites_faciles_temp sites_faciles
rm -rf sites_faciles/.git \
    sites_faciles/.github \
    sites_faciles/pyproject.toml

git restore --source=fork/main "**/apps.py"
git restore --source=fork/main "**/__init__.py"
