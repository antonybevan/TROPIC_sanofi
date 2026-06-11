*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adlb_generation.sas
   Version: 2.2.0
   Author: Principal Clinical Data Infrastructure Architect
   Date: 2026-05-27
   Standard: ADaMIG v1.3 BDS
   Input: sdtm.lb, adam.adsl
   Output: adam.adlb
   Description: Generates Laboratory BDS ADaM (ADLB) with analysis windowing, Worst
                Analysis flag (ANL01FL), and Project Optimus parameters.
   ============================================================================= */

/* PGMDIR guard: allows standalone execution (CWD=02_production_sas) and IOM/ODA mode.
   Wrapped in a macro for portability (open-code %IF requires 9.4M5+). */
%macro set_pgmdir;
    %if not %symexist(PGMDIR) %then %global PGMDIR;
    %if "&PGMDIR." = "" %then %let PGMDIR = .;
%mend set_pgmdir;
%set_pgmdir;
%include "&PGMDIR./00_config.sas";

proc sql;
    /* Create base dataset merging LB and ADSL */
    create table work.lb_base as
    select 
        adsl.studyid,
        adsl.usubjid,
        adsl.subjid as SUBJID length=10,
        adsl.trt01p,
        adsl.trtsdt,
        lb.visit,
        lb.visitnum,
        lb.lbseq,
        lb.lbtestcd as PARAMCD length=8,
        lb.lbtest as PARAM length=40,
        case 
            when lb.lbtestcd = 'NEUT' then 1
            when lb.lbtestcd = 'PSA' then 2
            when lb.lbtestcd = 'HGB' then 3
            else 4
        end as PARAMN,
        case 
            when lb.lbtestcd = 'PSA' then 'TUMOR MARKER'
            else 'HEMATOLOGY'
        end as PARCAT1 length=20,
        lb.lbdt as ADT format=yymmdd10.,
        lb.lbdy as ADY,
        lb.lbstresn as AVAL,
        lb.lborres as AVALC length=20,
        lb.lbornrlo as lbnrlo,
        lb.lbornrhi as lbnrhi,
        lb.lbnrind,
        coalesce(input(lb.lbtoxgr, best32.), 0.0) as ATOXGR
    from sdtm.lb as lb
    left join adam.adsl as adsl on lb.usubjid = adsl.usubjid
    where adsl.saffl = 'Y' and not missing(lb.lbstresn);
quit;

/* Assign Analysis Windows */
data work.lb_windows;
    set work.lb_base;
    
    length AVISIT $40;
    
    if ADY <= 0 then do;
        AVISITN = 0;
        AVISIT = 'Baseline';
        AWDIST = abs(ADY - (-1));
    end;
    else if 1 <= ADY <= 3 then do;
        AVISITN = 1;
        AVISIT = 'Cycle 1 Day 1 Pre-dose';
        AWDIST = abs(ADY - 1);
    end;
    else if 4 <= ADY <= 13 then do;
        AVISITN = 2;
        AVISIT = 'Cycle 1 Day 8';
        AWDIST = abs(ADY - 8);
    end;
    else if 14 <= ADY <= 17 then do;
        AVISITN = 3;
        AVISIT = 'Cycle 1 Day 15';
        AWDIST = abs(ADY - 15);
    end;
    else if 18 <= ADY <= 24 then do;
        AVISITN = 4;
        AVISIT = 'Cycle 2 Day 1 Pre-dose';
        AWDIST = abs(ADY - 22);
    end;
    else if 25 <= ADY <= 34 then do;
        AVISITN = 5;
        AVISIT = 'Cycle 2 Day 8';
        AWDIST = abs(ADY - 29);
    end;
    else if 39 <= ADY <= 45 then do;
        AVISITN = 6;
        AVISIT = 'Cycle 3 Day 1 Pre-dose';
        AWDIST = abs(ADY - 43);
    end;
    else do;
        AVISITN = 99;
        AVISIT = 'Unscheduled';
        AWDIST = .;
    end;
run;

/* Resolve Baseline values - stable sorting keeps first baseline record */
proc sort data=work.lb_windows out=work.lb_base_pre;
    by usubjid PARAMCD descending ADT lbseq;
    where AVISITN = 0;
run;

data work.baselines;
    set work.lb_base_pre;
    by usubjid PARAMCD;
    if first.PARAMCD;
    BASE = AVAL;
    BASEC = AVALC;
    BTOXGR = ATOXGR;
    keep usubjid PARAMCD BASE BASEC BTOXGR;
run;

/* Merge Baseline information */
proc sql;
    create table work.lb_base_merged as
    select 
        w.*,
        b.BASE,
        b.BASEC,
        b.BTOXGR,
        case when not missing(b.BASE) then (w.AVAL - b.BASE) else . end as CHG,
        case when not missing(b.BASE) and b.BASE > 0 then ((w.AVAL - b.BASE) / b.BASE) * 100 else . end as PCHG
    from work.lb_windows as w
    left join work.baselines as b on w.usubjid = b.usubjid and w.PARAMCD = b.PARAMCD;
quit;

