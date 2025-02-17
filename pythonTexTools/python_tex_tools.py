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
import tempfile
import shutil
from pathlib import Path
from .utils import print_best_values_fat
import pandas as pd


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

    def add_figure(self, name: str, figure: plt.figure):
        if TIKZPLOTLIB_AVAILABLE:
            self.add_figure_tikzplotlib(name, figure, plotlib_params)
        else:
            #raise NotImplementedError("tikzplotlib is not available. This could be related to deprecation.")
            self.add_figure_pgfplots(name, figure)
            
    def add_figure_pgfplots(self, name: str, figure: plt.figure):
        self.check_name_consistency(name)
                
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

    def add_table(self, name: str, table: pd.DataFrame, print_best_values_bf: bool = True, bf_options: dict = None):
        self.check_name_consistency(name)
        
            # check, if df is a pandas dataframe
        if not isinstance(table, pd.DataFrame):
            raise ValueError("The input table is not a pandas DataFrame.")
        
        bf_default_options = {
            "axis": 0,
            "higher_or_lower_is_better": "higher", # could als be an array like ["higher", "lower", "higher", "lower"] with the same length as the number of columns/ rows in the table
        }
        
        if bf_options is not None:
            for key, value in bf_default_options.items():
                if key not in bf_options:
                    raise ValueError(f"Unsupported key {key}. Supported Keys are: {bf_default_options.keys()}")
                else:
                    bf_default_options[key] = bf_options[key]
        
        if print_best_values_bf:
            table = print_best_values_fat(table, **bf_default_options)
        
        table_code = table.to_latex(escape=False)

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
        
        print("Exporting elements as LaTex functions. PGF files will be copied to the output directory.")
        
        if len(self.var_list) > 0:
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
            
        if len(self.fig_list) > 0:
            print("")
            print("Figures:")
            for i, e in enumerate(self.fig_list):
                # if the figure is a pgf file, we need to copy it to the output dir
                if e[1].endswith(".pgf"):
                    pgf_file_name = os.path.basename(e[0] + ".pgf")
                    pgf_file_path = os.path.join(export_path, pgf_file_name)
                    shutil.copy(e[1], pgf_file_path)
                    print(pgf_file_name)
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
                
        if len(self.tab_list) > 0:
            print("")
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
