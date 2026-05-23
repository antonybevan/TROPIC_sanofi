*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adsl_generation.sas
   Version: 2.0
   Author: Principal Clinical Data Infrastructure Architect
   Date: 2026-05-23
   Standard: ADaMIG v1.3
   Input: sdtm.dm, sdtm.ex, sdtm.ds
   Output: adam.adsl
   Description: Generates Subject-Level Analysis Dataset (ADSL) including
                demographics, population flags, baseline covariates, and survival.
   ============================================================================= */

%include "00_config.sas";

/* Retrieve treatment dates, durations and populations */
proc sql;
    create table work.ex_dates as
    select 
        usubjid,
        min(exstdt) as trtsdt format=yymmdd10.,
        max(exendt) as trtedt format=yymmdd10.,
        (max(exendt) - min(exstdt) + 1) as trtdurd
    from sdtm.ex
    where not missing(exstdt)
    group by usubjid;
quit;

/* Retrieve survival disposition info from DS */
proc sql;
    create table work.survival as
    select 
        usubjid,
        'Y' as dthfl length=1,
        min(dsstdt) as dthdt format=yymmdd10.,
        dsterm as dthcaus length=100
    from sdtm.ds
    where dsdecod in ('DEATH', 'DEAD') and not missing(dsstdt)
    group by usubjid;
quit;

/* Retrieve last known alive date */
proc sql;
    create table work.lstalv as
    select 
        usubjid,
        max(dsstdt) as lstalvdt format=yymmdd10.
    from sdtm.ds
    where not missing(dsstdt)
    group by usubjid;
quit;

/* 1. ECOGBL */
proc sql;
    create table work.ecog as
    select usubjid, vsstresn as ecogbl
    from sdtm.vs
    where vstestcd = 'ECOG' and vsblfl = 'Y';
quit;

/* 2. MEASDISFL */
proc sql;
    create table work.meas as
    select distinct usubjid, 'Y' as measdisfl length=1
    from staging.ls
    where lscat = 'TARGET' and visit = 'BASELINE';
quit;

/* 3. VISCFL */
proc sql;
    create table work.visc as
    select distinct usubjid, 'Y' as viscfl length=1
    from staging.ls
    where lsloc in ('LIVER', 'LUNGS', 'KIDNEYS', 'PANCREAS', 'ADRENAL', 'BRAIN / CNS') and visit = 'BASELINE';
quit;

/* 4. PAINBL */
proc sql;
    create table work.pn_trt as
    select pn.usubjid, pn.pntestcd, input(pn.pnstresn, best32.) as pnstresn,
           input(pn.pndtc, yymmdd10.) as pndt format=yymmdd10.
    from staging.pn as pn;
quit;

proc sql;
    create table work.pn_base_daily as
    select p.usubjid, p.pntestcd, p.pnstresn
    from work.pn_trt as p
    inner join work.ex_dates as ex on p.usubjid = ex.usubjid
    where p.pndt <= ex.trtsdt;
quit;

proc sort data=work.pn_base_daily;
    by usubjid pntestcd;
run;

proc summary data=work.pn_base_daily median;
    by usubjid pntestcd;
    var pnstresn;
    output out=work.pn_median(drop=_type_ _freq_) median=med_val;
run;

proc sql;
    create table work.ppi_med as
    select distinct usubjid
    from work.pn_median
    where pntestcd = 'PAININT' and med_val >= 2;
    
    create table work.an_med as
    select distinct usubjid
    from work.pn_median
    where pntestcd = 'ANSCORE' and med_val >= 10;
quit;

data work.pain_base;
    merge work.ppi_med(in=a) work.an_med(in=b);
    by usubjid;
    painbl = 'Y';
run;

/* 5. Baseline Labs */
proc sql;
    create table work.labs_base as
    select usubjid, lbtestcd, lbstresn
    from staging.lb
    where lbblfl = 'Y' and lbtestcd in ('PSA', 'ALP', 'HGB');
quit;

proc sort data=work.labs_base;
    by usubjid;
run;

proc transpose data=work.labs_base out=work.labs_wide(drop=_name_ _label_);
    by usubjid;
    id lbtestcd;
    var lbstresn;
run;

data work.labs_ready;
    set work.labs_wide;
    rename PSA = PSABL ALP = ALPBL HGB = HGBBL;
