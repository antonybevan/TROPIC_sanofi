*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adcm_generation.sas
   Version: 2.2.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-05-27
   Standard: ADaMIG v1.3 OCCDS v1.0
   Input: sdtm.cm, adam.adsl
   Output: adam.adcm
   Description: Generates Concomitant Medications ADaM (ADCM) and derives
                critical safety flags for G-CSF, Prednisone compliance, and NACT.
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
    /* Create base dataset merging CM and ADSL */
    create table work.cm_base as
    select 
        adsl.studyid,
        adsl.usubjid,
        adsl.trt01p,
        adsl.trtsdt,
        cm.cmtrt,
        cm.cmdecod,
        cm.cmcat length=60,
        cm.cmindc,
        cm.cmstdt,
        cm.cmendt,
        cm.cmstdy
    from sdtm.cm as cm
    left join adam.adsl as adsl on cm.usubjid = adsl.usubjid
    where adsl.saffl = 'Y';
quit;

/* Calculate NACTDT per subject first */
proc sql;
    create table work.nact_dates as
    select 
        usubjid,
        min(cmstdt) as nactdt format=yymmdd10.
    from work.cm_base
    where cmcat = 'POST TREATMENT ANTI-CANCER DRUG THERAPY' and not missing(cmstdt)
    group by usubjid;
quit;

/* Sort datasets by BY-variable before merging */
proc sort data=work.cm_base;
    by usubjid;
run;

proc sort data=work.nact_dates;
    by usubjid;
run;

/* Derive CM flags and merge NACTDT */
data adam.adcm(keep=STUDYID USUBJID CMDECOD CMCAT CMINDC CMSTDT CMENDT CMTRT CMSTDY GCSFFL GCSFPRFL NACTFL NACTDT PREDNFL TRTEMFL
                    rename=(CMSTDT=ASTDT CMENDT=AENDT CMSTDY=ASTDY));  /* audit F-10: OCCDS analysis-date naming */
    merge work.cm_base work.nact_dates;
    by usubjid;
    
    length GCSFFL GCSFPRFL NACTFL PREDNFL TRTEMFL $1;
    
    /* G-CSF Concomitant Med flag */
    if cmdecod in ('FILGRASTIM', 'PEGFILGRASTIM', 'LENOGRASTIM') then GCSFFL = 'Y';
    else GCSFFL = 'N';
    
    /* G-CSF Prophylactic flag (prophy indication or within 3 days of dose start) */
    if GCSFFL = 'Y' and (cmindc = 'PROPHYLAXIS' or (not missing(cmstdy) and cmstdy >= -3 and cmstdy <= 3)) then GCSFPRFL = 'Y';
    else GCSFPRFL = 'N';
    
    /* New Anti-Cancer Therapy flag */
    if cmcat = 'POST TREATMENT ANTI-CANCER DRUG THERAPY' then NACTFL = 'Y';
    else NACTFL = 'N';
    
    /* Prednisone baseline compliance check */
    if cmdecod in ('PREDNISONE', 'PREDNISOLONE') then PREDNFL = 'Y';
    else PREDNFL = 'N';
    
    /* Treatment Emergent flag */
    if not missing(cmstdt) and cmstdt >= trtsdt then TRTEMFL = 'Y';
    else TRTEMFL = 'N';
    
    label 
        GCSFFL = 'G-CSF Concomitant Med Flag'
        GCSFPRFL = 'G-CSF Prophylactic Med Flag'
        NACTFL = 'New Anti-Cancer Therapy Flag'
        NACTDT = 'First Date of New Anti-Cancer Therapy'
        PREDNFL = 'Prednisone Co-Medication Flag'
        TRTEMFL = 'Treatment Emergent Med Flag';
run;

proc sort data=adam.adcm;
    by usubjid ASTDT cmdecod;
run;

/* Clean up work library */
proc delete data=work.cm_base work.nact_dates;
run;
quit;
