/* ==============================================================================
   Program: F042_phase2_pain_derivation.sas
   Version: 1.0.0
   Author: Antony Bevan, Clinical Programming
   Scope: Path A Phase 2 implementation of the adopted F-042 pain rules.

   This is an independent SAS implementation of the controlled R track.  It
   creates WORK-only lineage and date tables consumed by A_adtte_generation.sas;
   it does not itself write a submission output or alter the release seal.

   Adopted controls:
     - baseline Cycle 1 window is TRTSDT-6 through TRTSDT;
     - PAININT is a median and ANSCORE is a mean, each requiring >=5 distinct
       valid calendar dates; missing baseline values are not zero-imputed;
     - post-baseline components are separately evaluable over a seven-day
       window, with exact same-test/date/value duplicates collapsed and
       discordant same-test/date values non-evaluable;
     - SV complete date is preferred, with maximum complete PN date as an
       explicit fallback; unscheduled VISITNUM=99 is excluded;
     - same-component triggers must occur at the immediately next scheduled
       evaluation at least 21 days later; terminal singletons do not qualify;
     - T-11-5 pain response is evaluated in the PAINBL='Y' ITT subset only,
       with component-specific response and the same immediate-next-visit
       >=21-day confirmation; no synthetic PN response is created;
     - direct-intent local palliative/antalgic radiotherapy is the standalone
       RT branch from the union of CM and PR; generic, prior/history and
       radiopharmaceutical records remain adjudication lineage;
     - diary events require ADRS RECIST PD, DS progression-week evidence, or
       qualifying RT evidence no later than the confirming visit.
   ============================================================================== */

/* ------------------------- governed PN preparation ------------------------- */
data work.f042_pn;
    set staging.pn;
    length PNDT 8;
    PNDT = input(strip(PNDTC), ?? yymmdd10.);
    PNTESTCD = upcase(strip(PNTESTCD));
    VISIT = strip(VISIT);
    format PNDT yymmdd10.;
    if not missing(PNSTRESN)
       and PNTESTCD in ('PAININT', 'ANSCORE');
run;

/* ------------------------ baseline component summary ---------------------- */
proc sql;
    create table work.f042_base_daily as
    select p.usubjid, p.pntestcd, p.pndt,
           count(distinct p.pnstresn) as n_distinct_values,
           case when calculated n_distinct_values = 1
                then min(p.pnstresn) else . end as day_value,
           case when calculated n_distinct_values > 1
                then 1 else 0 end as discordant_day
    from work.f042_pn as p
    inner join adam.adsl as a
      on p.usubjid = a.usubjid
    where a.ittfl = 'Y'
      and not missing(p.pndt)
      and p.pndt between a.trtsdt - 6 and a.trtsdt
    group by p.usubjid, p.pntestcd, p.pndt;

    create table work.f042_base_component as
    select usubjid, pntestcd,
           sum(case when not missing(day_value) then 1 else 0 end) as n_valid_days,
           sum(discordant_day) as discordant_days,
           case when pntestcd = 'PAININT' then median(day_value)
                else mean(day_value) end as component_value,
           case when calculated n_valid_days >= 5
                      and calculated discordant_days = 0
                then 1 else 0 end as component_evaluable
    from work.f042_base_daily
    group by usubjid, pntestcd;
quit;

proc sort data=work.f042_base_component; by usubjid; run;
proc transpose data=work.f042_base_component out=work.f042_base_values(drop=_name_)
               prefix=base_value_;
    by usubjid;
    id pntestcd;
    var component_value;
run;
proc transpose data=work.f042_base_component out=work.f042_base_ndays(drop=_name_)
               prefix=base_n_days_;
    by usubjid;
    id pntestcd;
    var n_valid_days;
run;
proc transpose data=work.f042_base_component out=work.f042_base_discordant(drop=_name_)
               prefix=base_discordant_;
    by usubjid;
    id pntestcd;
    var discordant_days;
run;
proc transpose data=work.f042_base_component out=work.f042_base_eval(drop=_name_)
               prefix=base_eval_;
    by usubjid;
    id pntestcd;
    var component_evaluable;
run;

