*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adae_io_respec.sas
   Version: 2.2.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-05-27
   Standard: ADaMIG v1.3 OCCDS v1.1
   Input: sdtm.ae, adam.adsl
   Output: adam.adae
   Description: Generates Adverse Events ADaM (ADAE) under OCCDS v1.1.
                Implements custom sponsor-defined continuous episode merging (gap <= 3 days)
                with corrected AEOCCFL occurrence denominator flags.
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
    /* Create base dataset merging AE and ADSL */
    create table work.ae_base as
    select
        adsl.studyid,
        adsl.usubjid,
        adsl.trt01p,
        adsl.trt01a as TRTA length=20,
        adsl.trt01an as TRTAN,
        adsl.trtsdt,
        ae.aeseq,            /* carried only as a deterministic sort tie-breaker; dropped before output */
        ae.aedecod,
        ae.aebodsys,
        ae.aehlt,
        case 
            when ae.aetoxgrn = 1 then 'MILD'
            when ae.aetoxgrn = 2 then 'MODERATE'
            when ae.aetoxgrn >= 3 then 'SEVERE'
            else ''
        end as aesev length=10,
        ae.aetoxgrn as atoxgr,
        ae.aeser,
        ae.aerel,
        ae.aestdt as astdt,
        ae.aeendt as aendt,
        case when not missing(ae.aestdt) and not missing(adsl.trtsdt) then ae.aestdt - adsl.trtsdt + 1 else . end as astdy,
        case when not missing(ae.aeendt) and not missing(adsl.trtsdt) then ae.aeendt - adsl.trtsdt + 1 else . end as aendy,
        ae.aeout,
        ae.aeacn,
        ae.aetrtem,
        /* Custom Sponsor Grouping: Customized Query 02 Name for Hematologic Events */
        case 
            when ae.aedecod in ('NEUTROPENIA', 'FEBRILE NEUTROPENIA', 'LEUKOPENIA') then 'HEMATOLOGIC EVENT'
            else ''
        end as CQ02NAM length=40,
        case 
            when ae.aedecod in ('NEUTROPENIA', 'FEBRILE NEUTROPENIA', 'LEUKOPENIA') then 'CQ02'
            else ''
        end as CQ02CD length=8,
        case 
            when ae.aedecod in ('NEUTROPENIA', 'FEBRILE NEUTROPENIA', 'LEUKOPENIA') then 'SPONSOR'
            else ''
        end as CQ02SC length=10
    from sdtm.ae as ae
    left join adam.adsl as adsl on ae.usubjid = adsl.usubjid
    where adsl.saffl = 'Y';
quit;

/* Sort for episode merging algorithm.
   AESEQ is appended as a DETERMINISTIC final tie-breaker (audit F-1) so that the
   independent R validation track can reproduce this exact order from source SDTM
   without ever reading the SAS production output. */
proc sort data=work.ae_base;
    by usubjid CQ02NAM astdt aendt aeseq;
run;

