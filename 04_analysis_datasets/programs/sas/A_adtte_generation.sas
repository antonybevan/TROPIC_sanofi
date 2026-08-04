*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adtte_generation.sas
   Version: 3.0.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-06-13 (ADaM dens contract 2026-07-09)
   Standard: ADaMIG v1.3 / CDISC BDS TTE v1.0
   Input: adam.adsl, adam.adrs, adam.adcm, adam.adae, adam.adlb, staging.pn
   Output: adam.adtte
   Description: Time-to-Event ADaM (ADTTE) with standard censoring (CNSR=0/1).

   ADaM dens contract (from ADSL — never EXTRT arm; never AE-distinct dens):
           OS, PFS, TTPSA, TTPAIN -> one row per ADSL ITTFL='Y' (Path A: 371)
           TTSAE                  -> one row per ADSL SAFFL='Y' (Path A: 371)
           TTUMOR                 -> one row per ADSL ITTFL='Y' (MEASDISF sensitivity)
           TRT01P/TRT01PN always from ADSL (DM-derived)

   Remediation v2.4.0 (roadmap #2/#3/#4/#7):
     #4  Analysis population per parameter is explicit and recorded on-record
         (ITTFL + SAFFL carried on every record):
           OS, PFS        -> ITT  (ITTFL='Y')   [anchored at RANDDT]
           TTPAIN         -> ITT with diary evaluability (ITTFL='Y') [anchored at RANDDT]
           TTPSA          -> ITT  (ITTFL='Y')   [anchored at RANDDT]
           TTSAE          -> SAFETY (SAFFL='Y') [anchored at TRTSDT]
           TTUMOR         -> ITT (measurable-disease subgroup retained as sensitivity, anchored at RANDDT)
     #3  PSA-progression censoring date is sourced from ADLB (adam.adlb,
         PARAMCD='PSA') -- an ADaM input -- NOT from raw sdtm.lb. The R
         validation track reads the same ADaM (adlb_v.xpt) for parity.
     #2  F-042 Phase 2 uses component-specific exact-duplicate collapse and
         discordance flags; SAS/R implement the adopted rule independently.
     #7  PARAMN, PARCAT1, AVALU carried for BDS-TTE metadata completeness.
     #10 Administrative data-cutoff (&STUDY_CUTOFF_DT.) is applied consistently
         to the censoring branch of EVERY parameter (was TTPSA/TTUMOR only).
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

/* 1. Retrieve first post-randomisation PD date per subject across all source
   domains.  Baseline milestones are not PFS/TTE events under SAP v4.0. */
proc sql;
    create table work.pd_dates as
    select
        r.usubjid,
        min(r.ADT) as pd_dt format=yymmdd10.
    from adam.adrs as r
    inner join adam.adsl(keep=usubjid randdt) as a
        on r.usubjid = a.usubjid
    where ((r.PARAMCD = 'OVRLRESP' and r.AVALC = 'PD') or
           (r.PARAMCD = 'BSGRESP' and r.AVALC = 'PROGRESSION') or
           (r.PARAMCD = 'PSPROG' and r.AVALC = 'Y'))
      and not missing(r.ADT)
      and r.ADT > a.RANDDT
    group by r.usubjid;
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

/* Assemble OS and TTSAE Parameters.
   No population filter on the base; each parameter is gated at OUTPUT to its own
   analysis population (#4), so OS=ITT and TTSAE=Safety can coexist. */
proc sql;
    create table work.os_ttsae_raw as
    select
        adsl.*,
        sae.sae_dt
    from adam.adsl(keep=studyid usubjid subjid siteid trt01p trt01pn ittfl saffl
                        randdt trtsdt trtedt dthfl dthdt lstalvdt) as adsl
    left join work.sae_dates as sae on adsl.usubjid = sae.usubjid;
quit;