data work.f042_base;
    merge work.f042_base_values work.f042_base_ndays
          work.f042_base_discordant work.f042_base_eval;
    by usubjid;
    base_ppi = base_value_PAININT;
    base_an  = base_value_ANSCORE;
    base_n_days_ppi = base_n_days_PAININT;
    base_n_days_an  = base_n_days_ANSCORE;
    base_discordant_ppi = base_discordant_PAININT;
    base_discordant_an  = base_discordant_ANSCORE;
    base_eval_ppi = base_eval_PAININT;
    base_eval_an  = base_eval_ANSCORE;
    keep usubjid base_ppi base_an base_n_days_ppi base_n_days_an
         base_discordant_ppi base_discordant_an base_eval_ppi base_eval_an;
run;

/* --------------------------- visit-date hierarchy ------------------------- */
data work.f042_sv_dates;
    set staging.sv;
    SV_DATE = input(strip(SVSTDTC), ?? yymmdd10.);
    VISIT = strip(VISIT);
    format SV_DATE yymmdd10.;
    if not missing(VISITNUM) and VISITNUM not in (0, 99);
run;

proc sql;
    create table work.f042_sv_summary0 as
    select usubjid, visitnum, visit,
           count(*) as sv_record_count,
           count(distinct sv_date) as sv_complete_date_count,
           min(sv_date) as sv_date_min format=yymmdd10.
    from work.f042_sv_dates
    group by usubjid, visitnum, visit;
quit;

data work.f042_sv_summary;
    set work.f042_sv_summary0;
    if sv_complete_date_count = 1 then sv_date = sv_date_min;
    else sv_date = .;
    sv_date_conflict = (sv_complete_date_count > 1);
    format sv_date yymmdd10.;
run;

proc sql;
    create table work.f042_pn_visit_dates as
    select p.usubjid, p.visitnum, p.visit,
           count(distinct p.pndt) as pn_complete_date_count,
           max(p.pndt) as pn_max_date format=yymmdd10.
    from work.f042_pn as p
    inner join adam.adsl as a
      on p.usubjid = a.usubjid
    where a.ittfl = 'Y'
      and p.visitnum > 1 and p.visitnum ne 99
      and not missing(p.pndt) and p.pndt > a.trtsdt
    group by p.usubjid, p.visitnum, p.visit;

    create table work.f042_schedule_raw as
    select coalesce(s.usubjid, p.usubjid) as usubjid length=40,
           coalesce(s.visitnum, p.visitnum) as visitnum,
           coalescec(s.visit, p.visit) as visit length=200,
           s.sv_date, s.sv_date_conflict,
           p.pn_max_date
    from work.f042_sv_summary as s
    full join work.f042_pn_visit_dates as p
      on s.usubjid = p.usubjid
     and s.visitnum = p.visitnum
     and s.visit = p.visit
    inner join adam.adsl as a
      on coalesce(s.usubjid, p.usubjid) = a.usubjid
     and a.ittfl = 'Y'
    where coalesce(s.visitnum, p.visitnum) > 1
      and coalesce(s.visitnum, p.visitnum) ne 99;
quit;

data work.f042_schedule;
    set work.f042_schedule_raw;
    if not sv_date_conflict and not missing(sv_date) then do;
        visit_date = sv_date;
        visit_date_source = 'SVSTDTC';
    end;
    else if sv_date_conflict and not missing(pn_max_date) then do;
        visit_date = pn_max_date;
        visit_date_source = 'SV_CONFLICT_PN_MAX_FALLBACK';
    end;
    else if not missing(pn_max_date) then do;
        visit_date = pn_max_date;
        visit_date_source = 'PN_MAX_FALLBACK';
    end;
    else if sv_date_conflict then do;
        visit_date = .;
        visit_date_source = 'SV_CONFLICT_MISSING';
    end;
    else do;
        visit_date = .;
        visit_date_source = 'MISSING';
    end;
    format visit_date yymmdd10.;
run;

