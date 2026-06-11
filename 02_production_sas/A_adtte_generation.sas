*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adtte_generation.sas
   Version: 2.2.0
   Author: Principal Clinical Data Infrastructure Architect
   Date: 2026-05-27
   Standard: ADaMIG v1.3 / CDISC BDS TTE v1.0
   Input: adam.adsl, adam.adrs, adam.adcm, adam.adae
   Output: adam.adtte
   Description: Time-to-Event ADaM (ADTTE) with standard censoring (CNSR=0/1) for
                Overall Survival (OS), Progression-Free Survival (PFS),
                and Time to First Serious AE (TTOS).
   ============================================================================= */

/* PGMDIR guard: allows standalone execution (CWD=02_production_sas) and IOM/ODA mode.
   Wrapped in a macro for portability (open-code %IF requires 9.4M5+). */
%macro set_pgmdir;
    %if not %symexist(PGMDIR) %then %global PGMDIR;
    %if "&PGMDIR." = "" %then %let PGMDIR = .;
%mend set_pgmdir;
%set_pgmdir;
%include "&PGMDIR./00_config.sas";

/* 1. Retrieve first PD date per subject across all source domains */
proc sql;
    create table work.pd_dates as
    select 
        usubjid,
        min(ADT) as pd_dt format=yymmdd10.
    from adam.adrs
    where (PARAMCD = 'OVRLRESP' and AVALC = 'PD') or 
          (PARAMCD = 'BSGRESP' and AVALC = 'PROGRESSION') or
          (PARAMCD = 'PSPROG' and AVALC = 'Y')
    group by usubjid;
quit;

/* Retrieve first Serious AE date per subject */
proc sql;
    create table work.sae_dates as
    select 
        usubjid,
        min(astdt) as sae_dt format=yymmdd10.
    from adam.adae
    where aeser = 'Y' and trtemfl = 'Y'
    group by usubjid;
quit;

/* Assemble OS and TTOS Parameters */
proc sql;
    create table work.os_ttos_raw as
    select 
        adsl.*,
        sae.sae_dt
    from adam.adsl(keep=studyid usubjid subjid siteid trt01p trt01pn saffl randdt trtsdt trtedt dthfl dthdt lstalvdt) as adsl
    left join work.sae_dates as sae on adsl.usubjid = sae.usubjid
    where adsl.saffl = 'Y';
quit;

data work.tte_base;
    set work.os_ttos_raw;
    
    length PARAMCD $8 PARAM $40 EVNTDESC CNSDTDSC $100;
    format ADT STARTDT format yymmdd10. AVAL CNSR 8.2;
    
    /* -------------------------------------------------------------------------- */
    /* PARAMETER 1: OVERALL SURVIVAL                                             */
    /* -------------------------------------------------------------------------- */
    PARAMCD = 'OS';
    PARAM = 'Overall Survival';
    STARTDT = RANDDT;
    
    if dthfl = 'Y' then do;
        ADT = dthdt;
        CNSR = 0;
        EVNTDESC = 'DEATH';
        CNSDTDSC = '';
    end;
    else do;
        ADT = lstalvdt;
        CNSR = 1;
        EVNTDESC = '';
        CNSDTDSC = 'LAST KNOWN ALIVE DATE';
    end;
    
    if ADT < STARTDT then ADT = STARTDT;
    AVAL = ADT - STARTDT + 1;
    output;
    
    /* -------------------------------------------------------------------------- */
    /* PARAMETER 2: TIME TO FIRST SERIOUS AE (TTOS)                              */
    /* -------------------------------------------------------------------------- */
    PARAMCD = 'TTOS';
    PARAM = 'Time to First Serious AE';
    STARTDT = TRTSDT;
    
    if not missing(sae_dt) then do;
        ADT = sae_dt;
        CNSR = 0;
        EVNTDESC = 'SERIOUS ADVERSE EVENT';
        CNSDTDSC = '';
    end;
    else do;
        ADT = lstalvdt;
        CNSR = 1;
        EVNTDESC = '';
        CNSDTDSC = 'LAST CONCOMITANT EVALUATION';
    end;
    
    if ADT < STARTDT then ADT = STARTDT;
    AVAL = ADT - STARTDT + 1;
    output;