data work.tte_base;
    set work.os_ttsae_raw;

    length PARAMCD $8 PARAM $40 PARCAT1 $20 AVALU $8 EVNTDESC CNSDTDSC $100;
    format ADT STARTDT yymmdd10. AVAL CNSR 8.2;
    AVALU = 'DAYS';

    /* -------------------------------------------------------------------------- */
    /* PARAMETER 1: OVERALL SURVIVAL  (ITT, anchored at RANDDT)                  */
    /* -------------------------------------------------------------------------- */
    if ITTFL = 'Y' then do;
        PARAMCD = 'OS';
        PARAM = 'Overall Survival';
        PARAMN = 1;
        PARCAT1 = 'EFFICACY';
        STARTDT = RANDDT;

        if dthfl = 'Y' then do;
            ADT = dthdt;
            CNSR = 0;
            EVNTDESC = 'DEATH';
            CNSDTDSC = '';
        end;
        else do;
            ADT = min(lstalvdt, &STUDY_CUTOFF_DT.);
            CNSR = 1;
            EVNTDESC = '';
            CNSDTDSC = 'LAST KNOWN ALIVE DATE';
        end;

        if not missing(ADT) and not missing(STARTDT) and ADT < STARTDT then
            putlog "WARNING: [ADTTE] event/censor date precedes time origin; floored to 1 day. " PARAMCD= USUBJID=;
        if ADT < STARTDT then ADT = STARTDT;
        AVAL = ADT - STARTDT + 1;
        output;
    end;

    /* -------------------------------------------------------------------------- */
    /* PARAMETER 6: TIME TO FIRST SERIOUS AE (TTSAE)  (Safety, anchored TRTSDT)  */
    /* -------------------------------------------------------------------------- */
    if SAFFL = 'Y' then do;
        PARAMCD = 'TTSAE';
        PARAM = 'Time to First Serious AE';
        PARAMN = 6;
        PARCAT1 = 'SAFETY';
        STARTDT = TRTSDT;

        if not missing(sae_dt) then do;
            ADT = sae_dt;
            CNSR = 0;
            EVNTDESC = 'SERIOUS ADVERSE EVENT';
            CNSDTDSC = '';
        end;
        else do;
            ADT = min(lstalvdt, &STUDY_CUTOFF_DT.);
            CNSR = 1;
            EVNTDESC = '';
            CNSDTDSC = 'LAST KNOWN ALIVE DATE';
        end;

        if not missing(ADT) and not missing(STARTDT) and ADT < STARTDT then
            putlog "WARNING: [ADTTE] event/censor date precedes time origin; floored to 1 day. " PARAMCD= USUBJID=;
        if ADT < STARTDT then ADT = STARTDT;
        AVAL = ADT - STARTDT + 1;
        output;
    end;
run;

/* F-042 Phase 2 controlled pain derivation.  This separately programmed SAS
   module creates the governed diary/RT event and censor-date work tables used
   by both PFS and TTPAIN. */
%include "&PGMDIR./F042_phase2_pain_derivation.sas";

/* SAP v4.0 PFS censoring uses the last evaluable post-baseline assessment when
   no progression/death/NACT event exists, and randomisation when there is no
   post-baseline assessment.  Build one governed date from the valid RECIST,
   PSA, and evaluable pain-visit sources.  Death milestones are excluded from
   the RECIST pool; they are not tumour assessments. */
proc sql;
    create table work.pfs_tumor_eval_dates as
    select r.usubjid, max(r.ADT) as last_tumor_eval_dt format=yymmdd10.
    from adam.adrs as r
    inner join adam.adsl(keep=usubjid randdt) as a
        on r.usubjid = a.usubjid
    where r.PARAMCD = 'OVRLRESP'
      and r.AVALC in ('CR', 'PR', 'SD', 'PD')
      and not missing(r.ADT)
      and r.ADT > a.RANDDT
    group by r.usubjid;

    create table work.pfs_psa_eval_dates as
    select l.usubjid, max(l.ADT) as last_psa_eval_dt format=yymmdd10.
    from adam.adlb as l
    inner join adam.adsl(keep=usubjid randdt) as a
        on l.usubjid = a.usubjid
    where l.PARAMCD = 'PSA'
      and not missing(l.AVAL)
      and not missing(l.ADT)
      and l.ADT > a.RANDDT
    group by l.usubjid;

    create table work.pfs_eval_candidates as
    select usubjid, last_tumor_eval_dt as last_eval_dt
    from work.pfs_tumor_eval_dates
    union all
    select usubjid, last_psa_eval_dt as last_eval_dt
    from work.pfs_psa_eval_dates
    union all
    select p.usubjid, p.last_pain_eval_dt as last_eval_dt
    from work.pfs_pain_eval_dates as p
    inner join adam.adsl(keep=usubjid randdt) as a
      on p.usubjid = a.usubjid
    where not missing(p.last_pain_eval_dt)
      and p.last_pain_eval_dt > a.RANDDT;

    create table work.pfs_last_eval_dates as
    select usubjid, max(last_eval_dt) as last_eval_dt format=yymmdd10.
    from work.pfs_eval_candidates
    group by usubjid;
quit;

