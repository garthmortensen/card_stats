# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 15:44:26 2022

@author: garth.mortensen
  _        _    _       ________
 | |_ __ _| |__| |___  |__ /__  |
 |  _/ _` | '_ \ / -_)  |_ \ / /
  \__\__,_|_.__/_\___| |_gm//_/

Possible improvements:
- merge group_categorical() and group_numeric() into one function
- create list of all columns and loop grouping functions
- carve out functions into .py and import them for reuse/readability
- replace df.append() with pd.concat()
"""

# %%

import os
import pandas as pd
import numpy as np
import warnings  # for supressing FutureWarning

# The frame.append method is deprecated and will be removed from pandas in a future version. Use pandas.concat instead.
warnings.simplefilter(action='ignore', category=FutureWarning)


def replace_ints(df):
    """Input base dataframe to perform replacement operations on"""

    grouping_var = "creditcardtype"
    df[grouping_var] = df[grouping_var].replace(1, 'General purpose')
    df[grouping_var] = df[grouping_var].replace(2, 'Private label')

    grouping_var = "producttype"
    df[grouping_var] = df[grouping_var].replace(1, 'Co-brand')
    df[grouping_var] = df[grouping_var].replace(2, 'Other')

    grouping_var = "activeflag"
    df[grouping_var] = df[grouping_var].replace(0, 'Open and active')
    df[grouping_var] = df[grouping_var].replace(1, 'Other')

    grouping_var = "monthendclosedrevokedflag"
    df[grouping_var] = df[grouping_var].replace(0, 'Not closed')
    df[grouping_var] = df[grouping_var].replace(1, 'Closed')

    return df


def create_bins(df):
    """ Create bins for numeric columns, according to Table 37
    use np.where, since it handles both Int and Str

    EXCEPTION category catches any values missed by the np.where clauses.

    source: https://www.statology.org/case-statement-pandas/
    """

    grouping_var = "currentcreditlimit"
    df[f"{grouping_var}_bins"] = np.where(df[grouping_var] <= 1500, '$1,500 and less',
                                 np.where(df[grouping_var] <= 7500, '$1,501-$7,500',
                                 np.where(df[grouping_var] > 7500, 'Over $7,500',
                                 'EXCEPTION')))

    grouping_var = "dayspastdue"
    df[f"{grouping_var}_bins"] = np.where(df[grouping_var] <= 30, 'Current',
                                 np.where(df[grouping_var] > 30, '30+ Days past due',
                                 'EXCEPTION'))

    grouping_var = "accountoriginationyear"
    df[f"{grouping_var}_bins"] = np.where(df[grouping_var] <= 2016, '2016 and prior',
                                  np.where(df[grouping_var] == 2017, '2017',
                                  np.where(df[grouping_var] == 2018, '2018',
                                  np.where(df[grouping_var] == 2019, '2019',
                                  np.where(df[grouping_var] == 2020, '2020',
                                  'EXCEPTION')))))

    grouping_var = "cycleendingbalance"
    df[f"{grouping_var}_bins"] = np.where(df[grouping_var] <= 1000, 'Under $1,000',
                                 np.where(df[grouping_var] <= 1999, '$1,000-$1,999',
                                 np.where(df[grouping_var] <= 2999, '$2,000-$2,999',
                                 np.where(df[grouping_var] <= 4999, '$3,000-$4,999',
                                 np.where(df[grouping_var] < 10000, '$5,000-$9,999',  # fill gap
                                 np.where(df[grouping_var] >= 10000, '$10,000 and over',
                                 'EXCEPTION'))))))

    grouping_var = "borrowerincome"
    df[f"{grouping_var}_bins"] = np.where(df[grouping_var] <= 50000, '$50,000 and less',
                                 np.where(df[grouping_var] <= 100000, '$50,001-$100,000',
                                 np.where(df[grouping_var] > 100000, 'Over $100,000',
                                 'EXCEPTION')))

    grouping_var = "originalcreditlimit"  # same as currentcreditlimit
    df[f"{grouping_var}_bins"] = np.where(df[grouping_var] <= 1500, '$1,500 and less',
                                 np.where(df[grouping_var] <= 7500, '$1,501-$7,500',
                                 np.where(df[grouping_var] > 7500, 'Over $7,500',
                                 'EXCEPTION')))

    grouping_var = "cycleendingretailapr"
    df[f"{grouping_var}_bins"] = np.where(df[grouping_var] < 12, 'Under 12%',
                                 np.where(df[grouping_var] <= 14.99, '12%-14.99%',
                                 np.where(df[grouping_var] <= 19.99, '15%-19.99%',
                                 np.where(df[grouping_var] < 24, '20%-23.99%',  # fill gap
                                 np.where(df[grouping_var] >= 24, '24% and over',
                                 'EXCEPTION')))))

    return df


def group_categorical(df_base, df, grouping_var):
    """Define categorical column, and provide original database (df) and ouput dataframe"""

    df_grouped = df.groupby([grouping_var]).sum()
    df_grouped[f"{grouping_var}_%"] = (df_grouped['cycleendingbalance'] / df_grouped['cycleendingbalance'].sum()) * 100
    df_grouped = df_grouped[[f"{grouping_var}_%"]]
    df_grouped = df_grouped.reset_index()

    new_row = pd.DataFrame({grouping_var: grouping_var}, index=[0])  # define header row for df
    df_grouped = pd.concat([new_row, df_grouped[:]]).reset_index(drop=True)  # insert row
    df_grouped.columns = ['Variable', '% share cycle ending balance']

    df_base.append(df_grouped)
    df_base = pd.concat([df_base, df_grouped])

    return df_base


def group_numeric(df_base, df, grouping_var):
    """Define numeric column, and provide original database (df) and ouput dataframe"""

    df_grouped = df.groupby([f"{grouping_var}_bins"]).sum()
    df_grouped[f"{grouping_var}_%"] = (df_grouped['cycleendingbalance'] / df_grouped['cycleendingbalance'].sum()) * 100
    df_grouped = df_grouped[[f"{grouping_var}_%"]]
    df_grouped = df_grouped.reset_index()

    new_row = pd.DataFrame({f"{grouping_var}_bins": grouping_var}, index=[0])  # define header row for df
    df_grouped = pd.concat([new_row, df_grouped[:]]).reset_index(drop=True)  # insert row
    df_grouped.columns = ['Variable', '% share cycle ending balance']

    df_base.append(df_grouped)
    df_base = pd.concat([df_base, df_grouped])

    return df_base


# =============================================================================
# process the data
# datapath_low = os.path.join(dir_py, "data", "input", "cards-low-risk-2022.csv")
# =============================================================================

# OS agnostic directory pointers
dir_py = os.path.dirname(__file__)
data_out = os.path.join(dir_py, "data", "output")
# data_in = os.path.join(dir_py, "data", "input_backup")

urls = [
        "https://www.federalreserve.gov/supervisionreg/files/cards-high-risk-2022.csv",
        "https://www.federalreserve.gov/supervisionreg/files/cards-typical-risk-2022.csv",
        "https://www.federalreserve.gov/supervisionreg/files/cards-low-risk-2022.csv",
        ]

i = 0
all_files = []
for url in urls:
    i += 1

    df = pd.read_csv(url)

    file = url.split('/files/')[1]
    filename = file.split('.csv')[0]
    print(f"file {i}: {file}")
    risk_level =  filename.split('-')[1]  # grab low/typical/high for header

    df = replace_ints(df)
    df = create_bins(df)

    # define empty df for appending to
    df_base = pd.DataFrame(columns=['Variable', '% share cycle ending balance'])

    # follow order found in Table 37
    # looping would be overkill
    # print(df.dtypes)  # determine each column datatype

    # 01
    grouping_var = "creditcardtype"
    df_base = group_categorical(df_base, df, grouping_var)

    # 02
    grouping_var = "currentcreditlimit"
    df_base = group_numeric(df_base, df, grouping_var)

    # 03
    grouping_var = "dayspastdue"
    df_base = group_numeric(df_base, df, grouping_var)

    # 04
    grouping_var = "producttype"
    df_base = group_categorical(df_base, df, grouping_var)

    # 05
    grouping_var = "activeflag"
    df_base = group_categorical(df_base, df, grouping_var)

    # 06
    grouping_var = "accountoriginationyear"
    df_base = group_numeric(df_base, df, grouping_var)

    # 07
    grouping_var = "monthendclosedrevokedflag"
    df_base = group_categorical(df_base, df, grouping_var)

    # 08
    grouping_var = "cycleendingbalance"
    df_base = group_numeric(df_base, df, grouping_var)

    # 09
    grouping_var = "borrowerincome"
    df_base = group_numeric(df_base, df, grouping_var)

    # 10
    grouping_var = "originalcreditlimit"
    df_base = group_numeric(df_base, df, grouping_var)

    # 11
    grouping_var = "cycleendingretailapr"
    df_base = group_numeric(df_base, df, grouping_var)

    # rename columns before write
    columns = ['Variable', risk_level]
    df_base.columns = columns

    df_base.to_csv(f"{data_out}/{filename}-processed.csv", index=False)
    df_base.to_html(f"{data_out}/{filename}-processed.html", index=False)
    print(f"saved to: {data_out}/{filename}-processed.csv")

# %%

# df1 = pd.read_csv(f"{data_out}/cards-low-risk-2022-processed.csv")
# df2 = pd.read_csv(f"{data_out}/cards-typical-risk-2022-processed.csv")
# df3 = pd.read_csv(f"{data_out}/cards-high-risk-2022-processed.csv")

# df_all = pd.merge(df3, df1, how='left', on='Variable')
"""ISSUE
cartesian product appears dye to e.g. 'Over $7,500' appearing in several groups
I can't resolve this without refactoring, which would likely exceed time limit.
"""

# df_all.to_html(f"{data_out}/Table_37.html", index=False)


