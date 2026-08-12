*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adsl_generation.sas
   Version: 2.4.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-08-09 (forensic remediation: source hierarchy and actual treatment)
   Standard: ADaMIG v1.3
   Input: sdtm.dm, sdtm.ex, sdtm.ds, sdtm.vs; staging.ls, staging.pn, staging.lb, staging.cm
   Output: adam.adsl
   Description: Generates Subject-Level Analysis Dataset (ADSL) including
                demographics, population flags, baseline covariates, and survival.

   ADaM phase rules (WS1_SDTM_E2E + ADaM entry criteria):
     - TRT01P from DM.ARM/ARMCD; TRT01A independently reflects administered IV drug.
     - EX supplies TRTSDT/TRTEDT/TRTDURD and actual-treatment evidence.
     - Row count must equal DM N (Path A: 371 MP).

   CRF grounding (D-012): ECOG on CRF VS; DS reasons on EOT/EOS.
     docs/workstreams/reviews/WS1_CRF_GROUNDING_D012_2026-07-09.md
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

/* Exposure dates. Planned treatment is never taken from EXTRT; actual treatment
   is independently classified from qualifying administered IV exposure below. */
proc sql;
    create table work.ex_dates as
    select 
        usubjid,
        min(exstdt) as trtsdt format=yymmdd10.,
        max(exendt) as trtedt format=yymmdd10.,
        (max(exendt) - min(exstdt) + 1) as trtdurd
    from sdtm.ex
    where not missing(exstdt)
    group by usubjid;
quit;

/* Actual treatment is distinct from planned/randomized treatment. The source
   contains one DM-planned MP subject with XRP6258 infusions; retain that
   discrepancy rather than silently copying TRT01P into TRT01A. */
proc sql;
    create table work.actual_trt as
    select usubjid,
           max(case when index(upcase(strip(extrt)), 'XRP') > 0 or
                         index(upcase(strip(extrt)), 'CABAZ') > 0 then 1 else 0 end) as has_cbzp,
           max(case when index(upcase(strip(extrt)), 'MITOX') > 0 then 1 else 0 end) as has_mp
    from sdtm.ex
    group by usubjid;
quit;

/* Retrieve survival disposition info from DS */
proc sql;
    create table work.survival_ds as
    select usubjid, dsstdt, dsterm, dsseq
    from sdtm.ds
    where dsdecod in ('DEATH', 'DEAD') and not missing(dsstdt);
quit;

proc sort data=work.survival_ds;
    by usubjid dsseq;
run;

data work.survival_approx;
    set work.survival_ds;
    by usubjid;
    retain dthdt dthcaus;
    length dthcaus $100 dthfl $1;
    if first.usubjid then do;
        dthdt = dsstdt;
        dthcaus = dsterm;
        dthfl = 'Y';
        output;
    end;
    keep usubjid dthfl dthdt dthcaus;
    format dthdt yymmdd10.;
run;

/* Prefer complete source-reported death dates from SUPPAE over week-derived DS
   point estimates. Multiple AE rows may repeat the same death date. */
proc sql;
    create table work.suppae_death as
    select usubjid,
           min(input(substr(aedthdtc, 1, 10), ? yymmdd10.)) as exact_dthdt format=yymmdd10.
    from staging.ae
    where not missing(aedthdtc)
      and prxmatch('/^[0-9]{4}-[0-9]{2}-[0-9]{2}/', strip(aedthdtc))
    group by usubjid;

    create table work.survival as
    select coalesce(a.usubjid, e.usubjid) as usubjid length=40,
           'Y' as dthfl length=1,
           coalesce(e.exact_dthdt, a.dthdt) as dthdt format=yymmdd10.,
           a.dthcaus length=100
    from work.survival_approx as a
    full join work.suppae_death as e on a.usubjid = e.usubjid;
quit;

/* Retrieve the latest dated evidence of subject contact/assessment across
   disposition, visits, exposure, vital signs, laboratories, lesions, and pain.
   Medication end dates are deliberately excluded because they may be planned. */
proc sql;
    create table work.lstalv_candidates as
    select usubjid, dsstdt as contact_dt from sdtm.ds where not missing(dsstdt)
    union all select usubjid, exstdt from sdtm.ex where not missing(exstdt)
    union all select usubjid, exendt from sdtm.ex where not missing(exendt)
    union all select usubjid, vsdt from sdtm.vs where not missing(vsdt)
    union all select usubjid, lbdt from sdtm.lb where not missing(lbdt)
    union all select usubjid, input(substr(lsdtc, 1, 10), ? yymmdd10.)
      from staging.ls where not missing(lsdtc)
    union all select usubjid, input(substr(pndtc, 1, 10), ? yymmdd10.)
      from staging.pn where not missing(pndtc)
    union all select usubjid, input(substr(svstdtc, 1, 10), ? yymmdd10.)
      from staging.sv where not missing(svstdtc)
    union all select usubjid, input(substr(svendtc, 1, 10), ? yymmdd10.)
      from staging.sv where not missing(svendtc);

    create table work.lstalv as
    select usubjid, max(contact_dt) as lstalvdt format=yymmdd10.
    from work.lstalv_candidates
    where not missing(contact_dt)
    group by usubjid;