/* -------------------------- post-baseline summaries ----------------------- */
proc sql;
    create table work.f042_post_window as
    select p.usubjid, p.visitnum, p.visit, p.pntestcd, p.pndt,
           p.pnstresn, s.visit_date, s.visit_date_source
    from work.f042_pn as p
    inner join work.f042_schedule as s
      on p.usubjid = s.usubjid
     and p.visitnum = s.visitnum
     and p.visit = s.visit
    where not missing(s.visit_date)
      and p.pndt between s.visit_date - 6 and s.visit_date;

    create table work.f042_visit_daily as
    select usubjid, visitnum, visit, pntestcd, pndt,
           count(distinct pnstresn) as n_distinct_values,
           case when calculated n_distinct_values = 1
                then min(pnstresn) else . end as day_value,
           case when calculated n_distinct_values > 1
                then 1 else 0 end as discordant_day
    from work.f042_post_window
    group by usubjid, visitnum, visit, pntestcd, pndt;

    create table work.f042_visit_component as
    select usubjid, visitnum, visit, pntestcd,
           sum(case when not missing(day_value) then 1 else 0 end) as n_valid_days,
           sum(discordant_day) as discordant_days,
           case when pntestcd = 'PAININT' then median(day_value)
                else mean(day_value) end as component_value,
           case when calculated n_valid_days >= 5
                      and calculated discordant_days = 0
                then 1 else 0 end as component_evaluable
    from work.f042_visit_daily
    group by usubjid, visitnum, visit, pntestcd;
quit;

proc sort data=work.f042_visit_component; by usubjid visitnum visit; run;
proc transpose data=work.f042_visit_component out=work.f042_visit_values(drop=_name_)
               prefix=component_value_;
    by usubjid visitnum visit;
    id pntestcd;
    var component_value;
run;
proc transpose data=work.f042_visit_component out=work.f042_visit_ndays(drop=_name_)
               prefix=n_valid_days_;
    by usubjid visitnum visit;
    id pntestcd;
    var n_valid_days;
run;
proc transpose data=work.f042_visit_component out=work.f042_visit_discordant(drop=_name_)
               prefix=discordant_days_;
    by usubjid visitnum visit;
    id pntestcd;
    var discordant_days;
run;
proc transpose data=work.f042_visit_component out=work.f042_visit_eval(drop=_name_)
               prefix=component_evaluable_;
    by usubjid visitnum visit;
    id pntestcd;
    var component_evaluable;
run;

proc sort data=work.f042_schedule; by usubjid visitnum visit; run;
data work.f042_visits;
    merge work.f042_schedule work.f042_visit_values work.f042_visit_ndays
          work.f042_visit_discordant work.f042_visit_eval;
    by usubjid visitnum visit;
    ppi_value = component_value_PAININT;
    as_value  = component_value_ANSCORE;
    ppi_evaluable = coalesce(component_evaluable_PAININT, 0);
    as_evaluable  = coalesce(component_evaluable_ANSCORE, 0);
    drop component_value_PAININT component_value_ANSCORE
         component_evaluable_PAININT component_evaluable_ANSCORE;
run;

proc sql;
    create table work.f042_visit_triggers as
    select v.*, b.base_ppi, b.base_an, b.base_eval_ppi, b.base_eval_an,
           b.base_n_days_ppi, b.base_n_days_an,
           b.base_discordant_ppi, b.base_discordant_an
    from work.f042_visits as v
    left join work.f042_base as b
      on v.usubjid = b.usubjid;
quit;

data work.f042_visit_triggers;
    set work.f042_visit_triggers;
    if ppi_evaluable and base_eval_ppi and not missing(ppi_value)
       and not missing(base_ppi)
       and coalesce(ppi_value, 0) - coalesce(base_ppi, 0) >= 1
       then ppi_trigger = 1;
    else ppi_trigger = 0;
    as_trigger = 0;
    if as_evaluable and base_eval_an and not missing(as_value)
       and not missing(base_an) and base_an > 0 then do;
        if (coalesce(as_value, 0) - coalesce(base_an, 0)) /
             coalesce(base_an, 1) >= 0.25 then as_trigger = 1;
    end;
run;

