import unittest
import os
import matplotlib.pyplot as plt
import numpy as np
from python_tex_tools import TexExporter, make_plt_look_like_latex
import shutil
from pandas import DataFrame

class TestPythonTexTools(unittest.TestCase):
    def setUp(self) -> None:
        self.test_folder = os.path.dirname(__file__) + "/test_folder"
        if not os.path.exists(self.test_folder):
            os.makedirs(self.test_folder)
        self.res_file_name = "python_results.tex"
        self.res_file_path = os.path.join(self.test_folder, self.res_file_name)

    def test_diagrams(self):
        test_exporter = TexExporter()

        with make_plt_look_like_latex():
            fig = plt.figure()
            ax = fig.add_subplot(1, 1, 1)
            x = np.linspace(0, 10, 1000)
            y = np.sin(x)
            ax.plot(x, y)

        test_exporter.add_figure("TestFigure", fig)
        test_exporter.export(export_path=self.test_folder, var_file_name=self.res_file_name)
        self.assertTrue(os.path.isfile(self.res_file_path))

    def test_table(self):
        tab_size = 3
        test_exporter = TexExporter()
        table = np.random.rand(tab_size, tab_size)
        table = DataFrame(table)
        
        # randomly choose "higher" or "lower" tab_size times
        higher_or_lower_is_better = np.random.choice(["higher", "lower"], tab_size)
        
        # setup options
        bf_options = {
            "axis": 0,
            "higher_or_lower_is_better": higher_or_lower_is_better,
        }
        
        # set column names
        table.columns = [f"Column_{i}" for i in range(tab_size)]
        
        # set row names
        table.index = [f"Row_{i}" for i in range(tab_size)]
        
        # add \percent to every entry of the table
        table = table.map(lambda x: f"{x:.2f} \\percent")
        
        test_exporter.add_table("TestTable", table, bf_options=bf_options)
        test_exporter.export(export_path=self.test_folder, var_file_name=self.res_file_name)
        self.assertTrue(os.path.isfile(self.res_file_path))

    def tearDown(self) -> None:
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)


if __name__ == "__main__":
    unittest.main()