run;

/* Add PFS parameter which has a more complex censoring hierarchy */
proc sql;
    create table work.nact_mapping as
    select usubjid, min(nactdt) as nactdt format=yymmdd10.
    from adam.adcm
    where not missing(nactdt)
    group by usubjid;
quit;

proc sql;
    create table work.pfs_raw as
    select 
        adsl.*,
        pd.pd_dt,
        nact.nactdt
    from adam.adsl(keep=studyid usubjid subjid siteid trt01p trt01pn saffl randdt dthfl dthdt lstalvdt) as adsl
    left join work.pd_dates as pd on adsl.usubjid = pd.usubjid
    left join work.nact_mapping as nact on adsl.usubjid = nact.usubjid
    where adsl.saffl = 'Y';
quit;

data work.pfs_derived;
    set work.pfs_raw;
    
    length PARAMCD $8 PARAM $40 EVNTDESC CNSDTDSC $100;
    format ADT STARTDT format yymmdd10. AVAL CNSR 8.2;
    
    PARAMCD = 'PFS';
    PARAM = 'Progression Free Survival';
    STARTDT = randdt;
    
    _pd_found = not missing(pd_dt);
    _nact_found = not missing(nactdt);
    
    /* Hierarchy rule checking */
    if _pd_found then do;
        /* PD event occurred */
        if _nact_found and nactdt < pd_dt then do;
            /* Censor: New therapy started BEFORE progression */
            ADT = nactdt - 1;
            CNSR = 1;
            EVNTDESC = '';
            CNSDTDSC = 'NEW ANTI-CANCER THERAPY START';
        end;
        else do;
            /* Event: Progression */
            ADT = pd_dt;
            CNSR = 0;
            EVNTDESC = 'TUMOR OR PSA PROGRESSION';
            CNSDTDSC = '';
        end;
    end;
    else if dthfl = 'Y' then do;
        /* PD did not occur but subject died */
        if _nact_found and nactdt < dthdt then do;
            /* Censor: New therapy before death */
            ADT = nactdt - 1;
            CNSR = 1;
            EVNTDESC = '';
            CNSDTDSC = 'NEW ANTI-CANCER THERAPY START';
        end;
        else do;
            /* Event: Death */
            ADT = dthdt;
            CNSR = 0;
            EVNTDESC = 'DEATH';
            CNSDTDSC = '';
        end;
    end;
    else do;
        /* Censor: No event, censor at last alive */
        if _nact_found then do;
            ADT = nactdt - 1;
            CNSR = 1;
            EVNTDESC = '';
            CNSDTDSC = 'NEW ANTI-CANCER THERAPY START';
        end;
        else do;
            ADT = lstalvdt;
            CNSR = 1;
            EVNTDESC = '';
            CNSDTDSC = 'LAST EVALUABLE TUMOR ASSESSMENT';
        end;
    end;
    
    if ADT < STARTDT then ADT = STARTDT;
    AVAL = ADT - STARTDT + 1;
    output;
run;

/* -------------------------------------------------------------------------- */
/* PARAMETER 4: TIME TO PAIN PROGRESSION (TTPAIN)                             */
/* -------------------------------------------------------------------------- */
proc sql;
    create table work.pn_trt_tte as
    select pn.usubjid, pn.pntestcd, pn.pnstresn,
           input(pn.pndtc, yymmdd10.) as pndt format=yymmdd10.,
           pn.visit, pn.visitnum,
           adsl.trtsdt, adsl.randdt
    from staging.pn as pn
    inner join adam.adsl as adsl on pn.usubjid = adsl.usubjid;
quit;

proc sql;
    create table work.pn_base_tte as
    select usubjid, pntestcd, pnstresn
    from work.pn_trt_tte
    where not missing(pndt) and pndt <= trtsdt;
quit;

proc sort data=work.pn_base_tte;
    by usubjid pntestcd;
