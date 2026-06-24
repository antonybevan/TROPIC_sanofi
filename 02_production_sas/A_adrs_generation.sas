*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adrs_generation.sas
   Version: 2.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-05-23
   Standard: CDISC ADaMIG v1.3 BDS
   Input: staging.ls, sdtm.rs, sdtm.lb, adam.adsl
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
    
    /* Target-lesion response only; integrated with non-target + new lesions below. */
    length target_resp $20;
    if post_sod = 0 then target_resp = 'CR';
    else if pct_chg_nadir >= &RECIST_PD_PCT. and abs_chg_nadir >= &RECIST_PD_ABS. then target_resp = 'PD';
    else if pct_chg_base <= &RECIST_PR_PCT. then target_resp = 'PR';
    else target_resp = 'SD';
run;

/* 1a. Non-target lesion response per visit (RECIST integration component).
   Worst-per-visit collapse of LSCAT='NON-TARGET' / LSTESTCD='STATUS' results.
   Ranking: PD > Non-CR/Non-PD (SD) > CR > NE. Absent for a subject/visit => the
   integration below falls back to target-only (no downgrade). */
proc sql;
    create table work.nontarget_resp as
    select usubjid, visit,
           max(case when lsstresc = 'PROGRESSIVE DISEASE'                then 4
                    when lsstresc = 'INCOMPLETE RESPONSE/STABLE DISEASE' then 3
                    when lsstresc = 'COMPLETE RESPONSE'                  then 2
                    else 1 end) as nt_rank
    from staging.ls
    where lscat = 'NON-TARGET' and lstestcd = 'STATUS' and visit ne 'BASELINE'
      and not missing(lsstresc) and lsstresc ne 'MISSING DATA'
    group by usubjid, visit;
quit;

data work.nontarget_resp;
    set work.nontarget_resp;
    length nt_resp $20;
    select (nt_rank);
        when (4) nt_resp = 'PD';
        when (3) nt_resp = 'SD';   /* Non-CR/Non-PD */
        when (2) nt_resp = 'CR';
        otherwise nt_resp = 'NE';
    end;
    keep usubjid visit nt_resp;
run;

/* 1b. New-lesion flag per visit (RECIST: any new lesion => PD). */
proc sql;
    create table work.newles_flag as
    select distinct usubjid, visit, 'Y' as newles_fl length=1
    from staging.ls
    where lstestcd = 'NEWLES' and lsstresc = 'NEW LESION' and visit ne 'BASELINE';
quit;

/* 1c. Integrated RECIST v1.0 overall response (target + non-target + new lesion).
   Overrides: new lesion => PD; any PD (target or non-target) => PD; target CR with a
   non-CR non-target => PR. Otherwise the target response carries (defensive: missing
   non-target / new-lesion rows reproduce the prior target-only result). */
proc sql;
    create table work.recist_join as
    select r.*, n.nt_resp, x.newles_fl
    from work.recist_calc as r
    left join work.nontarget_resp as n on r.usubjid = n.usubjid and r.visit = n.visit
    left join work.newles_flag   as x on r.usubjid = x.usubjid and r.visit = x.visit;
quit;

data work.recist_integrated;
    set work.recist_join;
    length recist_resp $20;
    if newles_fl = 'Y' then recist_resp = 'PD';
    else if target_resp = 'PD' or nt_resp = 'PD' then recist_resp = 'PD';
    else if target_resp = 'CR' and nt_resp not in ('', 'CR') then recist_resp = 'PR';
    else recist_resp = target_resp;
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
    from work.recist_integrated as r
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

/* Objective Response (OBJRESP) -- RECIST v1.0 CONFIRMED response (audit M-2).
   A responder requires a confirmatory CR/PR at least &RECIST_CONFIRM_DAYS days
   after the first CR/PR (CR confirmed by CR; PR confirmed by CR or PR). Confirmation
   is evaluated on the lesion-derived RECIST timepoints (work.recist_ovrl) so the SAS
   and R tracks use an identical, reconcilable basis. Unconfirmed single responses are
   NOT counted -- this aligns the real-MP ORR with the published confirmed rate, which
   the prior best-response logic overstated ~4x. */
proc sql;
    create table work.orr_confirmed as
    select distinct a.usubjid
    from work.recist_ovrl as a
    inner join work.recist_ovrl as b
        on a.usubjid = b.usubjid
       and b.ADT - a.ADT >= &RECIST_CONFIRM_DAYS.
    where a.AVALC in ('CR', 'PR') and b.AVALC in ('CR', 'PR')
      and not (a.AVALC = 'CR' and b.AVALC = 'PR');
quit;

