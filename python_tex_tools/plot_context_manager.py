import matplotlib.pyplot as plt
import copy

class make_plt_look_like_latex:
    def __init__(self, matplotlib_params: dict = None, diagram_size: str = "single_column"):
        figsize_default = { # default figure size in inches
            "single_column": (4.9, 3.5),
            "double_column": (2.45, 1.75),
        }    
        
        self.default_settings = {
                #"pgf.texsystem": "pdflatex",  # Use LaTeX for processing
                "figure.figsize" : figsize_default[diagram_size],
                "font.family": "serif",       # Use serif fonts
                "text.usetex": True,          # Enable LaTeX
                "pgf.rcfonts": False,         # Don't use rc settings for fonts
                "text.latex.preamble": r"\usepackage{amsmath}\usepackage{amssymb}\usepackage{siunitx}[=v2]"
            }
        
        # Configure LaTeX settings for matplotlib
        if matplotlib_params is not None:
            # update default settings with user-defined settings
            for key, value in self.matplotlib_params.items():
                self.default_settings[key] = value
            
    def __enter__(self):
        # safe old values
        self.original_rcParams = copy.deepcopy(plt.rcParams)
        
        plt.rcParams.update(self.default_settings)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # restore the old values
        plt.original_rcParams = self.original_rcParams