/* ---------------------------- pain response (T-11-5) ---------------------- */
/*
   This aggregate is deliberately produced in the independent SAS track even
   though the reporting TFL is rendered by the R output program.  It provides
   a directly programmable cross-language challenge for the real MP arm and
   keeps the synthetic CbzP arm out of a PN-derived response denominator.
*/
proc sql;
    create table work.f042_pain_response_candidates as
    select a.usubjid,
           a.painbl,
           x.visitnum as response_visitnum,
           x.visit_date as event_date format=yymmdd10.,
           y.visitnum as confirming_visitnum,
           y.visit_date as confirming_date format=yymmdd10.,
           x.visit_date_source as event_date_source length=40,
           y.visit_date_source as confirming_date_source length=40,
           case
             when (x.base_eval_ppi = 1 and x.base_ppi >= 2)
               or (x.base_eval_an = 1 and x.base_an >= 10)
             then 1 else 0
           end as baseline_eligible,
           case
             when calculated baseline_eligible = 1
              and x.ppi_evaluable = 1 and x.as_evaluable = 1
              and not missing(x.base_ppi) and not missing(x.base_an)
              and not missing(x.ppi_value) and not missing(x.as_value)
              and x.base_ppi - x.ppi_value >= 2
              and x.as_value <= x.base_an
             then 1 else 0
           end as ppi_response_initial,
           case
             when calculated baseline_eligible = 1
              and x.ppi_evaluable = 1 and x.as_evaluable = 1
              and not missing(x.base_ppi) and not missing(x.base_an)
              and not missing(x.ppi_value) and not missing(x.as_value)
              and x.base_an > 0
              and (x.base_an - x.as_value) / x.base_an >= 0.5
              and x.ppi_value <= x.base_ppi
             then 1 else 0
           end as as_response_initial,
           case
             when calculated baseline_eligible = 1
              and y.ppi_evaluable = 1 and y.as_evaluable = 1
              and not missing(x.base_ppi) and not missing(x.base_an)
              and not missing(y.ppi_value) and not missing(y.as_value)
              and x.base_ppi - y.ppi_value >= 2
              and y.as_value <= x.base_an
             then 1 else 0
           end as ppi_response_confirming,
           case
             when calculated baseline_eligible = 1
              and y.ppi_evaluable = 1 and y.as_evaluable = 1
              and not missing(x.base_ppi) and not missing(x.base_an)
              and not missing(y.ppi_value) and not missing(y.as_value)
              and x.base_an > 0
              and (x.base_an - y.as_value) / x.base_an >= 0.5
              and y.ppi_value <= x.base_ppi
             then 1 else 0
           end as as_response_confirming,
           case
             when calculated ppi_response_initial = 1
              and calculated ppi_response_confirming = 1
             then 1 else 0
           end as ppi_confirmed,
           case
             when calculated as_response_initial = 1
              and calculated as_response_confirming = 1
             then 1 else 0
           end as as_confirmed
    from work.f042_visit_triggers as x
    inner join adam.adsl as a
      on x.usubjid = a.usubjid
     and a.ittfl = 'Y'
     and upcase(strip(a.painbl)) = 'Y'
    left join work.f042_visit_triggers as y
      on x.usubjid = y.usubjid
     and y.visitnum = (select min(z.visitnum)
                       from work.f042_visit_triggers as z
                       where z.usubjid = x.usubjid
                         and z.visitnum > x.visitnum)
    where not missing(x.visit_date)
      and not missing(y.visit_date)
      and y.visit_date - x.visit_date >= 21;

    create table work.f042_pain_response_events as
    select usubjid,
           event_date,
           confirming_date,
           event_date_source,
           confirming_date_source,
           case when ppi_confirmed = 1 and as_confirmed = 1 then 'PPI+AS'
                when ppi_confirmed = 1 then 'PPI'
                when as_confirmed = 1 then 'AS'
                else '' end as response_component length=8
    from work.f042_pain_response_candidates
    where ppi_confirmed = 1 or as_confirmed = 1;
quit;

proc sort data=work.f042_pain_response_events;
    by usubjid event_date;
run;
data work.f042_pain_response_events;
    set work.f042_pain_response_events;
    by usubjid event_date;
    if first.usubjid;
run;

/*
   Export the independently derived subject-level response set for the local
   cross-language gate.  The orchestrator downloads this transient file from
   ODA, reconciles it to the R derivation, and removes it after comparison; only
   aggregate PASS/FAIL evidence is retained in the repository.
*/
proc export data=work.f042_pain_response_events
    outfile="&PROJ_ROOT.&PATH_SEP.04_analysis_datasets&PATH_SEP.adam&PATH_SEP.f042_pain_response_prod.csv"
    dbms=csv replace;
