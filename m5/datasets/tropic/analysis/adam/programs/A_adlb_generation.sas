*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adlb_generation.sas
   Version: 2.2.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-05-27
   Standard: ADaMIG v1.3 BDS
   Input: sdtm.lb, adam.adsl
   Output: adam.adlb
   Description: Generates Laboratory BDS ADaM (ADLB) with analysis windowing, Worst
                Analysis flag (ANL01FL), and Project Optimus parameters.
   ============================================================================= */

/* PGMDIR guard: define only when running standalone; master driver pre-defines this. */
%if not %sysmacexist(set_pgmdir) %then %do;
    %macro set_pgmdir;
        %if not %symexist(PGMDIR) %then %global PGMDIR;
        %if "&PGMDIR." = "" %then %let PGMDIR = .;
    %mend set_pgmdir;
%end;
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
        /* PARAMN is assigned 1:1 over the full PARAMCD set at the end of the program (audit F-02);
           the old NEUT/PSA/HGB/else=4 scheme collided across analytes and left ANCNADIR/ANCRECDY unset. */
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
        input(lb.lbtoxgr, best32.) as ATOXGR
    from sdtm.lb as lb
    left join adam.adsl as adsl on lb.usubjid = adsl.usubjid
    where adsl.saffl = 'Y' and not missing(lb.lbstresn);
quit;

/* Assign Analysis Windows */
data work.lb_windows;
    set work.lb_base;
    
    length AVISIT $40;
    
    if ADY <= &W_BL_HI. then do;
        AVISITN = 0;
        AVISIT = 'Baseline';
        /* Missing ADY sorts into Baseline (. <= W_BL_HI); guard the distance calc so
           it does not emit a "missing values generated" NOTE. AWDIST stays missing,
           the window classification above is unchanged. */
        if not missing(ADY) then AWDIST = abs(ADY - (-1));
    end;
    else if &W_C1D1_LO. <= ADY <= &W_C1D1_HI. then do;
        AVISITN = 1;
        AVISIT = 'Cycle 1 Day 1 Pre-dose';
        AWDIST = abs(ADY - 1);
    end;
    else if &W_C1D8_LO. <= ADY <= &W_C1D8_HI. then do;
        AVISITN = 2;
        AVISIT = 'Cycle 1 Day 8';
        AWDIST = abs(ADY - 8);
    end;
    else if &W_C1D15_LO. <= ADY <= &W_C1D15_HI. then do;
        AVISITN = 3;
        AVISIT = 'Cycle 1 Day 15';
        AWDIST = abs(ADY - 15);
    end;
    else if &W_C2D1_LO. <= ADY <= &W_C2D1_HI. then do;
        AVISITN = 4;
        AVISIT = 'Cycle 2 Day 1 Pre-dose';
        AWDIST = abs(ADY - 22);
    end;
    else if &W_C2D8_LO. <= ADY <= &W_C2D8_HI. then do;
        AVISITN = 5;
        AVISIT = 'Cycle 2 Day 8';
        AWDIST = abs(ADY - 29);
    end;
    else if &W_C3D1_LO. <= ADY <= &W_C3D1_HI. then do;
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
    where r.ADY > n.nadir_dy and r.AVAL >= &ANC_RECOVERY_THRESHOLD.
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

/* Combine base and derived Optimus kinetics.
   ADT (analysis date) is carried so downstream ADaM (e.g. ADTTE PSA-progression
   censoring) can source the last PSA assessment date from ADLB rather than reaching
   back into raw SDTM/staging (traceability, roadmap #3). Derived Optimus rows have
   no single assessment date and carry ADT missing. */
data work.adlb_all(keep=STUDYID USUBJID SUBJID TRT01P TRTSDT PARAMCD PARAM PARCAT1 ADT
                        AVAL AVALC LBNRLO LBNRHI LBNRIND AVISIT AVISITN AWDIST ATOXGR BASE BASEC
                        BTOXGR CHG PCHG ANL01FL BASEFL LBDY);
    set work.lb_anl01(rename=(ADY=LBDY)) work.optimus_nadir work.optimus_rec;
    format ADT yymmdd10.;
run;

/* Deterministic 1:1 PARAMN over the sorted distinct PARAMCD set (audit F-02). Replaces the old
   NEUT/PSA/HGB/else=4 scheme (collided across analytes; ANCNADIR/ANCRECDY unset). The sort is
   ASCII-ascending on the uppercase PARAMCD tokens, identical to the R track's
   distinct(PARAMCD) |> arrange(PARAMCD) |> row_number(). */
proc sort data=work.adlb_all out=work._pc(keep=PARAMCD) nodupkey;
    by PARAMCD;
run;
data work._pnmap;
    set work._pc;
    PARAMN = _n_;
run;

proc sql;
    create table adam.adlb as
    select a.STUDYID, a.USUBJID, a.SUBJID, a.TRT01P, a.TRTSDT, a.PARAMCD, a.PARAM,
           m.PARAMN, a.PARCAT1, a.ADT, a.AVAL, a.AVALC, a.LBNRLO, a.LBNRHI, a.LBNRIND,
           a.AVISIT, a.AVISITN, a.AWDIST, a.ATOXGR, a.BASE, a.BASEC, a.BTOXGR, a.CHG, a.PCHG,
           a.ANL01FL, a.BASEFL, a.LBDY
    from work.adlb_all as a
    left join work._pnmap as m on a.PARAMCD = m.PARAMCD;
quit;

proc sort data=adam.adlb;
    by usubjid PARAMCD AVISITN lbdy;
run;

/* Clean up work library */
proc delete data=work.lb_base work.lb_windows work.lb_base_pre work.baselines
            work.lb_base_merged work.lb_anl01 work.anc_records work.anc_nadir_val
            work.anc_nadir_summary work.anc_recovery work.optimus_nadir work.optimus_rec
            work.adlb_all work._pc work._pnmap;
run;
quit;
