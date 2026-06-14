*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adrs_generation.sas
   Version: 2.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-05-23
   Standard: CDISC ADaMIG v1.3 BDS
   Input: sdtm.rs, sdtm.lb, adam.adsl
   Output: adam.adrs
   Description: Efficacy response ADaM (ADRS) combining progression and
                death milestones with PSA progression metrics.
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

/* 1. RECIST v1.0 Visit-level calculations (trial-era standard per SAP v3.0 §5.3) */
/* Baseline Target Sum of Diameters */
proc sql;
    create table work.base_sod as
    select usubjid, sum(lsstresn) as base_sod
    from staging.ls
    where lscat = 'TARGET' and lstestcd = 'LENGTH' and not missing(lsstresn) and visit = 'BASELINE'
    group by usubjid;
quit;

/* Post-Baseline Target Sum of Diameters */
proc sql;
    create table work.post_sod as
    select ls.usubjid, ls.visitnum, ls.visit,
           input(substr(ls.lsdtc, 1, 10), yymmdd10.) as lsd_dt format=yymmdd10.,
           sum(ls.lsstresn) as post_sod
    from staging.ls as ls
    where ls.lscat = 'TARGET' and ls.lstestcd = 'LENGTH' and not missing(ls.lsstresn) and ls.visit ne 'BASELINE'
    group by ls.usubjid, ls.visitnum, ls.visit, ls.lsdtc;
quit;

/* Join baseline, calculate nadir, and evaluate response */
proc sql;
    create table work.cycle_sod_comp as
    select p.usubjid, p.visitnum, p.visit, p.lsd_dt, p.post_sod, b.base_sod
    from work.post_sod as p
    left join work.base_sod as b on p.usubjid = b.usubjid;
quit;

proc sort data=work.cycle_sod_comp;
    by usubjid visitnum;
run;

data work.recist_calc;
    set work.cycle_sod_comp;
    by usubjid;
    
    retain nadir_sod;
    
    if first.usubjid then nadir_sod = post_sod;
    else nadir_sod = min(nadir_sod, post_sod);
    
    if base_sod > 0 then pct_chg_base = (post_sod - base_sod) / base_sod * 100;
    else pct_chg_base = .;
    if nadir_sod > 0 then pct_chg_nadir = (post_sod - nadir_sod) / nadir_sod * 100;
    else pct_chg_nadir = .;
    abs_chg_nadir = post_sod - nadir_sod;
    
    length recist_resp $20;
    if post_sod = 0 then recist_resp = 'CR';
    else if pct_chg_nadir >= &RECIST_PD_PCT. and abs_chg_nadir >= &RECIST_PD_ABS. then recist_resp = 'PD';
    else if pct_chg_base <= &RECIST_PR_PCT. then recist_resp = 'PR';
    else recist_resp = 'SD';
run;

/* Map derived RECIST overall response records */
proc sql;
    create table work.recist_ovrl as
    select 
        adsl.studyid,
        adsl.usubjid,
        adsl.trt01p,
        adsl.trtsdt,
        'Overall Response per RECIST v1.0' as PARAM length=40,
        'OVRLRESP' as PARAMCD length=8,
        r.recist_resp as AVALC length=20,
        r.lsd_dt as ADT format=yymmdd10.,
        r.lsd_dt - adsl.trtsdt + 1 as ADY,
        r.visit as AVISIT length=40
    from work.recist_calc as r
    left join adam.adsl as adsl on r.usubjid = adsl.usubjid;
quit;

/* Map Efficacy Milestones from sdtm.rs */
proc sql;
    create table work.rs_disp as
    select 
        adsl.studyid,
        adsl.usubjid,
        adsl.trt01p,
        adsl.trtsdt,
        'Overall Response per RECIST v1.0' as PARAM length=40,
        'OVRLRESP' as PARAMCD length=8,
        rs.rsorres as AVALC length=20,
        rs.rsdt as ADT format=yymmdd10.,
        rs.rsdy as ADY,
        rs.visit as AVISIT length=40
    from sdtm.rs as rs
    left join adam.adsl as adsl on rs.usubjid = adsl.usubjid
    where adsl.saffl = 'Y';