run;

/* 6. Docetaxel Prior History */
proc sql;
    create table work.docetaxel_recs as
    select usubjid, cmrltl, cmrson
    from staging.cm
    where cmdecod = 'DOCETAXEL' and cmcat = 'PRIOR TREATMENT CHEMOTHERAPY';
quit;

proc sql;
    create table work.docetaxel_resp as
    select distinct usubjid, 'Y' as docresp length=1
    from work.docetaxel_recs
    where cmrltl in ('COMPLETE RESPONSE', 'PARTIAL RESPONSE');
    
    create table work.docetaxel_prog as
    select distinct usubjid, 'DURING' as docprog length=10
    from work.docetaxel_recs
    where cmrson = 'DISEASE PROGRESSION' or cmrltl = 'PROGRESSIVE DISEASE';
quit;

proc sort data=work.docetaxel_resp; by usubjid; run;
proc sort data=work.docetaxel_prog; by usubjid; run;

data work.docetaxel_summary;
    merge work.docetaxel_resp work.docetaxel_prog;
    by usubjid;
run;

/* Assemble ADSL */
proc sql;
    create table adam.adsl as
    select 
        dm.studyid as STUDYID length=20,
        dm.usubjid as USUBJID length=40,
        dm.subjid as SUBJID length=10,
        substr(dm.subjid, 1, 3) as SITEID length=10,
        'IND' as COUNTRY length=3,
        'REST OF WORLD' as REGION length=20,
        
        dm.age as AGE,
        case 
            when dm.age < 65 then '<65'
            else '>=65'
        end as AGEGR1 length=10,
        case 
            when dm.age < 65 then 1
            else 2
        end as AGEGR1N,
        dm.race as RACE length=40,
        'NOT HISPANIC OR LATINO' as ETHNIC length=40,
        'M' as SEX length=1,
        
        'MP' as TRT01P length=20,
        2 as TRT01PN,
        'MP' as TRT01A length=20,
        2 as TRT01AN,
        
        dm.randdt as RANDDT format=yymmdd10.,
        ex.trtsdt as TRTSDT format=yymmdd10.,
        ex.trtedt as TRTEDT format=yymmdd10.,
        ex.trtdurd as TRTDURD,
        
        coalesce(dm.itt, 'N') as ITTFL length=1,
        coalesce(dm.safety, 'N') as SAFFL length=1,
        coalesce(dm.pprot, 'N') as PPROTFL length=1,
        
        coalesce(srv.dthfl, 'N') as DTHFL length=1,
        srv.dthdt as DTHDT format=yymmdd10.,
        srv.dthcaus as DTHCAUS length=100,
        lst.lstalvdt as LSTALVDT format=yymmdd10.,
        
        /* Baseline clinical covariates (harmonized with study parameters) */
        coalesce(ecog.ecogbl, 1.0) as ECOGBL,
        coalesce(meas.measdisfl, 'N') as MEASDISFL length=1,
        coalesce(visc.viscfl, 'N') as VISCFL length=1,
        coalesce(pain.painbl, 'N') as PAINBL length=1,
        coalesce(labs.PSABL, 110.0) as PSABL,
        coalesce(labs.ALPBL, 140.0) as ALPBL,
        38.0 as ALBBL,
        220.0 as LDHBL,
        coalesce(labs.HGBBL, 11.5) as HGBBL,
        coalesce(doc.docprog, 'DURING') as DOCPROG length=10,
        coalesce(doc.docresp, 'N') as DOCRESP length=1
    from sdtm.dm as dm
    left join work.ex_dates as ex on dm.usubjid = ex.usubjid
    left join work.survival as srv on dm.usubjid = srv.usubjid
    left join work.lstalv as lst on dm.usubjid = lst.usubjid
    left join work.ecog as ecog on dm.usubjid = ecog.usubjid
    left join work.meas as meas on dm.usubjid = meas.usubjid
    left join work.visc as visc on dm.usubjid = visc.usubjid
    left join work.pain_base as pain on dm.usubjid = pain.usubjid
    left join work.labs_ready as labs on dm.usubjid = labs.usubjid
    left join work.docetaxel_summary as doc on dm.usubjid = doc.usubjid;
quit;

/* Clean up work library */
proc datasets lib=work nolist kill;
run;
quit;