run;

proc sql;
    /* Immediate next scheduled visit: the MIN visitnum greater than the
       trigger visit.  Missing or non-evaluable rows therefore block the pair. */
    create table work.f042_confirm_candidates as
    select a.usubjid, a.visitnum as trig_visitnum,
           a.visit_date as event_date format=yymmdd10.,
           b.visitnum as confirming_visitnum,
           b.visit_date as confirming_date format=yymmdd10.,
           a.visit_date_source as event_date_source,
           b.visit_date_source as confirming_date_source,
           case when a.ppi_trigger = 1 and b.ppi_trigger = 1
                     and not missing(a.visit_date)
                     and not missing(b.visit_date)
                     and coalesce(b.visit_date, 0) - coalesce(a.visit_date, 0) >= 21
                then 1 else 0 end as ppi_confirmed,
           case when a.as_trigger = 1 and b.as_trigger = 1
                     and not missing(a.visit_date)
                     and not missing(b.visit_date)
                     and coalesce(b.visit_date, 0) - coalesce(a.visit_date, 0) >= 21
                then 1 else 0 end as as_confirmed
    from work.f042_visit_triggers as a
    left join work.f042_visit_triggers as b
      on a.usubjid = b.usubjid
     and b.visitnum = (select min(c.visitnum)
                       from work.f042_visit_triggers as c
                       where c.usubjid = a.usubjid
                         and c.visitnum > a.visitnum);

    create table work.f042_diary_events as
    select usubjid, event_date, confirming_date,
           event_date_source, confirming_date_source,
           case when ppi_confirmed = 1 and as_confirmed = 1 then 'PPI+AS'
                when ppi_confirmed = 1 then 'PPI'
                when as_confirmed = 1 then 'AS' else '' end as component length=8
    from work.f042_confirm_candidates
    where ppi_confirmed = 1 or as_confirmed = 1;
quit;

/* --------------------------- CM + PR RT lineage --------------------------- */
data work.f042_rt_cm;
    set staging.cm;
    length source_domain $2 source_seq $40 treatment_text intent_text
           category_text exclusion_reason $500;
    source_domain = 'CM';
    source_seq = strip(put(cmseq, best32.));
    treatment_text = catx(' | ', strip(cmtrt), strip(cmdecod));
    intent_text = strip(cmtrt);
    category_text = strip(cmcat);
    event_date = input(strip(cmstdtc), ?? yymmdd10.);
    radiation_concept = prxmatch('/radiat|radiotherapy|radiation|photon|\bcgy\b|\bgray\b|beam/i', treatment_text) > 0;
    explicit_intent = prxmatch('/\b(palliative|antalgic)\b/i', intent_text) > 0;
    radiopharm_concept = prxmatch('/radiopharm|radium|strontium|samarium|radioisotope|radionuclide/i', treatment_text) > 0;
    prior_category = prxmatch('/\bprior\b|history/i', category_text) > 0;
    rt_inventory_candidate = radiation_concept and explicit_intent;
    rt_autoqualifies = radiation_concept and explicit_intent
                       and not radiopharm_concept and not prior_category;
    if not radiation_concept then exclusion_reason = 'NO_RADIATION_CONCEPT';
    else if not explicit_intent then exclusion_reason = 'NO_EXPLICIT_PALLIATIVE_OR_ANTALGIC_INTENT';
    else if radiopharm_concept then exclusion_reason = 'RADIOPHARMACEUTICAL_CLASSIFICATION_OR_TREATMENT';
    else if prior_category then exclusion_reason = 'PRIOR_OR_HISTORY_CATEGORY';
    else exclusion_reason = '';
    format event_date yymmdd10.;
    if rt_inventory_candidate;
    keep usubjid source_domain source_seq treatment_text intent_text category_text
         event_date radiation_concept explicit_intent radiopharm_concept
         prior_category rt_inventory_candidate rt_autoqualifies exclusion_reason;
run;