quit;

/* Union visit-level records */
data work.rs_base;
    set work.recist_ovrl work.rs_disp;
run;

proc sort data=work.rs_base;
    by usubjid ADT AVALC;
run;

/* Best Overall Response (BOR) */
proc sql;
    create table work.bor_rank as
    select 
        studyid,
        usubjid,
        trt01p,
        trtsdt,
        case 
            when AVALC = 'CR' then 1.0
            when AVALC = 'PR' then 2.0
            when AVALC = 'SD' then 3.0
            when AVALC = 'PD' then 4.0
            when AVALC = 'DEATH' then 5.0
            else 6.0
        end as rank,
        AVALC
    from work.rs_base
    where not missing(ADT);
quit;

proc sort data=work.bor_rank;
    by usubjid rank;
run;

data work.bor_summary;
    set work.bor_rank;
    by usubjid rank;
    if first.usubjid;
    
    length PARAMCD $8 PARAM $40 AVISIT $40;
    
    PARAMCD = 'BESTRESP';
    PARAM = 'Best Overall Response (BOR)';
    AVISIT = 'ALL CYCLES';
    AVISITN = 99;
    
    AVAL = rank;
    drop rank;
run;

/* Objective Response (CR/PR) */
data work.orr_summary;
    set work.bor_summary;
    
    PARAMCD = 'OBJRESP';
    PARAM = 'Objective Response (CR or PR)';
    
    if AVALC in ('CR', 'PR') then do;
        AVALC = 'Y';
        AVAL = 1.0;
    end;
    else do;
        AVALC = 'N';
        AVAL = 0.0;
    end;
run;

/* Rigorous PCWG3 PSA Progression Logic */
proc sql;
    create table work.psa_base as
    select usubjid, lbstresn as psabl, lbdt as base_dt
    from sdtm.lb
    where lbtestcd = 'PSA' and lbblfl = 'Y' and not missing(lbstresn);
quit;

proc sql;
    create table work.psa_post as
    select lb.usubjid, lb.lbdt, lb.lbstresn, lb.visit, lb.visitnum
    from sdtm.lb as lb
    inner join work.psa_base as b on lb.usubjid = b.usubjid
    where lb.lbtestcd = 'PSA' and lb.lbdt > b.base_dt and not missing(lb.lbstresn);
quit;

proc sql;
    create table work.psa_decline as
    select p.*, b.psabl, (b.psabl - p.lbstresn) / b.psabl as decline
    from work.psa_post as p
    inner join work.psa_base as b on p.usubjid = b.usubjid;
quit;

proc sql;
    create table work.psa_resp_cand as
    select a.usubjid, a.lbdt as dt1, b.lbdt as dt2
    from work.psa_decline as a
    inner join work.psa_decline as b on a.usubjid = b.usubjid
    where a.decline >= &PSA_RESP_THRESHOLD. and b.decline >= &PSA_RESP_THRESHOLD. and b.lbdt - a.lbdt >= &PSA_RESP_CONFIRM.;
quit;

proc sql;
    create table work.psa_responders as
    select distinct usubjid, 'Y' as psad50 length=1
    from work.psa_resp_cand;
quit;

data work.psa_all;
    set work.psa_base(keep=usubjid base_dt psabl rename=(psabl=lbstresn base_dt=lbdt))
        work.psa_post(keep=usubjid lbdt lbstresn visit visitnum);
run;

proc sort data=work.psa_all;
    by usubjid lbdt;
run;

data work.psa_nadir;
    set work.psa_all;
    by usubjid;
    retain psanadir;
    if first.usubjid then psanadir = lbstresn;
    else psanadir = min(psanadir, lbstresn);
run;

proc sql;
    create table work.psa_prog_check as
    select n.*, coalesce(r.psad50, 'N') as psad50
    from work.psa_nadir as n
    left join work.psa_responders as r on n.usubjid = r.usubjid;
