# python_tex_tools

This package provides a simple way to export information from Python to LaTeX for automatic document production such as reports or student projects.
 
## Setup:
### Usage:
Simply execute the command below and you're good to go:
```
pip install git+ssh://git@github.com/yblei/pythonTexTools.git
```
#### Notes on exporting figures
We rely on LaTeX libraries to export the figures as PGF files.
If you did not install TeX yet, run: 

```
sudo apt-get install texlive-full
```


### Development:
- Clone the repo.
- Install dev dependencies with `pip install -e .[dev]`

## Minimal Example:
Please check [demo.ipynb](./demo.ipynb) to try yourself!
Notes on how to include this in your LaTeX are given **in this file as well**.

 ```
 test_exporter = TexExporter()

 exporter.add_var(my_variable_name, my_value)

 with make_plt_look_like_latex():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    x = np.linspace(0, 10, 1000)
    y = -np.sin(x)

    ax.plot(x, y)

test_exporter.add_figure("TestFigure", fig)

# Make a demo table
table = np.random.rand(2, 2).round(2)
table = pd.DataFrame(table)

# set row names
table.index = ["Row1", "Row2"]

# set col names
table.columns = ["Col1", "Col2"]

test_exporter.add_table("TestTable", table)

test_exporter.export(export_path=cwd)
 ```


The files are then written to a .tex file in your output directory. You can include this
file in you latex document by using \include{document_name.tex}. All previously added
variables and figures are represented by a \var\<variable_name\> command.
