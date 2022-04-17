-- define table schemas before seeding
drop table if exists risk_high;
create table risk_high (
	  loan_id                              int
	, accountoriginationyear               int
	, activeflag                           int
	, borrowerincome                       int
	, creditcardtype                       int
	, currentcreditlimit                   int
	, cycleendingbalance                   int
	, cycleendingretailapr                 float
	, dayspastdue                          int
	, monthendclosedrevokedflag            int
	, originalcreditlimit                  int
	, producttype                          int
	, refreshedcreditscoreprimaryborrower  int
);

drop table if exists risk_typical;
create table risk_typical (
	  loan_id                              int
	, accountoriginationyear               int
	, activeflag                           int
	, borrowerincome                       int
	, creditcardtype                       int
	, currentcreditlimit                   int
	, cycleendingbalance                   int
	, cycleendingretailapr                 float
	, dayspastdue                          int
	, monthendclosedrevokedflag            int
	, originalcreditlimit                  int
	, producttype                          int
	, refreshedcreditscoreprimaryborrower  int
);

drop table if exists risk_low;
create table risk_low (
	  loan_id                              int
	, accountoriginationyear               int
	, activeflag                           int
	, borrowerincome                       int
	, creditcardtype                       int
	, currentcreditlimit                   int
	, cycleendingbalance                   int
	, cycleendingretailapr                 float
	, dayspastdue                          int
	, monthendclosedrevokedflag            int
	, originalcreditlimit                  int
	, producttype                          int
	, refreshedcreditscoreprimaryborrower  int
);


-- union all 3 tables
drop table if exists data_unioned;
create table data_unioned as
select *, 'high'    as risk_level from risk_high
    union all
select *, 'typical' as risk_level from risk_typical
    union all
select *, 'low'     as risk_level from risk_low
;

select * from  data_unioned;


-- perform all renamings and binnings
drop table if exists base_table;
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
        else 'EXCEPTION' end as cycleendingbalance_bin
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
        when cycleendingretailapr <  12     then 'Under 12%'
        when cycleendingretailapr <= 14.99  then '12%-14.99%'
        when cycleendingretailapr <= 19.99  then '15%-19.99%'
        when cycleendingretailapr <  24     then '20%-23.99%'  -- fill gap
        when cycleendingretailapr >= 24     then '24% and over'
        else 'EXCEPTION' end as cycleendingretailapr
from data_unioned
;

-- queries
	-- potential shortcut
	-- select distinct risk_level, creditcardtype, sum(cycleendingbalance) over(partition by risk_level, creditcardtype) from base_table

-- repeat this for each variable. cntrl-h it
-- 1
drop table if exists bin_creditcardtype;
create table bin_creditcardtype as
with high as
	(
	select creditcardtype
		, 100.0 * sum(cycleendingbalance) / 
		(select sum(cycleendingbalance) from base_table where risk_level = 'high') as amount
	from base_table where risk_level = 'high'
	group by 1 order by 1
	)
, typical as
	(
	select creditcardtype
		, 100.0 * sum(cycleendingbalance) / 
		(select sum(cycleendingbalance) from base_table where risk_level = 'typical') as amount
	from base_table where risk_level = 'typical'
	group by 1 order by 1
	)
, low as
	(
	select creditcardtype
		, 100.0 * sum(cycleendingbalance) / 
		(select sum(cycleendingbalance) from base_table where risk_level = 'low') as amount
	from base_table where risk_level = 'low'
	group by 1 order by 1
	)
select
	'creditcardtype' 		as metric
	, a.creditcardtype
	, round(c.amount, 2)	as Lower_risk
	, round(b.amount, 2)	as Typical
	, round(a.amount, 2)	as Higher_risk
from high a
left join typical b
	on a.creditcardtype = b.creditcardtype
left join low c
	on a.creditcardtype = c.creditcardtype
;

-- 2. simple cntrl-h replace keyword
drop table if exists bin_currentcreditlimit;
create table bin_currentcreditlimit as
with high as
	(
	select currentcreditlimit
		, 100.0 * sum(cycleendingbalance) / 
		(select sum(cycleendingbalance) from base_table where risk_level = 'high') as amount
	from base_table where risk_level = 'high'
	group by 1 order by 1
	)
, typical as
	(
	select currentcreditlimit
		, 100.0 * sum(cycleendingbalance) / 
		(select sum(cycleendingbalance) from base_table where risk_level = 'typical') as amount
	from base_table where risk_level = 'typical'
	group by 1 order by 1
	)
, low as
	(
	select currentcreditlimit
		, 100.0 * sum(cycleendingbalance) / 
		(select sum(cycleendingbalance) from base_table where risk_level = 'low') as amount
	from base_table where risk_level = 'low'
	group by 1 order by 1
	)
select
	'currentcreditlimit' 	as metric
	, a.currentcreditlimit
	, round(c.amount, 2)	as Lower_risk
	, round(b.amount, 2)	as Typical
	, round(a.amount, 2)	as Higher_risk
from high a
left join typical b
	on a.currentcreditlimit = b.currentcreditlimit
left join low c
	on a.currentcreditlimit = c.currentcreditlimit
;

-- combine all variables
select * from bin_creditcardtype
	union all
select * from bin_currentcreditlimit
;

-- repeat and you are good.
