# This file was created to export the results of python calculations to tech
# we can add variables to a list and later export the List to a .tex file which we can include in the project
import io

class tex_exporter:
    """
    This class exports python variables to Latex. You need to create an object of class tex_exporter and add key - value pairs to it.
    Finally, you can export everything to a .tex file which only needs to be included in your tex project.
    """
    def __init__(self, file_name) -> None:
        self.file_name = file_name
        self.var_list=[] # Name; Value
        self.function_prefix = "var"

    def add_var(self, name, value, unit_name=""):
        if not type(value) == str:
            value = str(value) #Try to convert to string if it is not
        if not unit_name == "":
            unit_name = " " + unit_name

        self.var_list.append([name, value, unit_name])

    def export(self):
        F = open(self.file_name, "wt")
        print("Exporting variables as LaTex functions:")
        for i, e in enumerate(self.var_list):
            print("\\" + self.function_prefix + e[0])
            F.write("\\newcommand{\\" + self.function_prefix + e[0] + "}{" + e[1] + "\\:" + e[2] +"}" + "\n")
        F.close()

        #clear all data
        self.var_list=[]
