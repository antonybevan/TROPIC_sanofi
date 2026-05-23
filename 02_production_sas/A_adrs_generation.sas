*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adrs_generation.sas
   Version: 2.0
   Author: Principal Clinical Data Infrastructure Architect
   Date: 2026-05-23
   Standard: CDISC ADaMIG v1.3 BDS
   Input: sdtm.rs, sdtm.lb, adam.adsl
   Output: adam.adrs
   Description: Efficacy response ADaM (ADRS) combining progression and
                death milestones with PSA progression metrics.
   ============================================================================= */

%include "00_config.sas";

proc sql;
    /* Base dataset merging RS and ADSL */
    create table work.rs_base as
    select 
        adsl.studyid,
        adsl.usubjid,
        adsl.trt01p,
        adsl.trtsdt,
        'Overall Response per RECIST 1.1 + PCWG3' as PARAM length=40,
        'OVRLRESP' as PARAMCD length=8,
        rs.rsorres as AVALC length=20,
        rs.rsdt as ADT format=yymmdd10.,
        rs.rsdy as ADY,
        rs.visit length=40
    from sdtm.rs as rs
    left join adam.adsl as adsl on rs.usubjid = adsl.usubjid
    where adsl.saffl = 'Y';
quit;

/* Calculate Best Overall Response (BOR) per subject */
proc sql;
    create table work.bor_raw as
    select 
        usubjid,
        min(case when AVALC = 'PD' then 4.0 else 5.0 end) as bor_val
    from work.rs_base
    where not missing(ADT)
    group by usubjid;
quit;

data work.bor_summary;
    set work.bor_raw;
    length PARAMCD $8 PARAM $40 AVALC $40 AVISIT $40;
    
    PARAMCD = 'BESTRESP';
    PARAM = 'Best Overall Response (BOR)';
    AVISIT = 'ALL CYCLES';
    AVISITN = 99;
    
    if bor_val = 4.0 then AVALC = 'PD';
    else AVALC = 'DEATH';
    
    AVAL = bor_val;
run;

/* Objective Response Parameter (always N/0.0 for control cohort) */
proc sql;
    create table work.orr_summary as
    select 
        usubjid,
        'OBJRESP' as PARAMCD length=8,
        'Objective Response (CR or PR)' as PARAM length=40,
        'N' as AVALC length=20,
        0.0 as AVAL,
        'ALL CYCLES' as AVISIT length=40,
        99 as AVISITN
    from work.bor_summary;
quit;

/* PSA progression indicator */
proc sql;
    create table work.psprog as
    select 
        usubjid,
        'PSPROG' as PARAMCD length=8,
        'PSA Progression (PCWG3)' as PARAM length=40,
        case when count(lbstresn) > 0 then 'Y' else 'N' end as AVALC length=20,
        case when count(lbstresn) > 0 then 1.0 else 0.0 end as AVAL,
        'ALL CYCLES' as AVISIT length=40,
        99 as AVISITN
    from sdtm.lb
    where lbtestcd = 'PSA' and upcase(lbnrind) in ('HIGH', 'H')
    group by usubjid;
quit;

/* Combine all parameters */
data adam.adrs;
    set work.rs_base work.bor_summary work.orr_summary work.psprog;
    
    /* Bring in ADSL headers */
    merge adam.adsl(keep=studyid usubjid subjid siteid trt01p trt01pn saffl trtsdt trtedt trtdurd) ;
    by usubjid;
    where saffl = 'Y';
    
    length ANL01FL $1;
    ANL01FL = 'Y';
    
    label 
        PARAMCD = 'Parameter Code'
        PARAM = 'Parameter Description'
        AVALC = 'Analysis Value (C)'
        AVAL = 'Analysis Value'
        ANL01FL = 'Analysis Flag 01';
run;

proc sort data=adam.adrs;
    by usubjid PARAMCD AVISIT;
run;

/* Clean up work library */
proc datasets lib=work nolist kill;
run;
quit;