run;

proc summary data=work.pn_base_tte median;
    by usubjid pntestcd;
    var pnstresn;
    output out=work.pn_base_med(drop=_type_ _freq_) median=base_val;
run;

proc sort data=work.pn_base_med;
    by usubjid;
run;

proc transpose data=work.pn_base_med out=work.pn_base_wide(drop=_name_ _label_);
    by usubjid;
    id pntestcd;
    var base_val;
run;

data work.pn_base_final;
    set work.pn_base_wide;
    base_ppi = coalesce(PAININT, 0);
    base_an = coalesce(ANSCORE, 0);
    drop PAININT ANSCORE;
run;

proc sql;
    create table work.pn_post_daily as
    select usubjid, visitnum, visit, pntestcd, pnstresn, pndt
    from work.pn_trt_tte
    where pndt > trtsdt;
quit;

proc sort data=work.pn_post_daily;
    by usubjid visitnum visit pndt pntestcd;
run;

proc sql;
    create table work.pn_first_day as
    select usubjid, visitnum, visit, pndt, pntestcd, min(pnstresn) as day_val
    from work.pn_post_daily
    group by usubjid, visitnum, visit, pndt, pntestcd;
quit;

proc sort data=work.pn_first_day;
    by usubjid visitnum visit pntestcd;
run;

proc summary data=work.pn_first_day median;
    by usubjid visitnum visit pntestcd;
    var day_val;
    output out=work.pn_cycle_med(drop=_type_ _freq_) median=cycle_val;
run;

data work.pn_cycle_med;
    set work.pn_cycle_med;
    label cycle_val = 'Cycle Value';
run;

proc sql;
    create table work.pn_cycle_min_date as
    select usubjid, visitnum, visit, min(pndt) as cycle_date format=yymmdd10.
    from work.pn_post_daily
    group by usubjid, visitnum, visit;
quit;

proc sort data=work.pn_cycle_med;
    by usubjid visitnum visit;
run;

proc transpose data=work.pn_cycle_med out=work.pn_cycle_wide(drop=_name_ _label_);
    by usubjid visitnum visit;
    id pntestcd;
    var cycle_val;
run;

proc sort data=work.pn_cycle_wide; by usubjid visitnum visit; run;
proc sort data=work.pn_cycle_min_date; by usubjid visitnum visit; run;
proc sort data=work.pn_base_final; by usubjid; run;

proc sql;
    create table work.cycle_comp_raw as
    select w.usubjid, w.visitnum, w.visit, d.cycle_date,
           w.PAININT as cycle_ppi, w.ANSCORE as cycle_an,
           b.base_ppi, b.base_an
    from work.pn_cycle_wide as w
    left join work.pn_cycle_min_date as d on w.usubjid = d.usubjid and w.visitnum = d.visitnum and w.visit = d.visit
    left join work.pn_base_final as b on w.usubjid = b.usubjid;
quit;

proc sort data=work.cycle_comp_raw;
    by usubjid visitnum;
run;

data work.cycle_comp;
    set work.cycle_comp_raw;
    by usubjid visitnum;
    
    _b_ppi = coalesce(base_ppi, 0);
    _b_an = coalesce(base_an, 0);
    
    ppi_diff = cycle_ppi - _b_ppi;
    an_diff = cycle_an - _b_an;
    
    if (not missing(ppi_diff) and ppi_diff >= 2) or (not missing(an_diff) and an_diff >= 10) then prog_trigger = 1;
    else prog_trigger = 0;
run;

/* Sustained confirmation: trigger confirmed if NEXT consecutive visit also triggers,
   OR if the triggered visit is the last observation for that subject.
   Uses PROC SQL self-join to emulate R lead()-based look-ahead. */
