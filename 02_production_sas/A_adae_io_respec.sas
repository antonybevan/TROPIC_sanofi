*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adae_io_respec.sas
   Version: 2.0
   Author: Principal Clinical Data Infrastructure Architect
   Date: 2026-05-23
   Standard: ADaMIG v1.3 OCCDS v1.1
   Input: sdtm.ae, adam.adsl
   Output: adam.adae
   Description: Generates Adverse Events ADaM (ADAE) under OCCDS v1.1.
                Implements custom sponsor-defined continuous episode merging (gap <= 3 days)
                with corrected AEOCCFL occurrence denominator flags.
   ============================================================================= */

%include "00_config.sas";

proc sql;
    /* Create base dataset merging AE and ADSL */
    create table work.ae_base as
    select 
        adsl.studyid,
        adsl.usubjid,
        adsl.trt01p,
        adsl.trtsdt,
        ae.aedecod,
        ae.aebodsys,
        ae.aehlt,
        case 
            when ae.aetoxgrn = 1 then 'MILD'
            when ae.aetoxgrn = 2 then 'MODERATE'
            when ae.aetoxgrn >= 3 then 'SEVERE'
            else 'MILD'
        end as aesev length=10,
        ae.aetoxgrn as atoxgr,
        ae.aeser,
        ae.aerel,
        ae.aestdt as astdt,
        ae.aeendt as aendt,
        ae.aestdy as astdy,
        ae.aeendy as aendy,
        ae.aeout,
        ae.aeacn,
        ae.aetrtem,
        /* Custom Sponsor Grouping: Customized Query 02 Name for irAEs */
        case 
            when ae.aedecod in ('NEUTROPENIA', 'FEBRILE NEUTROPENIA', 'LEUKOPENIA') then 'HEMATOLOGIC IRAE'
            else ''
        end as CQ02NAM length=40
    from sdtm.ae as ae
    left join adam.adsl as adsl on ae.usubjid = adsl.usubjid
    where adsl.saffl = 'Y';
quit;

/* Sort for episode merging algorithm */
proc sort data=work.ae_base;
    by usubjid CQ02NAM astdt aendt;
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
            /* Gap rule: check if start date is within 3 days of prior end date */
            if astdt <= (_ciaeedt + 3) then do;
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
        CIAEDUR = (CIAEEDT - CIAESDT + 1) / 30.4375;
    end;
    else do;
        CIAESEQ = .;
        CIAESDT = .;
        CIAEEDT = .;
        CIAEDUR = .;
    end;
    
    format CIAESDT CIAEEDT yymmdd10. CIAEDUR 8.2;
run;

/* Resolve standard OCCDS v1.1 denominator flag for non-grouped AEDECODs */
proc sort data=work.ae_episodes;
    by usubjid aedecod astdt;
run;

data adam.adae;
    set work.ae_episodes;
    by usubjid aedecod;
    
    /* Standard Treatment Emergent Flag */
    length TRTEMFL $1;
    if not missing(aetrtem) and strip(aetrtem) ne '' then TRTEMFL = aetrtem;
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
        CIAESEQ = 'Continuous Episode Sequence'
        CIAESDT = 'Continuous Episode Start Date'
        CIAEEDT = 'Continuous Episode End Date'
        CIAEDUR = 'Episode Duration (Months)';
run;

proc sort data=adam.adae;
    by usubjid astdt aedecod;
run;

/* Clean up work library */
proc datasets lib=work nolist kill;
run;
quit;