/* Add PFS parameter which has a more complex censoring hierarchy (ITT) */
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
        pain.pain_prog_dt,
        nact.nactdt,
        eval.last_eval_dt
    from adam.adsl(keep=studyid usubjid subjid siteid trt01p trt01pn ittfl saffl
                        randdt dthfl dthdt lstalvdt) as adsl
    left join work.pd_dates as pd on adsl.usubjid = pd.usubjid
    left join work.pain_pfs_prog_dates as pain on adsl.usubjid = pain.usubjid
    left join work.nact_mapping as nact on adsl.usubjid = nact.usubjid
    left join work.pfs_last_eval_dates as eval on adsl.usubjid = eval.usubjid
    where adsl.ittfl = 'Y';
quit;

data work.pfs_derived;
    set work.pfs_raw;

    length PARAMCD $8 PARAM $40 PARCAT1 $20 AVALU $8 EVNTDESC CNSDTDSC $100;
    format ADT STARTDT yymmdd10. AVAL CNSR 8.2;
    AVALU = 'DAYS';

    PARAMCD = 'PFS';
    PARAM = 'Progression Free Survival';
    PARAMN = 2;
    PARCAT1 = 'EFFICACY';
    STARTDT = randdt;

    if not missing(pd_dt) and not missing(pain_prog_dt) then _prog_dt = min(pd_dt, pain_prog_dt);
    else if not missing(pd_dt) then _prog_dt = pd_dt;
    else if not missing(pain_prog_dt) then _prog_dt = pain_prog_dt;
    else _prog_dt = .;
    _pd_found = not missing(_prog_dt);
    _nact_found = not missing(nactdt);

    /* Hierarchy rule checking */
    if _pd_found then do;
        /* PD event occurred */
        if _nact_found and nactdt < _prog_dt then do;
            /* Censor: New therapy started BEFORE progression */
            ADT = nactdt - 1;
            CNSR = 1;
            EVNTDESC = '';
            CNSDTDSC = 'NEW ANTI-CANCER THERAPY START';
        end;
        else do;
            /* Event: Progression */
            ADT = _prog_dt;
            CNSR = 0;
            /* Preserve the earliest composite component in the existing
               ADTTE traceability field.  A non-pain component wins a same-day
               tie deterministically; the SAP supporting-disease decision for
               pain remains an explicit Section 3 residual. */
            if not missing(pain_prog_dt) and
               (missing(pd_dt) or pain_prog_dt < pd_dt) then
                EVNTDESC = 'PAIN PROGRESSION';
            else EVNTDESC = 'DISEASE PROGRESSION';
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
        /* Censor: NACT outranks all other censoring.  Otherwise use the last
           evaluable post-baseline assessment; if none exists, censor at
           randomisation per SAP v4.0. */
        if _nact_found then do;
            ADT = nactdt - 1;
            CNSR = 1;
            EVNTDESC = '';
            CNSDTDSC = 'NEW ANTI-CANCER THERAPY START';
        end;
        else if not missing(last_eval_dt) then do;
            ADT = min(last_eval_dt, &STUDY_CUTOFF_DT.);
            CNSR = 1;
            EVNTDESC = '';
            CNSDTDSC = 'LAST EVALUABLE ASSESSMENT';
        end;
        else do;
            ADT = randdt;
            CNSR = 1;
            EVNTDESC = '';
            CNSDTDSC = 'NO POST-BASELINE ASSESSMENT';
        end;
    end;

    if not missing(ADT) and not missing(STARTDT) and ADT < STARTDT then
            putlog "WARNING: [ADTTE] event/censor date precedes time origin; floored to 1 day. " PARAMCD= USUBJID=;
        if ADT < STARTDT then ADT = STARTDT;
    AVAL = ADT - STARTDT + 1;
    output;
run;