proc sql;
    /* Step 1: Find the minimum visitnum of the next trigger visit per subject */
    create table work.confirmed_triggers as
    select a.usubjid, a.visitnum as trig_visitnum, a.cycle_date as trig_date
    from work.cycle_comp as a
    where a.prog_trigger = 1
    and (
        /* Next consecutive visit also triggers (confirmed pair) */
        exists (
            select 1 from work.cycle_comp as b
            where b.usubjid = a.usubjid
              and b.prog_trigger = 1
              and b.visitnum = (select min(c.visitnum)
                                from work.cycle_comp as c
                                where c.usubjid = a.usubjid and c.visitnum > a.visitnum)
        )
        or
        /* OR this is the last observation for the subject (terminal trigger) */
        a.visitnum = (select max(d.visitnum) from work.cycle_comp as d where d.usubjid = a.usubjid)
    );
quit;

proc sql;
    /* Step 2: Earliest confirmed trigger date per subject = pain progression date */
    create table work.prog_dates as
    select usubjid, min(trig_date) as prog_date format=yymmdd10.
    from work.confirmed_triggers
    group by usubjid;
quit;

proc sql;
    create table work.censor_dates as
    select usubjid, max(pndt) as last_pn_dt format=yymmdd10.
    from work.pn_trt_tte
    group by usubjid;
quit;

proc sql;
    create table work.ttpain_derived as
    select 
        adsl.studyid as STUDYID length=20,
        adsl.usubjid as USUBJID length=40,
        adsl.subjid as SUBJID length=10,
        adsl.siteid as SITEID length=10,
        adsl.trt01p as TRT01P length=20,
        adsl.trt01pn as TRT01PN,
        'TTPAIN' as PARAMCD length=8,
        'Time to Pain Progression' as PARAM length=40,
        adsl.randdt as STARTDT format=yymmdd10.,
        
        case 
            when not missing(p.prog_date) then p.prog_date
            when not missing(c.last_pn_dt) then c.last_pn_dt
            else adsl.randdt
        end as ADT format=yymmdd10.,
        
        case 
            when not missing(p.prog_date) then 0
            else 1
        end as CNSR,
        
        case 
            when not missing(p.prog_date) then 'PAIN PROGRESSION'
            else ''
        end as EVNTDESC length=100,
        
        case 
            when not missing(p.prog_date) then ''
            when not missing(c.last_pn_dt) then 'LAST PAIN ASSESSMENT DATE'
            else 'NO PAIN ASSESSMENT'
        end as CNSDTDSC length=100
    from adam.adsl as adsl
    left join work.prog_dates as p on adsl.usubjid = p.usubjid
    left join work.censor_dates as c on adsl.usubjid = c.usubjid
    where adsl.saffl = 'Y';
quit;

data work.ttpain_final;
    set work.ttpain_derived;
    if ADT < STARTDT then ADT = STARTDT;
    AVAL = ADT - STARTDT + 1;
run;

/* -------------------------------------------------------------------------- */
/* PARAMETER 5: TIME TO PSA PROGRESSION (TTPSA)                              */
/* -------------------------------------------------------------------------- */
proc sql;
    create table work.psa_prog_dates as
    select usubjid, ADT as psa_prog_dt
    from adam.adrs
    where PARAMCD = 'PSPROG' and AVALC = 'Y';
quit;

proc sql;
    create table work.psa_censor_dates as
    select usubjid, max(lbdt) as last_psa_dt format=yymmdd10.
    from sdtm.lb
    where lbtestcd = 'PSA' and not missing(lbstresn)
    group by usubjid;
quit;

