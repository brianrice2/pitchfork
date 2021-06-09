# Sphinx documentation

## Accessing docs

Open up `build/html/index.html` to access documentation.

## Updating docs

### Changes to current files

Any time that the current Python files or sphinx `.rst` files are changed, the `html` should be recreated by running from this directory:

```bash
make html
```

### Addition of files

If new files are added, the autodoc files should be recreated by running

```bash
sphinx-apidoc -f -o source/ ../
```

If new directories are added, the above command should be run for the new directory, and the directory needs to be added to `source/index.rst`.