data work.f042_rt_pr;
    set staging.pr;
    length source_domain $2 source_seq $40 treatment_text intent_text
           category_text exclusion_reason $500;
    source_domain = 'PR';
    source_seq = strip(put(prseq, best32.));
    treatment_text = strip(prtrt);
    intent_text = strip(prtrt);
    category_text = strip(prcat);
    event_date = input(strip(prdtc), ?? yymmdd10.);
    radiation_concept = prxmatch('/radiat|radiotherapy|radiation|photon|\bcgy\b|\bgray\b|beam/i', treatment_text) > 0;
    explicit_intent = prxmatch('/\b(palliative|antalgic)\b/i', intent_text) > 0;
    radiopharm_concept = prxmatch('/radiopharm|radium|strontium|samarium|radioisotope|radionuclide/i', treatment_text) > 0;
    prior_category = prxmatch('/\bprior\b|history/i', category_text) > 0;
    rt_inventory_candidate = radiation_concept and explicit_intent;
    rt_autoqualifies = radiation_concept and explicit_intent
                       and not radiopharm_concept and not prior_category;
    if not radiation_concept then exclusion_reason = 'NO_RADIATION_CONCEPT';
    else if not explicit_intent then exclusion_reason = 'NO_EXPLICIT_PALLIATIVE_OR_ANTALGIC_INTENT';
    else if radiopharm_concept then exclusion_reason = 'RADIOPHARMACEUTICAL_CLASSIFICATION_OR_TREATMENT';
    else if prior_category then exclusion_reason = 'PRIOR_OR_HISTORY_CATEGORY';
    else exclusion_reason = '';
    format event_date yymmdd10.;
    if rt_inventory_candidate;
    keep usubjid source_domain source_seq treatment_text intent_text category_text
         event_date radiation_concept explicit_intent radiopharm_concept
         prior_category rt_inventory_candidate rt_autoqualifies exclusion_reason;
run;

proc sql;
    create table work.f042_rt_candidate_rows as
    select x.*, a.randdt,
           case when not missing(x.event_date)
                then cats(x.usubjid, '|', put(x.event_date, yymmddn8.))
                else cats(x.usubjid, '|', x.source_domain, '|', x.source_seq)
           end as event_group length=120
    from (select * from work.f042_rt_cm union all select * from work.f042_rt_pr) as x
    inner join adam.adsl as a on x.usubjid = a.usubjid
    where (not missing(x.event_date) and x.event_date > a.randdt)
       or missing(x.event_date);
quit;

proc sort data=work.f042_rt_candidate_rows; by usubjid event_group; run;
data work.f042_rt_events;
    length source_domains source_keys source_treatment_text source_exclusion_reasons $2000;
    retain source_domains source_keys source_treatment_text source_exclusion_reasons
           source_record_count inventory_candidate_count all_rt_autoqualifies;
    set work.f042_rt_candidate_rows;
    by usubjid event_group;
    if first.event_group then do;
        source_domains = '';
        source_keys = '';
        source_treatment_text = '';
        source_exclusion_reasons = '';
        source_record_count = 0;
        inventory_candidate_count = 0;
        all_rt_autoqualifies = 1;
    end;
    source_record_count + 1;
    inventory_candidate_count + 1;
    source_domains = catx(';', source_domains, source_domain);
    source_keys = catx(';', source_keys, cats(source_domain, ':', source_seq));
    source_treatment_text = catx(' || ', source_treatment_text, treatment_text);
    if not missing(exclusion_reason) then
        source_exclusion_reasons = catx(';', source_exclusion_reasons, exclusion_reason);
    if not rt_autoqualifies then all_rt_autoqualifies = 0;
    if last.event_group then do;
        rt_autoqualifies = all_rt_autoqualifies;
        if missing(event_date) then do;
            rt_autoqualifies = 0;
            source_exclusion_reasons = catx(';', source_exclusion_reasons, 'MISSING_START_DATE');
        end;
        event_source = 'RT';
        treatment_text = source_treatment_text;
        exclusion_reasons = source_exclusion_reasons;
        output;
    end;
    keep usubjid event_date event_group event_source source_domains source_keys
         source_record_count inventory_candidate_count rt_autoqualifies
         exclusion_reasons treatment_text;
    format event_date yymmdd10.;
run;

