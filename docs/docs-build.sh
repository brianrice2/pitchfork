# Install dependencies
python -m pip install -r docs/requirements.txt

# Autogenerate pages
sphinx-apidoc -f -o docs/source/ docs/ 

# Make HTML files
make html