/* Episode Merging and OCCDS v1.1 Occurrence Flagging */
data work.ae_episodes;
    set work.ae_base;
    by usubjid CQ02NAM;
    
    retain _ciaeseq _ciaesdt _ciaeedt;
    
    length AEOCCFL $1;
    
    /* Initialize or increment sequence */
    if first.usubjid or first.cq02nam then do;
        if not missing(cq02nam) and cq02nam ne '' then do;
            _ciaeseq = 1;
            _ciaesdt = astdt;
            _ciaeedt = aendt;
            AEOCCFL = 'Y';
        end;
        else do;
            _ciaeseq = .;
            _ciaesdt = .;
            _ciaeedt = .;
            AEOCCFL = 'Y'; /* standard AE default first record */
        end;
    end;
    else do;
        if not missing(cq02nam) and cq02nam ne '' then do;
            /* Gap rule: check if start date is within 3 days of prior end date.
               Compute the window end without arithmetic on a missing prior end date
               (avoids a benign "missing values" NOTE); the comparison semantics are
               identical — a missing prior end yields a missing window, exactly as
               (_ciaeedt + gap) would. */
            if missing(_ciaeedt) then _ci_gapend = .;
            else _ci_gapend = _ciaeedt + &EPISODE_GAP_DAYS.;
            if astdt <= _ci_gapend then do;
                /* Merge: update end date to running maximum */
                _ciaeedt = max(_ciaeedt, aendt);
                AEOCCFL = 'N';
            end;
            else do;
                /* Reset sequence: new separate continuous episode */
                _ciaeseq = _ciaeseq + 1;
                _ciaesdt = astdt;
                _ciaeedt = aendt;
                AEOCCFL = 'Y';
            end;
        end;
        else do;
            /* For non-grouped AEs, set Y to first occurrence of AEDECOD per patient */
            _ciaeseq = .;
            _ciaesdt = .;
            _ciaeedt = .;
            AEOCCFL = 'Y'; /* Default first occurrence check handled below */
        end;
    end;
    
    /* Map working tracking variables to sponsor-defined non-standard variables */
    if not missing(cq02nam) and cq02nam ne '' then do;
        CIAESEQ = _ciaeseq;
        CIAESDT = _ciaesdt;
        CIAEEDT = _ciaeedt;
        /* Guard duration arithmetic; result (missing) is unchanged when either
           episode boundary date is missing, but no "missing values" NOTE is emitted. */
        if not missing(CIAEEDT) and not missing(CIAESDT) then
            CIAEDUR = (CIAEEDT - CIAESDT + 1) / 30.4375;
        else CIAEDUR = .;
    end;
    else do;
        CIAESEQ = .;
        CIAESDT = .;
        CIAEEDT = .;
        CIAEDUR = .;
    end;
    
    format CIAESDT CIAEEDT yymmdd10. CIAEDUR 8.2;
run;

/* Resolve standard OCCDS v1.1 denominator flag for non-grouped AEDECODs.
   AENDT + AESEQ appended as deterministic tie-breakers (audit F-1). */
proc sort data=work.ae_episodes;
    by usubjid aedecod astdt aendt aeseq;
run;

data adam.adae(keep=STUDYID USUBJID TRTA TRTAN AEDECOD AEBODSYS AEHLT AESEV ATOXGR AESER AEREL ASTDT AENDT ASTDY AENDY AEACN AEOUT CQ02NAM CQ02CD CQ02SC CIAESEQ CIAESDT CIAEEDT CIAEDUR AEOCCFL TRTEMFL ADURN ADURU AESEQ);
    set work.ae_episodes;
    by usubjid aedecod;
    
    /* Standard Treatment Emergent Flag */
    length TRTEMFL $1;
    if not missing(aetrtem) and strip(aetrtem) ne '' then do;
        if aetrtem = 'T' then TRTEMFL = 'Y';
        else TRTEMFL = 'N';
    end;
    else if not missing(astdt) and astdt >= trtsdt then TRTEMFL = 'Y';
    else TRTEMFL = 'N';
    
    /* Non-grouped OCCDS compliance override */
    if missing(cq02nam) or cq02nam = '' then do;
        if first.aedecod then AEOCCFL = 'Y';
        else AEOCCFL = 'N';
    end;
    
    /* Standard durations */
    if not missing(aendt) and not missing(astdt) then ADURN = aendt - astdt + 1;
    else ADURN = .;
    ADURU = 'DAYS';
    
    label 
        TRTEMFL = 'Treatment Emergent AE Flag'
        AEOCCFL = 'OCCDS Denominator Flag'
        CQ02NAM = 'Customized Query 02 Name'
        CQ02CD  = 'Customized Query 02 Code'
        CQ02SC  = 'Customized Query 02 Source'
        CIAESEQ = 'Continuous Episode Sequence'
        CIAESDT = 'Continuous Episode Start Date'
        CIAEEDT = 'Continuous Episode End Date'
        CIAEDUR = 'Episode Duration (Months)';
run;

proc sort data=adam.adae;
    by usubjid astdt aedecod aendt aeseq;
run;

/* Clean up work library */
proc delete data=work.ae_base work.ae_episodes;
run;
quit;
