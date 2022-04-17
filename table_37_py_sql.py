# -*- coding: utf-8 -*-
"""
Created on Sun Apr 17 11:19:34 2022

@author: garth.mortensen
 __________                             _ 
|___ /___  |  _ __  _   _     ___  __ _| |
  |_ \  / /  | '_ \| | | |   / __|/ _` | |
 ___) |/ /   | |_) | |_| |   \__ \ (_| | |
|____//_/____| .__/ \__, |___|___/\gm, |_|
       |_____|_|    |___/_____|      |_|  
       
Remade with python and sql, for db benefits.
"""

# %%

import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
import os  # for loading env variables
from dotenv import load_dotenv  # for loading env variables. pip install python-dotenv

# read db creds without hardcoding (github safe)
home = Path.home() / ".env"
load_dotenv(home)
creds = {
    "POSTGRES_USER": os.getenv("postgres_user"),
    "POSTGRES_PASS": os.getenv("postgres_pass"),
}

engine = create_engine(f"postgresql://{creds['POSTGRES_USER']}:{creds['POSTGRES_PASS']}@localhost:5432/table_exercise")

# write csv files out here
dir_py = os.path.dirname(__file__)
data_out = os.path.join(dir_py, "data", "output_sql")

# %%

# after inserting .csv into 3 tables in pgadmin, union them
table = "data_unioned"
query_drop = f"drop table if exists {table}"
query_create = \
    f"""
    create table {table} as
    select *, 'high'    as risk_level from risk_high
        union all
    select *, 'typical' as risk_level from risk_typical
        union all
    select *, 'low'     as risk_level from risk_low
    ;
    """

engine.execute(query_drop)
engine.execute(query_create)

query_select = f"select * from {table}"
df = pd.read_sql(query_select, con=engine)

# %%

# seeing what its like to import a large .sql query, to avoid clutter
table = "base_table"
query_drop = f"drop table if exists {table}"
with open(dir_py + '/query_case_when.sql', 'r') as file:
    lines = file.readlines()
query_case = ''.join(lines)

engine.execute(query_drop)
engine.execute(query_case)

query_select = f"select * from {table}"
df = pd.read_sql(query_select, con=engine)
# reading .sql isnt so bad

# %%

# avoid rewriting same query many times...
# ...by looping through all variables
variables = [
            "creditcardtype",
            "currentcreditlimit",
            "dayspastdue",
            "producttype",
            "activeflag",
            "accountoriginationyear",
            "monthendclosedrevokedflag",
            "cycleendingbalance_grouped",  # column renamed
            "borrowerincome",
            "originalcreditlimit",
            "cycleendingretailapr",    
            ]

# create binned tables for each
# theres probably a shorter sql window function for this
for variable in variables:
    query_drop = f"drop table if exists bin_{variable}"
    query_long = \
        f"""
        create table bin_{variable} as
        with high as
        	(
        	select {variable}
        		, 100.0 * sum(cycleendingbalance) / 
        		(select sum(cycleendingbalance) from base_table where risk_level = 'high') as amount
        	from base_table where risk_level = 'high'
        	group by 1 order by 1
        	)
        , typical as
        	(
        	select {variable}
        		, 100.0 * sum(cycleendingbalance) / 
        		(select sum(cycleendingbalance) from base_table where risk_level = 'typical') as amount
        	from base_table where risk_level = 'typical'
        	group by 1 order by 1
        	)
        , low as
        	(
        	select {variable}
        		, 100.0 * sum(cycleendingbalance) / 
        		(select sum(cycleendingbalance) from base_table where risk_level = 'low') as amount
        	from base_table where risk_level = 'low'
        	group by 1 order by 1
        	)
        select
        	'{variable}' 		    as metric
        	, a.{variable}
        	, round(c.amount, 2)	as Lower_risk
        	, round(b.amount, 2)	as Typical
        	, round(a.amount, 2)	as Higher_risk
        from high a
        left join typical b
        	on a.{variable} = b.{variable}
        left join low c
        	on a.{variable} = c.{variable}
        """

    engine.execute(query_drop)
    engine.execute(query_long)
    
    query_select = f"select * from bin_{variable}"
    df = pd.read_sql(query_select, con=engine)
    df.to_csv(data_out + f"/bin_{variable}.csv", index=False)  # archive

# %%

# add union all to all variables, except for last
table = "final_table"
query_drop = f"drop table if exists {table}"

all_unions = []
for variable in variables[:-1]:
	union = \
        f"""
        select * from bin_{variable} 
        union all
        """
	all_unions.append(union)

# add final touches to query
query_union = ''.join(all_unions)
query_union = f"create table {table} as {query_union} select * from bin_cycleendingretailapr"

engine.execute(query_drop)
engine.execute(query_union)

# %%

# archive results
query_select = f"select * from {table}"
df = pd.read_sql(query_select, con=engine)
df.to_csv(data_out + f"/{table}.csv", index=False)