quit;

/* 1. ECOGBL */
proc sql;
    create table work.ecog as
    select usubjid, vsstresn as ecogbl
    from sdtm.vs
    where vstestcd = 'ECOG' and vsblfl = 'Y';
quit;

/* 2. MEASDISF */
proc sql;
    create table work.meas as
    select distinct usubjid, 'Y' as measdisf length=1
    from staging.ls
    where lscat = 'TARGET' and visit = 'BASELINE';
quit;

/* 3. VISCFL */
proc sql;
    create table work.visc as
    select distinct usubjid, 'Y' as viscfl length=1
    from staging.ls
    where lsloc in ('LIVER', 'LUNGS', 'KIDNEYS', 'PANCREAS', 'ADRENAL', 'BRAIN / CNS') and visit = 'BASELINE';
quit;

/* 4. PAINBL: protocol diary baseline (TRTSDT-6 through TRTSDT), with
   component-specific aggregation and at least five non-discordant diary days. */
proc sql;
    create table work.pn_trt as
    select pn.usubjid, pn.pntestcd, pn.pnstresn,
           input(pn.pndtc, ? yymmdd10.) as pndt format=yymmdd10.
    from staging.pn as pn;
quit;

proc sql;
    create table work.pn_base_raw as
    select p.usubjid, p.pntestcd, p.pndt, p.pnstresn
    from work.pn_trt as p
    inner join work.ex_dates as ex on p.usubjid = ex.usubjid
    where p.pntestcd in ('PAININT', 'ANSCORE')
      and not missing(p.pndt) and not missing(p.pnstresn)
      and ex.trtsdt - 6 <= p.pndt <= ex.trtsdt;

    create table work.pn_base_daily as
    select usubjid, pntestcd, pndt,
           min(pnstresn) as day_value
    from work.pn_base_raw
    group by usubjid, pntestcd, pndt
    having count(distinct pnstresn) = 1;

    create table work.pn_base_component as
    select usubjid, pntestcd,
           count(*) as n_valid_days,
           median(day_value) as median_value,
           mean(day_value) as mean_value
    from work.pn_base_daily
    group by usubjid, pntestcd;

    create table work.pain_base as
    select usubjid, 'Y' as painbl length=1
    from work.pn_base_component
    group by usubjid
    having max(case when pntestcd = 'PAININT' and n_valid_days >= 5 and median_value >= 2
                    then 1 else 0 end) = 1
        or max(case when pntestcd = 'ANSCORE' and n_valid_days >= 5 and mean_value >= 10
                    then 1 else 0 end) = 1;
quit;

/* 5. Baseline Labs */
proc sql;
    create table work.labs_base as
    select usubjid, lbtestcd, lbstresn
    from staging.lb
    where lbblfl = 'Y' and lbtestcd in ('PSA', 'ALP', 'HGB');
quit;

proc sort data=work.labs_base;
    by usubjid;
run;

proc transpose data=work.labs_base out=work.labs_wide(drop=_name_ _label_);
    by usubjid;
    id lbtestcd;
    var lbstresn;
run;

data work.labs_ready;
    set work.labs_wide;
    rename PSA = PSABL ALP = ALPBL HGB = HGBBL;
run;

/* 6. Docetaxel Prior History */
proc sql;
    create table work.docetaxel_recs as
    select usubjid, cmrltl, cmrson
    from staging.cm
    where cmdecod = 'DOCETAXEL' and cmcat = 'PRIOR TREATMENT CHEMOTHERAPY';
quit;

proc sql;
    create table work.docetaxel_resp as
    select distinct usubjid, 'Y' as docresp length=1
    from work.docetaxel_recs
    where cmrltl in ('COMPLETE RESPONSE', 'PARTIAL RESPONSE');
    
    create table work.docetaxel_prog as
    select distinct usubjid, 'DURING' as docprog length=10
    from work.docetaxel_recs
    where cmrson = 'DISEASE PROGRESSION' or cmrltl = 'PROGRESSIVE DISEASE';
quit;

proc sort data=work.docetaxel_resp; by usubjid; run;
proc sort data=work.docetaxel_prog; by usubjid; run;

data work.docetaxel_summary;
    merge work.docetaxel_resp work.docetaxel_prog;
    by usubjid;
run;