/* -------------------------------------------------------------------------- */
/* PARAMETER 5: TIME TO PAIN PROGRESSION (TTPAIN)  (ITT, RANDDT origin)       */
/* F-042 Phase 2 primary event = qualified diary OR direct-intent RT.         */
/* Non-events censor at the last evaluable scheduled pain assessment.          */
/* -------------------------------------------------------------------------- */
proc sql;
    create table work.ttpain_derived as
    select
        adsl.studyid as STUDYID length=40,
        adsl.usubjid as USUBJID length=40,
        adsl.subjid as SUBJID length=10,
        adsl.siteid as SITEID length=10,
        adsl.trt01p as TRT01P length=20,
        adsl.trt01pn as TRT01PN,
        adsl.ittfl as ITTFL length=1,
        adsl.saffl as SAFFL length=1,
        'TTPAIN' as PARAMCD length=8,
        'Time to Pain Progression' as PARAM length=40,
        5 as PARAMN,
        'EFFICACY' as PARCAT1 length=20,
        'DAYS' as AVALU length=8,
        adsl.randdt as STARTDT format=yymmdd10.,
        case
            when not missing(p.prog_date) then p.prog_date
            when not missing(c.last_pn_dt) then min(c.last_pn_dt, &STUDY_CUTOFF_DT.)
            else adsl.randdt
        end as ADT format=yymmdd10.,
        case when not missing(p.prog_date) then 0 else 1 end as CNSR,
        case when not missing(p.prog_date) then 'PAIN PROGRESSION'
             else '' end as EVNTDESC length=100,
        case when not missing(p.prog_date) then ''
             when not missing(c.last_pn_dt) then 'LAST EVALUABLE PAIN ASSESSMENT'
             else 'NO EVALUABLE PAIN ASSESSMENT' end as CNSDTDSC length=100
    from adam.adsl as adsl
    left join work.prog_dates as p on adsl.usubjid = p.usubjid
    left join work.censor_dates as c on adsl.usubjid = c.usubjid
    where adsl.ittfl = 'Y';
quit;

data work.ttpain_final;
    set work.ttpain_derived;
    if not missing(ADT) and not missing(STARTDT) and ADT < STARTDT then
        putlog "WARNING: [ADTTE] event/censor date precedes time origin; floored to 1 day. " PARAMCD= USUBJID=;
    if ADT < STARTDT then ADT = STARTDT;
    AVAL = ADT - STARTDT + 1;
run;

/* -------------------------------------------------------------------------- */
/* PARAMETER 3: TIME TO PSA PROGRESSION (TTPSA)  (ITT, anchored RANDDT)       */
/* #3: censoring date sourced from ADLB (adam.adlb, PARAMCD='PSA'), an ADaM   */
/*     input -- NOT raw sdtm.lb. R track reads the same ADaM (adlb_v.xpt).    */
/* -------------------------------------------------------------------------- */
proc sql;
    create table work.psa_prog_dates as
    select r.usubjid, r.ADT as psa_prog_dt
    from adam.adrs as r
    inner join adam.adsl(keep=usubjid randdt) as a
        on r.usubjid = a.usubjid
    where r.PARAMCD = 'PSPROG' and r.AVALC = 'Y'
      and not missing(r.ADT) and r.ADT > a.RANDDT;
quit;

proc sql;
    create table work.psa_censor_dates as
    select usubjid, max(ADT) as last_psa_dt format=yymmdd10.
    from adam.adlb
    where PARAMCD = 'PSA' and not missing(AVAL) and not missing(ADT)
    group by usubjid;
quit;

proc sql;
    create table work.ttpsa_derived as
    select
        adsl.studyid as STUDYID length=40,
        adsl.usubjid as USUBJID length=40,
        adsl.subjid as SUBJID length=10,
        adsl.siteid as SITEID length=10,
        adsl.trt01p as TRT01P length=20,
        adsl.trt01pn as TRT01PN,
        adsl.ittfl as ITTFL length=1,
        adsl.saffl as SAFFL length=1,
        'TTPSA' as PARAMCD length=8,
        'Time to PSA Progression' as PARAM length=40,
        3 as PARAMN,
        'EFFICACY' as PARCAT1 length=20,
        'DAYS' as AVALU length=8,
        adsl.randdt as STARTDT format=yymmdd10.,

        case
            when not missing(p.psa_prog_dt) then p.psa_prog_dt
            when not missing(c.last_psa_dt) then min(c.last_psa_dt, &STUDY_CUTOFF_DT.)
            else min(adsl.lstalvdt, &STUDY_CUTOFF_DT.)
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
    where adsl.ittfl = 'Y';
quit;

data work.ttpsa_final;
    set work.ttpsa_derived;
    if not missing(ADT) and not missing(STARTDT) and ADT < STARTDT then
            putlog "WARNING: [ADTTE] event/censor date precedes time origin; floored to 1 day. " PARAMCD= USUBJID=;
        if ADT < STARTDT then ADT = STARTDT;
    AVAL = ADT - STARTDT + 1;
run;

/* -------------------------------------------------------------------------- */
/* PARAMETER 4: TIME TO TUMOR PROGRESSION (TTUMOR)  (ITT, RANDDT origin)       */
/* -------------------------------------------------------------------------- */
proc sql;
    create table work.tumor_prog_dates as
    select r.usubjid, min(r.ADT) as tumor_prog_dt format=yymmdd10.
    from adam.adrs as r
    inner join adam.adsl(keep=usubjid randdt) as a
        on r.usubjid = a.usubjid
    where r.PARAMCD = 'OVRLRESP' and r.AVALC = 'PD'
      and not missing(r.ADT) and r.ADT > a.RANDDT
    group by r.usubjid;
