import pandas as pd

def expand_col(df, col_name, func=None):
    """
    for every entry in column "col_name" a new row in the dataframe is produced. The index is kept (i.e. it results in
    all rows having the same index which belonged together)

    if a default func is given, it should return a

    Parameters
    ----------
    df : pandas.DataFrame
    col_name : str
    func : function
        must return pandas.Series object

    Returns
    -------
    new dataframe with column expanded
    """
    if func is None:
        func = pd.Series
    expanded_col = df[col_name].apply(func).stack().reset_index(1, drop=True).to_frame(col_name)
    # del df[col_name]  # fast inplace hopefully, but this is changing df which is not expected
    df = df.drop(col_name, 1)
    return df.join(expanded_col)