/* Assemble ADSL */
proc sql;
    create table adam.adsl as
    select
        "&STUDYID." as STUDYID length=40,
        dm.usubjid as USUBJID length=40,
        dm.subjid as SUBJID length=10,
        substr(dm.subjid, 1, 3) as SITEID length=10,

        dm.age as AGE,
        case
            when dm.age < &AGE_STRAT_CUT. then '<65'
            else '>=65'
        end as AGEGR1 length=10,
        case
            when dm.age < &AGE_STRAT_CUT. then 1
            else 2
        end as AGEGR1N,
        dm.race as RACE length=40,
        'NOT REPORTED' as ETHNIC length=40,
        'M' as SEX length=1,

        /* Planned arm from DM; actual arm from administered IV antineoplastic. */
        case
            when index(upcase(strip(dm.arm)), 'MITOX') > 0
                 or strip(dm.armcd) = 'A'
                then 'MP'
            when index(upcase(strip(dm.arm)), 'CABAZ') > 0
                 or index(upcase(strip(dm.arm)), 'XRP') > 0
                then 'CbzP'
            else "&TRT01P_CODE."
        end as TRT01P length=20,
        case
            when index(upcase(strip(dm.arm)), 'MITOX') > 0
                 or strip(dm.armcd) = 'A'
                then 2
            when index(upcase(strip(dm.arm)), 'CABAZ') > 0
                 or index(upcase(strip(dm.arm)), 'XRP') > 0
                then 1
            else &TRT01PN_CODE.
        end as TRT01PN,
        case when act.has_cbzp = 1 then 'CbzP'
             when act.has_mp = 1 then 'MP'
             else calculated TRT01P end as TRT01A length=20,
        case when act.has_cbzp = 1 then 1
             when act.has_mp = 1 then 2
             else calculated TRT01PN end as TRT01AN,

        dm.randdt as RANDDT format=yymmdd10.,
        ex.trtsdt as TRTSDT format=yymmdd10.,
        ex.trtedt as TRTEDT format=yymmdd10.,
        ex.trtdurd as TRTDURD,

        coalesce(dm.itt, 'N') as ITTFL length=1,
        coalesce(dm.safety, 'N') as SAFFL length=1,
        coalesce(dm.pprot, 'N') as PPROTFL length=1,

        coalesce(srv.dthfl, 'N') as DTHFL length=1,
        srv.dthdt as DTHDT format=yymmdd10.,
        srv.dthcaus as DTHCAUS length=100,
        case when srv.dthfl = 'Y' and not missing(srv.dthdt) and
                       lst.lstalvdt > srv.dthdt then srv.dthdt
             else lst.lstalvdt end as LSTALVDT format=yymmdd10.,

        /* No unapproved constant imputation: retain missing collected covariates.
           *IF remains N because no value is imputed in the real-data track. */
        ecog.ecogbl as ECOGBL,
        'N' as ECOGBLIF length=1,
        coalesce(meas.measdisf, 'N') as MEASDISF length=1,
        coalesce(visc.viscfl, 'N') as VISCFL length=1,
        coalesce(pain.painbl, 'N') as PAINBL length=1,
        labs.PSABL as PSABL,
        'N' as PSABLIF length=1,
        labs.ALPBL as ALPBL,
        'N' as ALPBLIF length=1,
        . as ALBBL,
        ' ' as ALBBLIF length=1,
        . as LDHBL,
        ' ' as LDHBLIF length=1,
        labs.HGBBL as HGBBL,
        'N' as HGBBLIF length=1,
        coalesce(doc.docprog, 'AFTER') as DOCPROG length=10,
        coalesce(doc.docresp, 'N') as DOCRESP length=1
    from sdtm.dm as dm
    left join work.ex_dates as ex on dm.usubjid = ex.usubjid
    left join work.actual_trt as act on dm.usubjid = act.usubjid
    left join work.survival as srv on dm.usubjid = srv.usubjid
    left join work.lstalv as lst on dm.usubjid = lst.usubjid
    left join work.ecog as ecog on dm.usubjid = ecog.usubjid
    left join work.meas as meas on dm.usubjid = meas.usubjid
    left join work.visc as visc on dm.usubjid = visc.usubjid
    left join work.pain_base as pain on dm.usubjid = pain.usubjid
    left join work.labs_ready as labs on dm.usubjid = labs.usubjid
    left join work.docetaxel_summary as doc on dm.usubjid = doc.usubjid;
quit;

/* ADaM QC: one row per DM subject; arm from DM map only */
data _null_;
    if 0 then set adam.adsl nobs=n_adsl;
    if 0 then set sdtm.dm nobs=n_dm;
    putlog "NOTE: [ADSL-QC] ADSL n=" n_adsl " DM n=" n_dm;
    if n_adsl ne n_dm then
        putlog "WARNING: [ADSL-QC] ADSL row count differs from DM — check joins.";
run;
proc freq data=adam.adsl noprint;
    tables TRT01P*TRT01A / out=work.adsl_trt;
run;
data _null_;
    set work.adsl_trt;
    putlog "NOTE: [ADSL-QC] TRT01P=" TRT01P " TRT01A=" TRT01A " n=" COUNT;
run;

/* Clean up work library */
proc delete data=work.ex_dates work.actual_trt work.survival_ds work.survival_approx
            work.suppae_death work.survival work.lstalv_candidates work.lstalv work.ecog
            work.meas work.visc work.pn_trt work.pn_base_raw work.pn_base_daily
            work.pn_base_component work.pain_base work.labs_base work.labs_wide
            work.labs_ready work.docetaxel_recs work.docetaxel_resp work.docetaxel_prog
            work.docetaxel_summary work.adsl_trt;
run;
quit;
