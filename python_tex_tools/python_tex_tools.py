# This file was created to export the results of python calculations to tech
# we can add variables to a list and later export the List to a .tex file which we can
# include in the project
from multiprocessing.sharedctypes import Value
from typing import List

TIKZPLOTLIB_AVAILABLE = True
try:
    import tikzplotlib
except ImportError:
    TIKZPLOTLIB_AVAILABLE = False
    
import os
import matplotlib.pyplot as plt
from matplotlib import rcParams
from tabulate import tabulate
import tempfile
import shutil
from pathlib import Path


class TexExporter:
    """
    This class exports python variables to Latex. You need to create an object of class
    tex_exporter and add key - value pairs to it. Finally, you can export everything to
    a .tex file which only needs to be included in your tex project.
    """

    def __init__(self, verbose=False) -> None:
        """Initializes the tex_exporter class.

        Args:
            dir_name (str, optional): here, you can set the output directory. If not
             defined, the constructor will try to retreive the value from the
             TEX_EXPORTER_DIR environment variable.
             Defaults to None.
            var_file_name (str, optional): Defines the name of the latex file, holding
             the vairables. Defaults to python_results.tex.
        """
       
        # make a temporary directory
        self.tmp_dir = tempfile.mkdtemp()
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        self.var_list = []  # Name; Value
        self.fig_list = []  # Name; Figure
        self.tab_list = []  # Name; Table
        self.var_function_prefix = "var"
        self.fig_function_prefix = "tikz"
        self.tab_function_prefix = "tab"
        self.verbose = verbose

    def add_var(self, name, value, unit_name=""):
        self.check_name_consistency(name)
        if not type(value) == str:
            value = str(value)  # Try to convert to string if it is not
        if unit_name == "":
            # apply as number
            value="\\num{"+value+"}"

        if not unit_name == "":
            value="\\SI{"+value+"}{"+unit_name+"}"

        self.var_list.append([name, value])
        if self.verbose:
            print(f"New Variable: \\{self.var_function_prefix}{name}")

    def add_figure(self, name: str, figure: plt.figure, plotlib_params=None, article_type="single_column"):
        if TIKZPLOTLIB_AVAILABLE:
            self.add_figure_tikzplotlib(name, figure, plotlib_params)
        else:
            #raise NotImplementedError("tikzplotlib is not available. This could be related to deprecation.")
            self.add_figure_pgfplots(name, figure, plotlib_params, article_type)
            
    def add_figure_pgfplots(self, name: str, figure: plt.figure, plotlib_params: dict, article_type: str):
        self.check_name_consistency(name)
        
        figsize_default = { # default figure size in inches
            "single_column": (4.9, 3.5),
            "double_column": (2.45, 1.75),
        }    
        
        default_settings = {
                #"pgf.texsystem": "pdflatex",  # Use LaTeX for processing
                "figure.figsize" : figsize_default[article_type],
                "font.family": "serif",       # Use serif fonts
                "text.usetex": True,          # Enable LaTeX
                "pgf.rcfonts": False,         # Don't use rc settings for fonts
                "text.latex.preamble": r"\usepackage{amsmath}\usepackage{amssymb}\usepackage{siunitx}[=v2]"
            }
        
        # Configure LaTeX settings for matplotlib
        if plotlib_params is not None:
            # update default settings with user-defined settings
            for key, value in plotlib_params.items():
                rcParams[key] = value
            rcParams.update(plotlib_params)
        else:
            # using default settings for pgfplots
            rcParams.update(default_settings)
        
        # save the figure as a pgf file in the temporary directory
        pgf_file_path = os.path.join(self.tmp_dir, name + ".pgf")
        figure.savefig(pgf_file_path, format="pgf")
        
        self.fig_list.append([name, pgf_file_path])        
        
    def add_figure_tikzplotlib(self, name: str, figure: plt.figure, tikzplotlib_params=None):
        self.check_name_consistency(name)
        if tikzplotlib_params is not None:
            tikz_code = tikzplotlib.get_tikz_code(
                figure, table_row_sep="\\\\", **tikzplotlib_params
            )
        else:
            tikz_code = tikzplotlib.get_tikz_code(figure, table_row_sep="\\\\")

        self.fig_list.append([name, tikz_code])
        if self.verbose:
            print(f"New Figure:  \\{self.fig_function_prefix}{name}")

    def add_table(self, name: str, table, headers: List[str] = "firstrow"):
        self.check_name_consistency(name)
        table_code = tabulate(table, tablefmt="latex_raw", headers=headers)

        # replace hline with tpp and bottomrule
        table_code = table_code.replace(r"\hline", r"\midrule")
        table_code = table_code.replace(r"\midrule", r"\toprule",1)

        # replace the last -> replace first in reversed string
        target_reverse = (r"\midrule")[::-1]
        table_code = (table_code[::-1].replace(target_reverse, (r"\bottomrule")[::-1], 1))[::-1]

        self.tab_list.append([name, table_code])
        if self.verbose:
            print(f"New Table:  \\{self.tab_function_prefix}{name}")

    def check_name_consistency(self, name: str):
        """Latex variable names should only contain chars.

        Args:
            name (str): the string to check
        """
        if any(not char.isalpha() for char in name):
            raise ValueError("Only chars are permitted in latex variable names.")

    def export(self, export_path=".", var_file_name="python_results.tex"):
        
        export_path = Path(export_path).resolve()
        var_file_path = os.path.join(export_path, var_file_name)

        print("Writing output to %s." % var_file_path)
        f = open(var_file_path, "wt")
        print("Exporting elements as LaTex functions")
        print("Variables:")
        for i, e in enumerate(self.var_list):
            print("\\" + self.var_function_prefix + e[0])
            f.write(
                "\\newcommand{\\"
                + self.var_function_prefix
                + e[0]
                + "}{"
                + e[1]
                + "}" #+ "\\:" re enable this later!
                + "\n"
            )
            
        print("Figures:")
        for i, e in enumerate(self.fig_list):
            # if the figure is a pgf file, we need to copy it to the output dir
            if e[1].endswith(".pgf"):
                pgf_file_path = os.path.join(export_path, e[0] + ".pgf")
                shutil.copy(e[1], pgf_file_path)
            else:
                print("\\" + self.fig_function_prefix + e[0])
                f.write(
                    "\\newcommand{\\"
                    + self.fig_function_prefix
                    + e[0]
                    + "}{"
                    + e[1]
                    + "}"
                    + "\n"
                )

        print("Tables:")
        for i, e in enumerate(self.tab_list):
            print("\\" + self.tab_function_prefix + e[0])
            f.write(
                "\\newcommand{\\"
                + self.tab_function_prefix
                + e[0]
                + "}{"
                + e[1]
                + "}"
                + "\n"
            )
        f.close()
        
    def __del__(self):
        # remove the temporary directory
        shutil.rmtree(self.tmp_dir)
