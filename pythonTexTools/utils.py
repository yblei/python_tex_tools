import pandas as pd
import re


def regex_get_digits_only(input: str):   
    # raise error if input is not a string
    if not isinstance(input, str):
        return input
    
    n = re.sub(r'[^0-9.]','', input)
    
    # raise error when empty
    if n == "":
        raise ValueError(f"The input string {input} does not contain any parsable digits.")
    
    return n

def print_best_values_fat(df: pd.DataFrame, axis:int = 0, higher_or_lower_is_better:str| list[str] = "higher"):
    # latex symbols for arrow up/ down
    tex_up = r"($\uparrow$)"
    tex_down = r"($\downarrow$)"
    
    # deepcopy the dataframe
    df_numerical_only = df.copy()
    
    # caset the dataframe to string only
    df = df.astype(str)
    
    # remove all non numerical values from the dataframe
    df_numerical_only = df_numerical_only.map(regex_get_digits_only)
    
    # if higher_or_lower_is_better is a string, convert it to a list of the same lenght as the dimension
    if isinstance(higher_or_lower_is_better, str):
        higher_or_lower_is_better = [higher_or_lower_is_better for _ in range(df_numerical_only.shape[axis])]
        
    # check if the length of the higher_or_lower_is_better list is the same as the number of columns/ rows in the table
    if len(higher_or_lower_is_better) != df_numerical_only.shape[axis]:
        raise ValueError(f"The length of the higher_or_lower_is_better list ({len(higher_or_lower_is_better)}) does not match the number of columns/ rows in the table ({df_numerical_only.shape[axis]}).")
    
    # add the up/ down arrows to the entries in the rows/ columns names
    if axis == 0:
        entries = df.columns
    elif axis == 1:
        entries = df.index
    else:
        raise ValueError("The axis parameter must be either 0 or 1.")
    
    entries_out = []
    for higher_or_lower, entry in zip(higher_or_lower_is_better, entries):
        if higher_or_lower == "higher":
            entries_out.append(f"{entry} {tex_up}")
        elif higher_or_lower == "lower":
            entries_out.append(f"{entry} {tex_down}")
        else:
            raise ValueError(f"The value {higher_or_lower} is not a valid value for the higher_or_lower_is_better parameter. It must be either 'higher' or 'lower'.")
        
    if axis == 0:
        df.columns = entries_out
    elif axis == 1:
        df.index = entries_out 
        
        
    # get the index of the best value in each row/ column
    highest_values = df_numerical_only.idxmax(axis=axis)
    lowest_values = df_numerical_only.idxmin(axis=axis)
    
    # print the best values in bold with \textbf{}
    for i, (highest_value, lowest_value, higher_or_lower) in enumerate(zip(highest_values, lowest_values, higher_or_lower_is_better)):
        if axis == 0:
            if higher_or_lower == "higher":
                df.loc[highest_value, df.columns[i]] = f"\\textbf{{{df.loc[highest_value, df.columns[i]]}}}"
            elif higher_or_lower == "lower":
                df.loc[lowest_value, df.columns[i]] = f"\\textbf{{{df.loc[lowest_value, df.columns[i]]}}}"
        elif axis == 1:
            if higher_or_lower == "higher":
                df.loc[df.index[i], highest_value] = f"\\textbf{{{df.loc[df.index[i], highest_value]}}}"
            elif higher_or_lower == "lower":
                df.loc[df.index[i], lowest_value] = f"\\textbf{{{df.loc[df.index[i], lowest_value]}}}"
    
    return df