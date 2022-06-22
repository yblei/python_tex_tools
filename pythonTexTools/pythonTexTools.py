# This file was created to export the results of python calculations to tech
# we can add variables to a list and later export the List to a .tex file which we can
# include in the project
import tikzplotlib
import os
import matplotlib.pyplot as plt
from tabulate import tabulate


class tex_exporter:
    """
    This class exports python variables to Latex. You need to create an object of class
    tex_exporter and add key - value pairs to it. Finally, you can export everything to
    a .tex file which only needs to be included in your tex project.
    """

    def __init__(
        self, dir_name=None, res_file_name="python_results.tex", verbose=False
    ) -> None:
        """Initializes the tex_exporter class.

        Args:
            dir_name (str, optional): here, you can set the output directory. If not
             defined, the constructor will try to retreive the value from the
             TEX_EXPORTER_DIR environment variable.
             Defaults to None.
            var_file_name (str, optional): Defines the name of the latex file, holding
             the vairables. Defaults to python_results.tex.
        """
        if dir_name is None:
            if "TEX_EXPORTER_DIR" in os.environ:
                dir_name = os.environ["TEX_EXPORTER_DIR"]
            else:
                raise ValueError(
                    "You must specify at least file_name attribute or"
                    "TEX_EXPORTER_DIR environment variable"
                )
            if not os.path.exists(dir_name):
                raise FileNotFoundError("Path %s does not exist" % dir_name)
        self.var_file_name = res_file_name

        self.dir_name = dir_name
        self.var_list = []  # Name; Value
        self.fig_list = []  # Name; Figure
        self.tab_list = []  # Name; Table
        self.var_function_prefix = "var"
        self.fig_function_prefix = "tikz"
        self.tab_function_prefix = "tab"
        self.verbose = verbose

    def add_var(self, name, value, unit_name=""):
        if not type(value) == str:
            value = str(value)  # Try to convert to string if it is not
        if not unit_name == "":
            unit_name = " " + unit_name

        self.var_list.append([name, value, unit_name])
        if self.verbose:
            print(f"New Variable: \\{self.var_function_prefix}{name}")

    def add_figure(self, name: str, figure: plt.figure, tikzplotlib_params=None):
        if tikzplotlib_params is not None:
            tikz_code = tikzplotlib.get_tikz_code(
                figure, table_row_sep="\\\\", **tikzplotlib_params
            )
        else:
            tikz_code = tikzplotlib.get_tikz_code(figure, table_row_sep="\\\\")

        self.fig_list.append([name, tikz_code])
        if self.verbose:
            print(f"New Figure:  \\{self.fig_function_prefix}{name}")

    def add_table(self, name: str, table):
        table_code = tabulate(table, tablefmt="latex")
        self.tab_list.append([name, table_code])
        if self.verbose:
            print(f"New Table:  \\{self.tab_function_prefix}{name}")

    def export(self):
        var_file_path = os.path.join(self.dir_name, self.var_file_name)
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
                + "\\:"
                + e[2]
                + "}"
                + "\n"
            )
        print("Figures:")
        for i, e in enumerate(self.fig_list):
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


        # clear all data
        self.var_list = []
        self.fig_list = []
        self.tab_list = []
