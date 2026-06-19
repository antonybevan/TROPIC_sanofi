*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adex_generation.sas
   Version: 2.2.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-05-27
   Standard: ADaMIG v1.3 BDS
   Input: sdtm.ex, adam.adsl
   Output: adam.adex
   Description: Characterizes cycle-level and cumulative drug exposure, BSA resets,
                dose adjustments, delays, and relative dose intensity (RDI).
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

/* Summarize modifications per subject from real SDTM EX */
proc sql;
    create table work.subj_mods as
    select 
        usubjid,
        max(exseq) as ncycle,
        max(excumd2) as cumdose,
        sum(case when not missing(exdelay) and exdelay ne '' then 1 else 0 end) as ndeldose,
        sum(case when not missing(exdsrcm) and exdsrcm ne '' then 1 else 0 end) as nreddose,
        max(extrint) as rdi
    from sdtm.ex
    group by usubjid;
quit;

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
    if missing(cumdose) then cumdose = 0;
    if missing(ndeldose) then ndeldose = 0;
    if missing(nreddose) then nreddose = 0;
    if missing(rdi) then rdi = 0;
    
    planned_dose = &PLANNED_DOSE.; /* Mitoxantrone planned dose mg/m2 — see config */
    
    /* 1. Planned Dose Parameter */
    PARAMCD = 'PLDOSE';
    PARAM = 'Planned Dose (mg/m2)';
    PARCAT1 = 'INDIVIDUAL';
    AVAL = planned_dose;
    AVALC = strip(put(AVAL, 8.2));
    AVISIT = 'ALL CYCLES';
    output;
    
    /* 2. Cumulative Dose Parameter */
    PARAMCD = 'CUMDOSE';
    PARAM = 'Cumulative Actual Dose (mg/m2)';
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
    PARAM = 'Relative Dose Intensity (%)';
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
    if rdi >= 85 then AVALC = '>=85%';
    else if rdi >= 65 then AVALC = '65-<85%';
    else AVALC = '<65%';
    AVISIT = 'ALL CYCLES';
    output;
run;

/* Sort cycle-level EX data by usubjid */
proc sort data=sdtm.ex(keep=usubjid exdose2 exseq exdsrcm exdelay) out=work.ex_sorted;
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
    
    AVISIT = catx(' ', 'CYCLE', put(exseq, 2.));
    
    /* 8. Actual Performance Dose Parameter */
    PARAMCD = 'PERFDOSE';
    PARAM = 'Actual Dose Administered (mg/m2)';
    PARCAT1 = 'INDIVIDUAL';
    AVAL = exdose2;
    AVALC = strip(put(AVAL, 8.2));
    output;
    
    /* 9. Dose Adjusted Flag */
    PARAMCD = 'ADJ';
    PARAM = 'Dose Adjusted Flag';
    PARCAT1 = 'INDIVIDUAL';
    if not missing(exdsrcm) and exdsrcm ne '' then do;
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
    if exdsrcm = 'ADVERSE EVENT' then do;
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
data adam.adex(keep=STUDYID USUBJID SUBJID TRT01P TRT01PN TRTSDT PARAMCD PARAM PARCAT1 AVAL AVALC AVISIT);
    set work.adex_bds work.adex_cycle;
run;

proc sort data=adam.adex;
    by usubjid PARAMCD AVISIT;
run;

/* Clean up work library */
proc delete data=work.subj_mods work.adsl_sorted work.adex_bds_merged work.adex_bds
            work.ex_sorted work.adex_cycle_merged work.adex_cycle;
run;
quit;
