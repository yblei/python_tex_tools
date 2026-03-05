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
import subprocess
import matplotlib.pyplot as plt
from matplotlib import rcParams
import tempfile
import shutil
from pathlib import Path
from .utils import print_best_values_fat
import pandas as pd
import sys


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

    def register_overleaf(
        self,
        git_repo_url: str,
        auth_token: str,
        local_mirror_path: str = None,
        user_identifier: str = "python_tex_tools"
    ):
        """Register an Overleaf Git repository for automatic syncing.
        
        Args:
            git_repo_url: The Overleaf Git repository URL
            auth_token: Authentication token for Git access
            local_mirror_path: Local path for repo mirror (default: ~/.tex_exporter_overleaf_mirror)
            user_identifier: Identifier to mark commits as yours (default: "python_tex_tools")
        """
        # Store auth_token for later use
        self.auth_token = auth_token
        self.git_repo_url = git_repo_url
        self.user_identifier = user_identifier
        
        if local_mirror_path is None:
            local_mirror_path = Path(
                "~/.tex_exporter_overleaf_mirror"
            ).expanduser()

        repo_name = Path(git_repo_url.split("/")[-1].replace(".git", ""))
        local_repo_path = local_mirror_path / repo_name

        if not local_repo_path.exists():
            print(f"Creating new mirror at {local_mirror_path}")
            print(f"Cloning {git_repo_url} to {local_repo_path}...")
            
            # Embed auth token in URL
            authenticated_url = self._get_authenticated_url(git_repo_url)
            
            result = subprocess.run(
                ['git', 'clone', authenticated_url, str(local_repo_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Git output: {result.stdout}")
                print(f"Git error: {result.stderr}")
                raise RuntimeError(f"Git clone failed: {result.stderr}")
            
            print(result.stdout)
            print(result.stderr)
            self.repo_path = local_repo_path
        else:
            print(f"Using existing local mirror at {local_mirror_path}")
            # Pull with rebase to sync with remote and discard local changes
            print("Syncing with remote (discarding local changes)...")
            result = subprocess.run(
                ['git', 'pull', '--rebase'],
                cwd=local_repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Git pull output: {result.stdout}")
                print(f"Git pull error: {result.stderr}")
                # If rebase fails, try hard reset to remote
                print("Rebase failed, performing hard reset to remote...")
                
                # Get current branch
                branch_result = subprocess.run(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    cwd=local_repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                current_branch = branch_result.stdout.strip()
                
                # Fetch first
                subprocess.run(
                    ['git', 'fetch', 'origin'],
                    cwd=local_repo_path,
                    check=True
                )
                
                # Hard reset to remote
                subprocess.run(
                    ['git', 'reset', '--hard', f'origin/{current_branch}'],
                    cwd=local_repo_path,
                    check=True
                )
                print(f"✓ Reset to origin/{current_branch}")
            else:
                print("✓ Synced with remote")
            
            self.repo_path = local_repo_path
    
    def _get_authenticated_url(self, git_url: str) -> str:
        """Embed auth token in Git URL."""
        if "https://git@" in git_url:
            return git_url.replace(
                "https://git@",
                f"https://git:{self.auth_token}@"
            )
        elif "https://" in git_url:
            return git_url.replace(
                "https://",
                f"https://{self.auth_token}@"
            )
        else:
            return git_url

    def push_to_overleaf(
        self,
        commit_message: str = "Update from python_tex_tools",
        var_file_name: str = "python_results.tex",
        force_overwrite: bool = False
    ):
        """Push changes to Overleaf with conflict protection.
        
        WORKFLOW:
        - Blocks updates if the generated file was modified by someone else
        - Only proceeds if file doesn't exist on remote (deleted = green light)
          or if we were the last ones to modify it
        - This prevents overwriting supervisor's manual edits
        
        SUPERVISOR HANDOFF:
        When supervisor is done reviewing/editing, they delete the generated
        file from Overleaf to signal "ready for automated updates again"
        
        Args:
            commit_message: Git commit message
            var_file_name: The generated file to protect from conflicts
            force_overwrite: If True, skip conflict check and force push
                           (dangerous - overwrites supervisor's edits!)
        """
        if not hasattr(self, "repo_path"):
            raise ValueError(
                "No Overleaf repository registered. "
                "Please call register_overleaf() first."
            )

        print(f"Pushing changes to Overleaf repository at {self.repo_path}...")
        
        # Fetch latest remote changes
        print("Fetching remote changes...")
        subprocess.run(
            ['git', 'fetch', 'origin'],
            cwd=self.repo_path,
            check=True
        )
        
        # Check if the generated file was modified remotely
        if not force_overwrite and self._check_remote_file_conflict(var_file_name):
            conflict_info = getattr(self, '_conflict_info', {})
            author_name = conflict_info.get('author_name', 'Unknown')
            author_email = conflict_info.get('author_email', '')
            time_ago = conflict_info.get('time_ago', 'recently')
            commit_msg = conflict_info.get('commit_msg', 'No message')
            
            author_display = f"{author_name} <{author_email}>" if author_email else author_name
            
            # Print the detailed message to console
            print(f"\n{'='*60}")
            print(f"🛑 UPDATES BLOCKED - FILE LOCKED BY SUPERVISOR\n")
            print(f"The file '{var_file_name}' was last modified by:")
            print(f"  👤 {author_display}")
            print(f"  📅 {time_ago}")
            print(f"  💬 {commit_msg}\n")
            print(f"WORKFLOW:")
            print(f"1. Your supervisor is reviewing/editing numbers in Overleaf")
            print(f"2. When they're done, they should DELETE '{var_file_name}'")
            print(f"   from the Overleaf project (via web interface)")
            print(f"3. This signals: 'Ready for automated updates again'")
            print(f"4. Re-run your script - it will push successfully\n")
            print(f"WHY THIS APPROACH?")
            print(f"- Prevents accidentally overwriting supervisor's edits")
            print(f"- Explicit handoff: deletion = permission to proceed")
            print(f"- Your numbers stay fresh, their reviews stay safe\n")
            print(f"TO VIEW THEIR CHANGES:")
            print(f"Check the Overleaf web interface before they delete\n")
            print(f"TO FORCE OVERWRITE (dangerous!):")
            print(f"Re-run with: export(force_overwrite=True)")
            print(f"{'='*60}\n")
            
            raise RuntimeError(
                f"Push blocked: '{var_file_name}' was modified by {author_name}"
            )
        
        # If force overwrite, reset to remote first (overwrite their changes)
        if force_overwrite:
            print("⚠ Force overwrite enabled - discarding remote changes!")
            # Get current branch
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = result.stdout.strip()
            
            # Reset to match remote exactly (discards any differences)
            subprocess.run(
                ['git', 'reset', '--hard', f'origin/{current_branch}'],
                cwd=self.repo_path,
                check=True
            )
            print(f"  Reset local to match origin/{current_branch}")
        
        # Git add
        subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)
        
        # Git commit with user identifier
        result = subprocess.run(
            ['git', 'commit', '-m', f"{commit_message} [{self.user_identifier}]"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0 and "nothing to commit" not in result.stdout:
            print(f"Git commit output: {result.stdout}")
            print(f"Git commit error: {result.stderr}")
        
        # Update remote URL to include auth token
        authenticated_url = self._get_authenticated_url(self.git_repo_url)
        subprocess.run(
            ['git', 'remote', 'set-url', 'origin', authenticated_url],
            cwd=self.repo_path,
            check=True
        )
        
        # Git push with automatic handling of non-fast-forward errors
        result = subprocess.run(
            ['git', 'push'],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        # Handle non-fast-forward errors automatically
        if result.returncode != 0:
            if "non-fast-forward" in result.stderr or "rejected" in result.stderr:
                print("⚠ Non-fast-forward error detected - handling automatically...")
                
                # Pull with rebase to integrate remote changes, then push
                # Note: Overleaf doesn't support --force, so we always use rebase
                print("  Pulling remote changes with rebase...")
                pull_result = subprocess.run(
                    ['git', 'pull', '--rebase'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                
                if pull_result.returncode != 0:
                    print(f"Git pull output: {pull_result.stdout}")
                    print(f"Git pull error: {pull_result.stderr}")
                    raise RuntimeError(f"Git pull --rebase failed: {pull_result.stderr}")
                
                print("  Retrying push...")
                result = subprocess.run(
                    ['git', 'push'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"Git push output: {result.stdout}")
                    print(f"Git push error: {result.stderr}")
                    raise RuntimeError(f"Git push failed after rebase: {result.stderr}")
            else:
                # Other git error
                print(f"Git push output: {result.stdout}")
                print(f"Git push error: {result.stderr}")
                raise RuntimeError(f"Git push failed: {result.stderr}")
        
        print("✓ Successfully pushed to Overleaf!")
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    
    def _check_remote_file_conflict(self, filename: str) -> bool:
        """Check if generated file was modified by someone else on remote.
        
        Returns True if file exists remotely and was last touched by someone else.
        Only allows updates if:
        - File doesn't exist on remote (supervisor deleted it = green light)
        - File was last modified by us (we own it)
        """
        # Get current branch
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        current_branch = result.stdout.strip()
        
        # Check if file exists on remote
        result = subprocess.run(
            ['git', 'ls-tree', f'origin/{current_branch}', '--', filename],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        # If file doesn't exist on remote, allow push
        if not result.stdout.strip():
            print(f"✓ File '{filename}' not on remote - ready for update")
            return False
        
        # File exists on remote - check who last modified it
        result = subprocess.run(
            ['git', 'log', f'origin/{current_branch}', '-1',
             '--pretty=format:%s||%an||%ae||%ar', '--', filename],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            parts = result.stdout.strip().split('||')
            last_commit_msg = parts[0] if len(parts) > 0 else ''
            author_name = parts[1] if len(parts) > 1 else 'Unknown'
            author_email = parts[2] if len(parts) > 2 else ''
            time_ago = parts[3] if len(parts) > 3 else ''
            
            # Store for error message
            self._conflict_info = {
                'author_name': author_name,
                'author_email': author_email,
                'commit_msg': last_commit_msg,
                'time_ago': time_ago
            }
            
            # If last commit wasn't from us, it's a conflict
            if self.user_identifier not in last_commit_msg:
                print(f"⚠ Warning: Remote file was modified by someone else")
                print(f"  Author: {author_name} <{author_email}>")
                print(f"  When: {time_ago}")
                print(f"  Commit: {last_commit_msg}")
                return True
        
        # File exists but we last modified it - OK to update
        print(f"✓ File '{filename}' was last modified by us - OK to update")
        return False

    def add_var(self, name, value, unit_name=""):
        self.check_name_consistency(name)
        if not isinstance(value, str):
            value = str(value)  # Try to convert to string if it is not
        if unit_name == "":
            # apply as number
            value = "\\num{" + value + "}"

        if not unit_name == "":
            value = "\\SI{" + value + "}{" + unit_name + "}"

        self.var_list.append([name, value])
        if self.verbose:
            print(f"New Variable: \\{self.var_function_prefix}{name}")

    def add_figure(self, name: str, figure: plt.figure):
        if TIKZPLOTLIB_AVAILABLE:
            self.add_figure_tikzplotlib(name, figure)
        else:
            # raise NotImplementedError("tikzplotlib is not available.")
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
        """_summary_

        Args:
            name (str): The Name to be used.
            table (pd.DataFrame): A Table with the Information. Index and Columns will be used.
            print_best_values_bf (bool, optional): Weather to print the best values bold in LaTex export. Defaults to True.
            bf_options (dict, optional): Specifications on what to print bold (Details in source code). Defaults to None.
        """
        self.check_name_consistency(name)
        
            # check, if df is a pandas dataframe
        if not isinstance(table, pd.DataFrame):
            raise ValueError("The input table is not a pandas DataFrame.")
        
        bf_default_options = {
            "axis": 0, # 0 best in columns, 1 best in rows
            "higher_or_lower_is_better": "higher", # could als be an array like ["higher", "lower", "higher", "lower"] with the same length as the number of columns/ rows in the table
        }
        
        if bf_options is not None:
            for key, value in bf_options.items():
                if key not in bf_default_options:
                    raise ValueError(
                        f"Unsupported key {key}. Supported Keys are: {bf_default_options.keys()}"
                    )
                bf_default_options[key] = value
        
        if print_best_values_bf:
            table = print_best_values_fat(table, **bf_default_options)
        
        table_code = table.to_latex(escape=False)

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

    def export(
        self,
        export_path=".",
        var_file_name="python_results.tex",
        force_overwrite=False
    ):
        """Export all variables, figures, and tables to LaTeX file.
        
        If Overleaf is registered, automatically pushes to remote with
        conflict protection. Updates are blocked if the generated file
        was modified by someone else. Supervisor should delete the file
        on Overleaf to signal "ready for automated updates again."
        
        Args:
            export_path: Directory to export to (overridden if Overleaf registered)
            var_file_name: Name of the generated LaTeX file
            force_overwrite: If True, force push to Overleaf even if conflicts exist
                           (dangerous - overwrites others' edits!)
        """
        if hasattr(self, "repo_path"):
            export_path = self.repo_path
            print(
                f"Overleaf remote repository registered. "
                f"Exporting to {export_path}..."
            )

        export_path = Path(export_path).resolve()
        var_file_path = os.path.join(export_path, var_file_name)

        print("Writing output to %s" % var_file_path)
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

        if hasattr(self, "repo_path"):
            print("")
            print("Export complete. Pushing to overleaf.")
            self.push_to_overleaf(
                var_file_name=var_file_name,
                force_overwrite=force_overwrite
            )
        
    def __del__(self):
        # remove the temporary directory
        shutil.rmtree(self.tmp_dir)