quit;

proc sql;
    create table work.tumor_censor_dates as
    select r.usubjid, max(r.ADT) as last_tumor_dt format=yymmdd10.
    from adam.adrs as r
    inner join adam.adsl(keep=usubjid randdt) as a
        on r.usubjid = a.usubjid
    where r.PARAMCD = 'OVRLRESP'
      and r.AVALC in ('CR', 'PR', 'SD', 'PD')
      and not missing(r.ADT)
      and r.ADT > a.RANDDT
    group by r.usubjid;
quit;

proc sql;
    create table work.ttum_derived as
    select
        adsl.studyid as STUDYID length=40,
        adsl.usubjid as USUBJID length=40,
        adsl.subjid as SUBJID length=10,
        adsl.siteid as SITEID length=10,
        adsl.trt01p as TRT01P length=20,
        adsl.trt01pn as TRT01PN,
        adsl.ittfl as ITTFL length=1,
        adsl.saffl as SAFFL length=1,
        'TTUMOR' as PARAMCD length=8,
        'Time to Tumor Progression' as PARAM length=40,
        4 as PARAMN,
        'EFFICACY' as PARCAT1 length=20,
        'DAYS' as AVALU length=8,
        adsl.randdt as STARTDT format=yymmdd10.,

        case
            when not missing(p.tumor_prog_dt) then p.tumor_prog_dt
            when not missing(c.last_tumor_dt) then min(c.last_tumor_dt, &STUDY_CUTOFF_DT.)
            else adsl.randdt
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
    where adsl.ittfl = 'Y';
quit;

data work.ttum_final;
    set work.ttum_derived;
    if not missing(ADT) and not missing(STARTDT) and ADT < STARTDT then
            putlog "WARNING: [ADTTE] event/censor date precedes time origin; floored to 1 day. " PARAMCD= USUBJID=;
        if ADT < STARTDT then ADT = STARTDT;
    AVAL = ADT - STARTDT + 1;
run;

/* Combine TTE parameters */
data adam.adtte(keep=STUDYID USUBJID SUBJID SITEID TRT01P TRT01PN ITTFL SAFFL
                     PARAMCD PARAM PARAMN PARCAT1 STARTDT ADT AVAL AVALU CNSR
                     EVNTDESC CNSDTDSC);
    set work.tte_base work.pfs_derived work.ttpain_final work.ttpsa_final work.ttum_final;
run;

proc sort data=adam.adtte;
    by usubjid PARAMCD;
run;

/* Clean up work library */
proc delete data=work.pd_dates work.sae_dates work.os_ttsae_raw work.nact_mapping work.pfs_raw
            work.prog_dates
            work.pain_pfs_prog_dates work.pfs_tumor_eval_dates work.pfs_psa_eval_dates
            work.pfs_pain_eval_dates work.pfs_eval_candidates work.pfs_last_eval_dates
            work.censor_dates work.ttpain_derived work.psa_prog_dates work.psa_censor_dates
            work.ttpsa_derived work.tumor_prog_dates work.tumor_censor_dates work.ttum_derived
            work.tte_base work.pfs_derived work.ttpain_final work.ttpsa_final work.ttum_final
            work.f042_pn work.f042_base_daily work.f042_base_component work.f042_base_values
            work.f042_base_ndays work.f042_base_discordant work.f042_base_eval work.f042_base
            work.f042_sv_dates work.f042_sv_summary0 work.f042_sv_summary work.f042_pn_visit_dates
            work.f042_schedule_raw work.f042_schedule work.f042_post_window work.f042_visit_daily
            work.f042_visit_component work.f042_visit_values work.f042_visit_ndays
            work.f042_visit_discordant work.f042_visit_eval work.f042_visits work.f042_visit_triggers
            work.f042_confirm_candidates work.f042_diary_events work.f042_rt_cm work.f042_rt_pr
            work.f042_rt_candidate_rows work.f042_rt_events work.f042_evidence_adrs
            work.f042_evidence_ds work.f042_evidence_rt work.f042_evidence work.f042_diary_qualified
            work.f042_primary_candidates work.f042_primary_event_dates work.f042_pain_pfs_prog_dates
            work.f042_pain_lastassess work.f042_pain_response_candidates
            work.f042_pain_response_events;
run;
quit;
