create table base_table as
select
      risk_level
    , cycleendingbalance
    , case 
        when creditcardtype = 1             then 'General purpose'
        when creditcardtype = 2             then 'Private label'
        else 'EXCEPTION' end as creditcardtype
    , case 
        when producttype = 1                then 'Co-brand'
        when producttype = 2                then 'Other'
        else 'EXCEPTION' end as producttype
    , case 
        when activeflag = 0                 then 'Open and active'
        when activeflag = 1                 then 'Other'
        else 'EXCEPTION' end as activeflag
    , case 
        when monthendclosedrevokedflag = 0  then 'Not closed'
        when monthendclosedrevokedflag = 1  then 'Closed'
        else 'EXCEPTION' end as monthendclosedrevokedflag
    , case 
        when currentcreditlimit <= 1500     then '$1,500 and less'
        when currentcreditlimit <= 7500     then '$1,501-$7,500'
        when currentcreditlimit >  7500     then 'Over $7,500'
        else 'EXCEPTION' end as currentcreditlimit
    , case 
        when dayspastdue <= 30              then 'Current'
        when dayspastdue >  30              then '30+ Days past due'
        else 'EXCEPTION' end as dayspastdue
    , case 
        when accountoriginationyear <= 2016 then '2016 and prior'
        when accountoriginationyear =  2017 then '2017'
        when accountoriginationyear =  2018 then '2018'
        when accountoriginationyear =  2019 then '2019'
        when accountoriginationyear =  2020 then '2020'
        else 'EXCEPTION' end as accountoriginationyear
    , case 
        when cycleendingbalance <= 1000     then 'Under $1,000'
        when cycleendingbalance <= 1999     then '$1,000-$1,999'
        when cycleendingbalance <= 2999     then '$2,000-$2,999'
        when cycleendingbalance <= 4999     then '$3,000-$4,999'
        when cycleendingbalance <  10000    then '$5,000-$9,999' -- fill gap
        when cycleendingbalance >= 10000    then '$10,000 and over'
        else 'EXCEPTION' end as cycleendingbalance_grouped -- rename field
    , case 
        when borrowerincome <= 50000        then '$50,000 and less'
        when borrowerincome <= 100000       then '$50,001-$100,000'
        when borrowerincome >  100000       then 'Over $100,000'
        else 'EXCEPTION' end as borrowerincome
    , case 
        when originalcreditlimit <= 1500    then '$1,500 and less'
        when originalcreditlimit <= 7500    then '$1,501-$7,500'
        when originalcreditlimit >  7500    then 'Over $7,500'
        else 'EXCEPTION' end as originalcreditlimit
    , case 
        when cycleendingretailapr <  12     then 'Under 12pct'
        when cycleendingretailapr <= 14.99  then '12pct-14.99pct'
        when cycleendingretailapr <= 19.99  then '15pct-19.99pct'
        when cycleendingretailapr <  24     then '20pct-23.99pct'  -- fill gap
        when cycleendingretailapr >= 24     then '24pct and over'
        else 'EXCEPTION' end as cycleendingretailapr
from data_unioned
