import unittest
import os
import matplotlib.pyplot as plt
import numpy as np
from python_tex_tools import TexExporter
import shutil

class TestPythonTexTools(unittest.TestCase):
    def setUp(self) -> None:
        self.test_folder = os.path.dirname(__file__) + "/test_folder"
        if not os.path.exists(self.test_folder):
            os.makedirs(self.test_folder)
        self.res_file_name = "python_results.tex"
        self.res_file_path = os.path.join(self.test_folder, self.res_file_name)

    def test_diagrams(self):
        test_exporter = TexExporter()
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        x = np.linspace(0, 10, 1000)
        y = np.sin(x)

        ax.plot(x, y)

        test_exporter.add_figure("TestFigure", fig)
        test_exporter.export(export_path=self.test_folder, var_file_name=self.res_file_name)
        self.assertTrue(os.path.isfile(self.res_file_path))

    def test_table(self):
        test_exporter = TexExporter()
        table = np.random.rand(10, 10)
        test_exporter.add_table("TestTable", table)
        test_exporter.export(export_path=self.test_folder, var_file_name=self.res_file_name)
        self.assertTrue(os.path.isfile(self.res_file_path))

    def tearDown(self) -> None:
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)


if __name__ == "__main__":
    unittest.main()
