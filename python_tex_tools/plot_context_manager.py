import matplotlib.pyplot as plt
import copy

class make_plt_look_like_latex:
    def __init__(self, matplotlib_params: dict | tuple = None, diagram_size: str = "single_column"):
        """Context manager to make a matplotlib figure look like latex. 

        Args:
            matplotlib_params (dict, optional): Optional MPL parameters. Defaults to None.
            diagram_size (str | tuple, optional): Figure size preset or custom dimensions. 
                Use "single_column" or "double_column" for IEEE paper layout presets, 
                or provide a custom (width, height) tuple in inches. Defaults to "single_column".
        """
        figsize_default = { # default figure size in inches
            "single_column": (3.5, 2.75),
            "double_column": (7.2, 3.5),
        }    
        
        self.default_settings = {
                #"pgf.texsystem": "pdflatex",  # Use LaTeX for processing
                "figure.figsize" : figsize_default[diagram_size] if isinstance(diagram_size, str) else diagram_size,
                "font.family": "serif",       # Use serif fonts
                "text.usetex": True,          # Enable LaTeX
                "pgf.rcfonts": False,         # Don't use rc settings for fonts
                "text.latex.preamble": r"\usepackage{amsmath}\usepackage{amssymb}\usepackage{siunitx}[=v2]"
            }
        
        # Configure LaTeX settings for matplotlib
        if matplotlib_params is not None:
            # update default settings with user-defined settings
            for key, value in matplotlib_params.items():
                self.default_settings[key] = value
            
    def __enter__(self):
        # safe old values
        self.original_rcParams = copy.deepcopy(plt.rcParams)
        
        plt.rcParams.update(self.default_settings)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # restore the old values
        plt.original_rcParams = self.original_rcParams