proc sql;
    create table work.ttpsa_derived as
    select 
        adsl.studyid as STUDYID length=20,
        adsl.usubjid as USUBJID length=40,
        adsl.subjid as SUBJID length=10,
        adsl.siteid as SITEID length=10,
        adsl.trt01p as TRT01P length=20,
        adsl.trt01pn as TRT01PN,
        'TTPSA' as PARAMCD length=8,
        'Time to PSA Progression' as PARAM length=40,
        adsl.trtsdt as STARTDT format=yymmdd10.,
        
        case 
            when not missing(p.psa_prog_dt) then p.psa_prog_dt
            when not missing(c.last_psa_dt) then min(c.last_psa_dt, '25SEP2009'd)
            else min(adsl.lstalvdt, '25SEP2009'd)
        end as ADT format=yymmdd10.,
        
        case 
            when not missing(p.psa_prog_dt) then 0
            else 1
        end as CNSR,
        
        case 
            when not missing(p.psa_prog_dt) then 'PSA PROGRESSION'
            else ''
        end as EVNTDESC length=100,
        
        case 
            when not missing(p.psa_prog_dt) then ''
            when not missing(c.last_psa_dt) then 'LAST PSA ASSESSMENT'
            else 'LAST KNOWN ALIVE DATE'
        end as CNSDTDSC length=100
    from adam.adsl as adsl
    left join work.psa_prog_dates as p on adsl.usubjid = p.usubjid
    left join work.psa_censor_dates as c on adsl.usubjid = c.usubjid
    where adsl.saffl = 'Y';
quit;

data work.ttpsa_final;
    set work.ttpsa_derived;
    if ADT < STARTDT then ADT = STARTDT;
    AVAL = ADT - STARTDT + 1;
run;

/* -------------------------------------------------------------------------- */
/* PARAMETER 6: TIME TO TUMOR PROGRESSION (TTUMOR)                           */
/* -------------------------------------------------------------------------- */
proc sql;
    create table work.tumor_prog_dates as
    select usubjid, min(ADT) as tumor_prog_dt format=yymmdd10.
    from adam.adrs
    where PARAMCD = 'OVRLRESP' and AVALC = 'PD'
    group by usubjid;
quit;

proc sql;
    create table work.tumor_censor_dates as
    select usubjid, max(ADT) as last_tumor_dt format=yymmdd10.
    from adam.adrs
    where PARAMCD = 'OVRLRESP' and not missing(ADT)
    group by usubjid;
quit;

proc sql;
    create table work.ttum_derived as
    select 
        adsl.studyid as STUDYID length=20,
        adsl.usubjid as USUBJID length=40,
        adsl.subjid as SUBJID length=10,
        adsl.siteid as SITEID length=10,
        adsl.trt01p as TRT01P length=20,
        adsl.trt01pn as TRT01PN,
        'TTUMOR' as PARAMCD length=8,
        'Time to Tumor Progression' as PARAM length=40,
        adsl.trtsdt as STARTDT format=yymmdd10.,
        
        case 
            when not missing(p.tumor_prog_dt) then p.tumor_prog_dt
            when not missing(c.last_tumor_dt) then min(c.last_tumor_dt, '25SEP2009'd)
            else adsl.trtsdt
        end as ADT format=yymmdd10.,
        
        case 
            when not missing(p.tumor_prog_dt) then 0
            else 1
        end as CNSR,
        
        case 
            when not missing(p.tumor_prog_dt) then 'TUMOR PROGRESSION'
            else ''
        end as EVNTDESC length=100,
        
        case 
            when not missing(p.tumor_prog_dt) then ''
            when not missing(c.last_tumor_dt) then 'LAST TUMOR ASSESSMENT'
            else 'NO POST-BASELINE ASSESSMENT'
        end as CNSDTDSC length=100
    from adam.adsl as adsl
    left join work.tumor_prog_dates as p on adsl.usubjid = p.usubjid
    left join work.tumor_censor_dates as c on adsl.usubjid = c.usubjid
    where adsl.saffl = 'Y' and adsl.measdisf = 'Y';
quit;

data work.ttum_final;
    set work.ttum_derived;
    if ADT < STARTDT then ADT = STARTDT;
    AVAL = ADT - STARTDT + 1;
run;

/* Combine TTE parameters */
data adam.adtte(keep=STUDYID USUBJID SUBJID SITEID TRT01P TRT01PN PARAMCD PARAM STARTDT ADT AVAL CNSR EVNTDESC CNSDTDSC);
    set work.tte_base work.pfs_derived work.ttpain_final work.ttpsa_final work.ttum_final;
run;

proc sort data=adam.adtte;
    by usubjid PARAMCD;
run;

/* Clean up work library */
proc datasets lib=work nolist kill;
run;
quit;