quit;

data work.psa_prog_eval;
    set work.psa_prog_check;
    if not missing(visitnum) and visitnum > 0;
    length is_trigger 8;
    if psad50 = 'Y' then do;
        if lbstresn >= &PSA_PROG_MULT_RESP. * psanadir then is_trigger = 1;
        else is_trigger = 0;
    end;
    else do;
        if lbstresn >= &PSA_PROG_MULT_NORESP. * psanadir and (lbstresn - psanadir) >= &PSA_PROG_ABS. then is_trigger = 1;
        else is_trigger = 0;
    end;
run;

proc sql;
    create table work.psa_prog_conf as
    select distinct a.usubjid, min(a.lbdt) as prog_date format=yymmdd10.
    from work.psa_prog_eval as a
    inner join work.psa_prog_eval as b on a.usubjid = b.usubjid
    where a.is_trigger = 1 and b.is_trigger = 1 and b.lbdt - a.lbdt >= &PSA_PROG_CONFIRM.
    group by a.usubjid;
quit;

/* Final PSPROG Parameter creation */
proc sql;
    create table work.psprog as
    select 
        adsl.usubjid,
        'PSPROG' as PARAMCD length=8,
        'PSA Progression (PCWG3)' as PARAM length=40,
        case when not missing(p.prog_date) then 'Y' else 'N' end as AVALC length=20,
        case when not missing(p.prog_date) then 1.0 else 0.0 end as AVAL,
        p.prog_date as ADT format=yymmdd10.,
        'ALL CYCLES' as AVISIT length=40,
        99 as AVISITN
    from adam.adsl as adsl
    left join work.psa_prog_conf as p on adsl.usubjid = p.usubjid
    where adsl.saffl = 'Y';
quit;

/* Final PSARESP Parameter creation */
proc sql;
    create table work.psaresp as
    select 
        adsl.usubjid,
        'PSARESP' as PARAMCD length=8,
        'PSA Response (>=50% decline)' as PARAM length=40,
        coalesce(r.psad50, 'N') as AVALC length=20,
        case when r.psad50 = 'Y' then 1.0 else 0.0 end as AVAL,
        . as ADT format=yymmdd10.,
        'ALL CYCLES' as AVISIT length=40,
        99 as AVISITN
    from adam.adsl as adsl
    left join work.psa_responders as r on adsl.usubjid = r.usubjid
    where adsl.saffl = 'Y';
quit;

/* Combine all parameters and sort before merge */
data work.adrs_union;
    set work.rs_base work.bor_summary work.orr_summary work.psprog work.psaresp;
run;

proc sort data=work.adrs_union;
    by usubjid;
run;

proc sql;
    create table adam.adrs as
    select 
        coalesce(u.studyid, adsl.studyid) as STUDYID length=20,
        u.usubjid as USUBJID length=40,
        adsl.subjid as SUBJID length=10,
        coalesce(u.trt01p, adsl.trt01p) as TRT01P length=20,
        coalesce(u.trtsdt, adsl.trtsdt) as TRTSDT format=yymmdd10.,
        u.PARAMCD,
        u.PARAM,
        u.AVALC,
        u.ADT,
        u.ADY,
        u.AVISIT,
        'Y' as ANL01FL length=1,
        u.AVAL
    from work.adrs_union as u
    left join adam.adsl as adsl on u.usubjid = adsl.usubjid
    where adsl.saffl = 'Y';
quit;

proc sort data=adam.adrs;
    by usubjid PARAMCD AVISIT;
run;

/* Clean up work library */
proc delete data=work.base_sod work.post_sod work.cycle_sod_comp work.recist_calc work.recist_ovrl work.rs_disp work.rs_base work.bor_rank work.bor_summary work.orr_summary work.psa_base work.psa_post work.psa_decline work.psa_resp_cand work.psa_responders work.psa_all work.psa_nadir work.psa_prog_check work.psa_prog_eval work.psa_prog_conf work.psprog work.psaresp work.adrs_union;
run;
quit;
