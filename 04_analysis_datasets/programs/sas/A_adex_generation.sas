*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adex_generation.sas
   Version: 3.0.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-08-09
   Standard: ADaMIG v1.3 BDS
   Input: sdtm.ex, adam.adsl
   Output: adam.adex
   Description: Characterizes primary IV antineoplastic exposure, dose
                adjustments, delays, and source-derived relative dose intensity.

   ADaM dens: one subject-level BDS spine per ADSL SAFFL='Y'. Oral prednisone/
   prednisolone records are excluded from antineoplastic cycle metrics.
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

/* Restrict exposure metrics to the randomized IV antineoplastic. EXSEQ counts
   oral and IV records, so VISITNUM is the governed treatment-cycle index. */
data work.iv_ex;
    set sdtm.ex;
    where index(upcase(strip(extrt)), 'MITOX') > 0
       or index(upcase(strip(extrt)), 'XRP') > 0
       or index(upcase(strip(extrt)), 'CABAZ') > 0;
    delay_flag = (not missing(exdelay));
    reduction_flag = (not missing(exdose2) and exdose2 > 0 and not missing(expdose) and
                      exdose2 < expdose * (1 - &DOSE_REDUCTION_TOLERANCE.));
run;

/* EXTRINT is a source-derived subject-level RDI repeated on each cycle. It may
   be carried only when the repeated values are internally unique. */
proc sql;
    create table work.subj_mods as
    select 
        usubjid,
        count(distinct case when exdose2 > 0 then visitnum else . end) as ncycle,
        max(case when visitnum = 1 then expdose else . end) as planned_dose,
        max(excumd2) as cumdose,
        sum(delay_flag) as ndeldose,
        sum(reduction_flag) as nreddose,
        case when count(distinct extrint) <= 1 then max(extrint) else . end as rdi,
        count(distinct extrint) as n_rdi_values
    from work.iv_ex
    group by usubjid;
quit;

data _null_;
    set work.subj_mods;
    if n_rdi_values > 1 then
        putlog "ERROR: [ADEX-QC] Conflicting source EXTRINT values for " usubjid= n_rdi_values=;
run;

/* Sort ADSL safety population by usubjid */
proc sort data=adam.adsl(keep=studyid usubjid subjid siteid trt01p trt01pn saffl trtsdt trtedt trtdurd
                         where=(saffl = 'Y')) out=work.adsl_sorted;
    by usubjid;
run;

/* Sort subj_mods by usubjid */
proc sort data=work.subj_mods;
    by usubjid;
run;

/* Match-merge ADSL and summaries */
data work.adex_bds_merged;
    merge work.adsl_sorted(in=a) work.subj_mods(in=b);
    by usubjid;
    if a;
run;

/* Build BDS structure (Summary records) */
data work.adex_bds;
    set work.adex_bds_merged;
    
    length PARAMCD $8 PARAM $40 AVALC $40 PARCAT1 $20 AVISIT $40;
    format AVAL 8.2;
    
    if missing(ncycle) then ncycle = 0;
    if missing(ndeldose) then ndeldose = 0;
    if missing(nreddose) then nreddose = 0;
    
    /* 1. Planned Dose Parameter */
    PARAMCD = 'PLDOSE';
    PARAM = 'Initial Planned IV Dose (mg/m2)';
    PARCAT1 = 'INDIVIDUAL';
    AVAL = planned_dose;
    AVALC = strip(put(AVAL, 8.2));
    AVISIT = 'ALL CYCLES';
    output;
    
    /* 2. Cumulative Dose Parameter */
    PARAMCD = 'CUMDOSE';
    PARAM = 'Cumulative IV Actual Dose (mg/m2)';
    PARCAT1 = 'SUMMARY';
    AVAL = cumdose;
    AVALC = strip(put(AVAL, 8.2));
    AVISIT = 'ALL CYCLES';
    output;
    
    /* 3. Number of Cycles Parameter */
    PARAMCD = 'NCYCLE';
    PARAM = 'Number of Cycles Received';
    PARCAT1 = 'SUMMARY';
    AVAL = ncycle;
    AVALC = strip(put(AVAL, 8.));
    AVISIT = 'ALL CYCLES';
    output;
    
    /* 4. Number of Dose Delays Parameter */
    PARAMCD = 'NDELDOSE';
    PARAM = 'Number of Dose Delays';
    PARCAT1 = 'SUMMARY';
    AVAL = ndeldose;
    AVALC = strip(put(AVAL, 8.));
    AVISIT = 'ALL CYCLES';
    output;
    
    /* 5. Number of Dose Reductions Parameter */
    PARAMCD = 'NREDDOSE';
    PARAM = 'Number of Dose Reductions';
    PARCAT1 = 'SUMMARY';
    AVAL = nreddose;
    AVALC = strip(put(AVAL, 8.));
    AVISIT = 'ALL CYCLES';
    output;
    
    /* 6. Relative Dose Intensity Parameter */
    PARAMCD = 'RDI';
    PARAM = 'Source RDI (%)';
    PARCAT1 = 'SUMMARY';
    AVAL = rdi;
    AVALC = strip(put(AVAL, 8.1));
    AVISIT = 'ALL CYCLES';
    output;
    
    /* 7. Relative Dose Intensity Category */
    PARAMCD = 'RDIDL';
    PARAM = 'Relative Dose Intensity Category';
    PARCAT1 = 'SUMMARY';
    AVAL = rdi;
    if missing(rdi) then AVALC = '';
    else if rdi >= 85 then AVALC = '>=85%';
    else if rdi >= 65 then AVALC = '65-<85%';
    else AVALC = '<65%';
    AVISIT = 'ALL CYCLES';
    output;