proc sql;
    create table work.orr_summary as
    select
        b.studyid, b.usubjid, b.trt01p, b.trtsdt,
        'OBJRESP' as PARAMCD length=8,
        'Objective Response (confirmed CR/PR)' as PARAM length=40,
        case when c.usubjid is not null then 'Y' else 'N' end as AVALC length=20,
        case when c.usubjid is not null then 1.0 else 0.0 end as AVAL,
        b.AVISIT length=40,
        b.AVISITN
    from work.bor_summary as b
    left join work.orr_confirmed as c on b.usubjid = c.usubjid;
quit;

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

/* PCWG3 Bone-Scan Progression (BSGRESP) -- 2+2 rule (Scher 2016). Methodological
   demonstration (post-2010, not in the trial-era SAP; see ADRG SS4A), mirroring how
   PSPROG already applies PCWG3 to this 2010 trial. Bone is the dominant mCRPC
   progression site and is largely non-measurable by RECIST, so it is tracked
   separately and feeds A_adtte_generation.sas (BSGRESP='PROGRESSION'). */
proc sql;
    /* New bone lesions per post-baseline scan date */
    create table work.bone_new as
    select usubjid,
           input(substr(lsdtc, 1, 10), yymmdd10.) as scan_dt format=yymmdd10.,
           count(*) as n_new_bone
    from staging.ls
    where lstestcd = 'NEWLES' and lsloc = 'BONE' and lsstresc = 'NEW LESION'
      and visit ne 'BASELINE' and not missing(lsdtc)
    group by usubjid, calculated scan_dt;
quit;

proc sql;
    /* PDu: first scan with >= MIN_NEW new bone lesions (unconfirmed progression). */
    create table work.bone_pdu as
    select usubjid, min(scan_dt) as pdu_date format=yymmdd10.
    from work.bone_new
    where n_new_bone >= &BONE_PROG_MIN_NEW.
    group by usubjid;
quit;

proc sql;
    /* Confirmed: a later scan adds >= CONFIRM_NEW further new bone lesions (2+2).
       PD date is backdated to the PDu scan. */
    create table work.bone_conf as
    select distinct p.usubjid
    from work.bone_pdu as p
    inner join work.bone_new as b
        on p.usubjid = b.usubjid and b.scan_dt > p.pdu_date
       and b.n_new_bone >= &BONE_PROG_CONFIRM_NEW.;
quit;

proc sql;
    /* Three-level PCWG3 result: confirmed PROGRESSION feeds TTUMOR (A_adtte);
       PROGRESSION UNCONFIRMED (PDu) is informational and does NOT count as an event. */
    create table work.bsgresp as
    select
        adsl.usubjid,
        'BSGRESP' as PARAMCD length=8,
        'Bone Scan Progression (PCWG3)' as PARAM length=40,
        case when c.usubjid is not null then 'PROGRESSION'
             when p.usubjid is not null then 'PROGRESSION UNCONFIRMED'
             else 'NO PROGRESSION' end as AVALC length=24,
        case when c.usubjid is not null then 1.0 else 0.0 end as AVAL,
        p.pdu_date as ADT format=yymmdd10.,
        'ALL CYCLES' as AVISIT length=40,
        99 as AVISITN
    from adam.adsl as adsl
    left join work.bone_pdu  as p on adsl.usubjid = p.usubjid
    left join work.bone_conf as c on adsl.usubjid = c.usubjid
    where adsl.saffl = 'Y';
quit;

/* Combine all parameters and sort before merge.
   AVALC must be declared $100 (= define.xml IT.ADRS.AVALC Length) BEFORE the SET:
   in a DATA-step concatenation the variable length is otherwise fixed by the first
   contributing dataset (work.rs_base -> $20), which silently truncates the longest
   BSGRESP term 'PROGRESSION UNCONFIRMED' (23 chars) to 'PROGRESSION UNCONFIR'. That
   truncation is what the SAS-vs-R cross-language audit caught (5 BSGRESP cells). */
data work.adrs_union;
    length AVALC $100;
    set work.rs_base work.bor_summary work.orr_summary work.psprog work.psaresp work.bsgresp;
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
proc delete data=work.base_sod work.post_sod work.cycle_sod_comp work.recist_calc
            work.nontarget_resp work.newles_flag work.recist_join work.recist_integrated
            work.recist_ovrl work.rs_disp work.rs_base work.bor_rank work.bor_summary
            work.orr_confirmed work.orr_summary work.psa_base work.psa_post work.psa_decline
            work.psa_resp_cand work.psa_responders work.psa_all work.psa_nadir
            work.psa_prog_check work.psa_prog_eval work.psa_prog_conf work.psprog
            work.psaresp work.bone_new work.bone_pdu work.bone_conf work.bsgresp
            work.adrs_union;
run;
quit;
