*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adtte_generation.sas
   Version: 2.0
   Author: Principal Clinical Data Infrastructure Architect
   Date: 2026-05-23
   Standard: ADaMIG v1.3 / CDISC BDS TTE v1.0
   Input: adam.adsl, adam.adrs, adam.adcm, adam.adae
   Output: adam.adtte
   Description: Time-to-Event ADaM (ADTTE) with standard censoring (CNSR=0/1) for
                Overall Survival (OS), Progression-Free Survival (PFS),
                and Time to First Serious AE (TTOS).
   ============================================================================= */

%include "00_config.sas";

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
    
    AVAL = ADT - STARTDT + 1;
    output;
run;

/* Add PFS parameter which has a more complex censoring hierarchy */
proc sql;
    create table work.nact_mapping as
    select usubjid, max(nactdt) as nactdt format=yymmdd10.
    from adam.adcm
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
    
    AVAL = ADT - STARTDT + 1;
    output;
run;

/* Combine TTE parameters */
data adam.adtte;
    set work.tte_base work.pfs_derived;
run;

proc sort data=adam.adtte;
    by usubjid PARAMCD;
run;

/* Clean up work library */
proc datasets lib=work nolist kill;
run;
quit;