/* Sort to determine ANL01FL Worst-Case / Closest-to-target selection */
proc sort data=work.lb_base_merged;
    by usubjid PARAMCD AVISITN AWDIST descending ATOXGR ADT lbseq;
run;

/* Derive ANL01FL and BASEFL */
data work.lb_anl01;
    set work.lb_base_merged;
    by usubjid PARAMCD AVISITN;
    
    length ANL01FL BASEFL $1;
    
    /* Set ANL01FL Worst Flag */
    if not missing(AVISITN) and AVISITN ne 99 then do;
        if first.AVISITN then ANL01FL = 'Y';
        else ANL01FL = 'N';
    end;
    else do;
        ANL01FL = 'N';
    end;
    
    /* Set BASEFL Baseline Flag */
    if AVISITN = 0 then BASEFL = 'Y';
    else BASEFL = 'N';
run;

/* Add Project Optimus continuous parameters: ANCNADIR, ANCRECDY */
/* 1. Calculate ANC Nadir per subject per cycle */
data work.anc_records;
    set work.lb_anl01;
    where PARAMCD = 'NEUT' and ADY > 0 and ANL01FL = 'Y';
    if ADY < 18 then cycle = 1;
    else if 18 <= ADY and ADY < 39 then cycle = 2;
    else if 39 <= ADY then cycle = 3;
run;

proc sql;
    /* Step 1: Compute minimum AVAL per subject/cycle */
    create table work.anc_nadir_val as
    select 
        usubjid,
        cycle,
        min(AVAL) as nadir_val
    from work.anc_records
    group by usubjid, cycle;

    /* Step 2: Get the minimum ADY corresponding to the minimum AVAL */
    create table work.anc_nadir_summary as
    select 
        r.usubjid,
        r.cycle,
        v.nadir_val,
        min(r.ADY) as nadir_dy
    from work.anc_records as r
    inner join work.anc_nadir_val as v on r.usubjid = v.usubjid and r.cycle = v.cycle and r.AVAL = v.nadir_val
    group by r.usubjid, r.cycle, v.nadir_val;
quit;

/* 2. Calculate ANC recovery days per cycle */
proc sql;
    create table work.anc_recovery as
    select 
        r.usubjid,
        r.cycle,
        min(r.ADY) as rec_dy
    from work.anc_records as r
    inner join work.anc_nadir_summary as n on r.usubjid = n.usubjid and r.cycle = n.cycle
    where r.ADY > n.nadir_dy and r.AVAL >= 1.5
    group by r.usubjid, r.cycle;
quit;

/* Format Project Optimus derived BDS parameters */
proc sql;
    create table work.optimus_nadir as
    select 
        adsl.studyid,
        n.usubjid,
        adsl.subjid,
        adsl.trt01p,
        adsl.trtsdt,
        'ANCNADIR' as PARAMCD length=8,
        'ANC Nadir Value (x10^3/uL)' as PARAM length=40,
        'OPTIMUS KINETICS' as PARCAT1 length=20,
        catx(' ', 'CYCLE', put(n.cycle, 2.)) as AVISIT length=40,
        n.cycle as AVISITN,
        n.nadir_val as AVAL,
        strip(put(n.nadir_val, 8.2)) as AVALC length=20,
        'Y' as ANL01FL length=1,
        'N' as BASEFL length=1,
        n.nadir_dy as lbdy
    from work.anc_nadir_summary as n
    left join adam.adsl as adsl on n.usubjid = adsl.usubjid;

    create table work.optimus_rec as
    select 
        adsl.studyid,
        r.usubjid,
        adsl.subjid,
        adsl.trt01p,
        adsl.trtsdt,
        'ANCRECDY' as PARAMCD length=8,
        'Days from ANC Nadir to Recovery' as PARAM length=40,
        'OPTIMUS KINETICS' as PARCAT1 length=20,
        catx(' ', 'CYCLE', put(r.cycle, 2.)) as AVISIT length=40,
        r.cycle as AVISITN,
        (r.rec_dy - n.nadir_dy) as AVAL,
        strip(put((r.rec_dy - n.nadir_dy), 8.0)) as AVALC length=20,
        'Y' as ANL01FL length=1,
        'N' as BASEFL length=1,
        r.rec_dy as lbdy
    from work.anc_recovery as r
    inner join work.anc_nadir_summary as n on r.usubjid = n.usubjid and r.cycle = n.cycle
    left join adam.adsl as adsl on r.usubjid = adsl.usubjid;
quit;

/* Combine base and derived Optimus kinetics */
data adam.adlb(keep=STUDYID USUBJID SUBJID TRT01P TRTSDT PARAMCD PARAM PARAMN PARCAT1 AVAL AVALC LBNRLO LBNRHI LBNRIND AVISIT AVISITN AWDIST ATOXGR BASE BASEC BTOXGR CHG PCHG ANL01FL BASEFL LBDY);
    set work.lb_anl01(rename=(ADY=LBDY)) work.optimus_nadir work.optimus_rec;
run;

proc sort data=adam.adlb;
    by usubjid PARAMCD AVISITN lbdy;
run;

/* Clean up work library */
proc datasets lib=work nolist kill;
run;
quit;
