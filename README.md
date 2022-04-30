# pythonTexTools

This package provides a simple way to export information from Python to LaTeX for automatic document production such as reports or student projects.

## Setup:

- Clone the repo
- Install with pip install -e .

## Usage:

1. Initialize the object: exporter = tex_exporter(dir_name=\<Name of the output directory\>)
2. Add a variable to the tes_exporter object: exporter.add_var(my_variable_name, my_value)
3. Create the .tex File after you've added all information to the exporter: exporter.export()

The files are then written to a .tex file in your output directory. You can include this
file in you latex document by using \include{document_name.tex}. All previously added
variables and figures are represented by a \var\<variable_name\> command.
