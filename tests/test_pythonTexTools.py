import unittest
import os
import matplotlib.pyplot as plt
import numpy as np
from pythonTexTools import tex_exporter


class TestPythonTexTools(unittest.TestCase):
    def setUp(self) -> None:
        self.file_path = os.path.dirname(__file__)
        self.res_file_name = "python_results.tex"
        self.res_file_path = os.path.join(self.file_path, self.res_file_name)

    def test_diagrams(self):
        test_exporter = tex_exporter(
            dir_name=self.file_path, res_file_name=self.res_file_name
        )
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        x = np.linspace(0, 10, 1000)
        y = np.sin(x)

        ax.plot(x, y)

        test_exporter.add_figure("TestFigure", fig)
        test_exporter.export()
        self.assertTrue(os.path.isfile(self.res_file_path))

    def test_table(self):
        test_exporter = tex_exporter(
            dir_name=self.file_path, res_file_name=self.res_file_name
        )
        table = np.random.rand(10, 10)
        test_exporter.add_table("TestTable", table)
        test_exporter.export()
        self.assertTrue(os.path.isfile(self.res_file_path))

    def tearDown(self) -> None:
        if os.path.isfile(self.res_file_path):
            os.remove(self.res_file_path)


if __name__ == "__main__":
    unittest.main()