run;

/* Sort cycle-level EX data by usubjid */
proc sort data=work.iv_ex(keep=usubjid exdose2 expdose visitnum exdsrea exdelay
                              delay_flag reduction_flag) out=work.ex_sorted;
    by usubjid;
run;

/* Match-merge cycle EX with sorted ADSL */
data work.adex_cycle_merged;
    merge work.ex_sorted(in=a) work.adsl_sorted(in=b);
    by usubjid;
    if a and b;
run;

/* Add cycle level performance dose and adjustments */
data work.adex_cycle;
    set work.adex_cycle_merged;
    
    length PARAMCD $8 PARAM $40 AVALC $40 PARCAT1 $20 AVISIT $40;
    format AVAL 8.2;
    
    AVISIT = catx(' ', 'CYCLE', put(visitnum, best.));
    
    /* 8. Actual Performance Dose Parameter */
    PARAMCD = 'PERFDOSE';
    PARAM = 'IV Actual Dose Administered (mg/m2)';
    PARCAT1 = 'INDIVIDUAL';
    AVAL = exdose2;
    AVALC = strip(put(AVAL, 8.2));
    output;
    
    /* 9. Dose Adjusted Flag */
    PARAMCD = 'ADJ';
    PARAM = 'Dose Adjusted Flag';
    PARCAT1 = 'INDIVIDUAL';
    if delay_flag = 1 or reduction_flag = 1 or not missing(exdsrea) then do;
        AVALC = 'Y';
        AVAL = 1.0;
    end;
    else do;
        AVALC = 'N';
        AVAL = 0.0;
    end;
    output;
    
    /* 10. Dose Adjusted due to AE Flag */
    PARAMCD = 'ADJAE';
    PARAM = 'Dose Adjusted due to AE Flag';
    PARCAT1 = 'INDIVIDUAL';
    if upcase(strip(exdsrea)) = 'ADVERSE EVENT' then do;
        AVALC = 'Y';
        AVAL = 1.0;
    end;
    else do;
        AVALC = 'N';
        AVAL = 0.0;
    end;
    output;
run;

/* Combine all exposure parameters */
data work.adex_all(keep=STUDYID USUBJID SUBJID TRT01P TRT01PN TRTSDT PARAMCD PARAM PARCAT1 AVAL AVALC AVISIT AVISITN);
    set work.adex_bds work.adex_cycle;
    /* AVISITN companion to AVISIT (audit F-09): ALL CYCLES -> 0; CYCLE n -> n */
    if AVISIT = 'ALL CYCLES' then AVISITN = 0;
    else AVISITN = input(scan(AVISIT, 2, ' '), ?? best12.);
run;

/* Deterministic 1:1 PARAMN over the sorted distinct PARAMCD set (audit F-09), identical to the
   R track's distinct(PARAMCD) |> arrange(PARAMCD) |> row_number(). */
proc sort data=work.adex_all out=work._pc(keep=PARAMCD) nodupkey;
    by PARAMCD;
run;
data work._pnmap;
    set work._pc;
    PARAMN = _n_;
run;

proc sql;
    create table adam.adex as
    select a.STUDYID, a.USUBJID, a.SUBJID, a.TRT01P, a.TRT01PN, a.TRTSDT, a.PARAMCD, a.PARAM,
           a.PARCAT1, a.AVAL, a.AVALC, a.AVISIT, m.PARAMN, a.AVISITN
    from work.adex_all as a
    left join work._pnmap as m on a.PARAMCD = m.PARAMCD;
quit;

proc sort data=adam.adex;
    by usubjid PARAMCD AVISIT;
run;

/* Clean up work library */
proc delete data=work.iv_ex work.subj_mods work.adsl_sorted work.adex_bds_merged work.adex_bds
            work.ex_sorted work.adex_cycle_merged work.adex_cycle
            work.adex_all work._pc work._pnmap;
run;
quit;