/* ------------------------- disease-support evidence ---------------------- */
proc sql;
    create table work.f042_evidence_adrs as
    select r.usubjid, 'RADIOLOGICAL_RECIST_PD' as evidence_type length=40,
           r.adt as evidence_date format=yymmdd10.,
           r.adt as latest_possible_date format=yymmdd10.,
           cats('ADRS:', put(r.adt, yymmddn8.)) as evidence_key length=80
    from adam.adrs as r
    inner join adam.adsl as a on r.usubjid = a.usubjid
    where upcase(strip(r.paramcd)) = 'OVRLRESP'
      and upcase(strip(r.avalc)) = 'PD'
      and not missing(r.adt) and r.adt >= a.randdt;
quit;

proc sql;
    create table work.f042_evidence_ds as
    select d.usubjid, 'CLINICAL_DS_PROGRESSION_WEEK' as evidence_type length=40,
           a.randdt + 7 * (d.dsstwk - 1) as evidence_date format=yymmdd10.,
           a.randdt + 7 * (d.dsstwk - 1) + 4 as latest_possible_date format=yymmdd10.,
           cats('DS:', put(d.dsseq, best32.)) as evidence_key length=80
    from staging.ds as d
    inner join adam.adsl as a on d.usubjid = a.usubjid
    where upcase(strip(d.dsdecod)) in ('DISEASE PROGRESSION', 'PROGRESSION')
      and not missing(d.dsstwk)
      and a.randdt + 7 * (d.dsstwk - 1) >= a.randdt;

    create table work.f042_evidence_rt as
    select usubjid, 'PALLIATIVE_RT' as evidence_type length=40,
           event_date as evidence_date format=yymmdd10.,
           event_date as latest_possible_date format=yymmdd10.,
           source_keys as evidence_key length=80
    from work.f042_rt_events
    where rt_autoqualifies = 1 and not missing(event_date);

    create table work.f042_evidence as
    select * from work.f042_evidence_adrs
    union all select * from work.f042_evidence_ds
    union all select * from work.f042_evidence_rt;

    create table work.f042_diary_qualified as
    select d.*,
           case when exists
             (select 1 from work.f042_evidence as e
              where e.usubjid = d.usubjid
                and not missing(d.confirming_date)
                and not missing(e.latest_possible_date)
                and e.latest_possible_date <= d.confirming_date)
           then 1 else 0 end as support_qualified
    from work.f042_diary_events as d;

    create table work.f042_primary_candidates as
    select usubjid, event_date, 'DIARY' as event_source length=8,
           component as event_component length=8
    from work.f042_diary_qualified
    where support_qualified = 1
    union all
    select usubjid, event_date, 'RT' as event_source length=8,
           'RT' as event_component length=8
    from work.f042_rt_events
    where rt_autoqualifies = 1 and not missing(event_date);

    create table work.f042_primary_event_dates as
    select usubjid, min(event_date) as event_date format=yymmdd10.
    from work.f042_primary_candidates
    group by usubjid;

    create table work.f042_pain_pfs_prog_dates as
    select usubjid, event_date as pain_prog_dt format=yymmdd10.
    from work.f042_primary_event_dates;
quit;

/* Last evaluable scheduled pain assessment is the controlled censor source. */
proc sql;
    create table work.f042_pain_lastassess as
    select v.usubjid, max(v.visit_date) as last_eval_dt format=yymmdd10.
    from work.f042_visit_triggers as v
    inner join adam.adsl as a on v.usubjid = a.usubjid
    where not missing(v.visit_date)
      and v.visit_date > a.randdt
      and v.visit_date <= &STUDY_CUTOFF_DT.
      and (v.ppi_evaluable = 1 or v.as_evaluable = 1)
    group by v.usubjid;

    create table work.pain_pfs_prog_dates as
    select usubjid, pain_prog_dt from work.f042_pain_pfs_prog_dates;
    create table work.pfs_pain_eval_dates as
    select usubjid, last_eval_dt as last_pain_eval_dt
    from work.f042_pain_lastassess;
    create table work.prog_dates as
    select usubjid, pain_prog_dt as prog_date
    from work.f042_pain_pfs_prog_dates;
    create table work.censor_dates as
    select usubjid, last_eval_dt as last_pn_dt
    from work.f042_pain_lastassess;
quit;
