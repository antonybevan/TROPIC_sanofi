*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: A_adex_generation.sas
   Version: 2.0
   Author: Principal Clinical Data Infrastructure Architect
   Date: 2026-05-23
   Standard: ADaMIG v1.3 BDS
   Input: sdtm.ex, adam.adsl
   Output: adam.adex
   Description: Characterizes cycle-level and cumulative drug exposure, BSA resets,
                dose adjustments, delays, and relative dose intensity (RDI).
   ============================================================================= */

%include "00_config.sas";

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

/* Build BDS structure (Summary records) */
data work.adex_bds;
    set adam.adsl(keep=studyid usubjid subjid siteid trt01p trt01pn saffl trtsdt trtedt trtdurd);
    where saffl = 'Y';
    
    length PARAMCD $8 PARAM $40 AVALC $40 PARCAT1 $20 AVALCAT1 $20 AVISIT $40;
    format AVAL 8.2;
    
    /* Merge summaries */
    merge work.subj_mods;
    by usubjid;
    
    if missing(ncycle) then ncycle = 0;
    if missing(cumdose) then cumdose = 0;
    if missing(ndeldose) then ndeldose = 0;
    if missing(nreddose) then nreddose = 0;
    if missing(rdi) then rdi = 0;
    
    planned_dose = 12.0; /* planned dose for Mitoxantrone (mg/m2) */
    
    /* 1. Planned Dose Parameter */
    PARAMCD = 'PLDOSE';
    PARAM = 'Planned Dose (mg/m2)';
    PARCAT1 = 'INDIVIDUAL';
    AVAL = planned_dose;
    AVALC = put(AVAL, 8.2);
    AVISIT = 'ALL CYCLES';
    output;
    
    /* 2. Cumulative Dose Parameter */
    PARAMCD = 'CUMDOSE';
    PARAM = 'Cumulative Actual Dose (mg/m2)';
    PARCAT1 = 'SUMMARY';
    AVAL = cumdose;
    AVALC = put(AVAL, 8.2);
    AVISIT = 'ALL CYCLES';
    output;
    
    /* 3. Number of Cycles Parameter */
    PARAMCD = 'NCYCLE';
    PARAM = 'Number of Cycles Received';
    PARCAT1 = 'SUMMARY';
    AVAL = ncycle;
    AVALC = put(AVAL, 8.);
    AVISIT = 'ALL CYCLES';
    output;
    
    /* 4. Number of Dose Delays Parameter */
    PARAMCD = 'NDELDOSE';
    PARAM = 'Number of Dose Delays';
    PARCAT1 = 'SUMMARY';
    AVAL = ndeldose;
    AVALC = put(AVAL, 8.);
    AVISIT = 'ALL CYCLES';
    output;
    
    /* 5. Number of Dose Reductions Parameter */
    PARAMCD = 'NREDDOSE';
    PARAM = 'Number of Dose Reductions';
    PARCAT1 = 'SUMMARY';
    AVAL = nreddose;
    AVALC = put(AVAL, 8.);
    AVISIT = 'ALL CYCLES';
    output;
    
    /* 6. Relative Dose Intensity Parameter */
    PARAMCD = 'RDI';
    PARAM = 'Relative Dose Intensity (%)';
    PARCAT1 = 'SUMMARY';
    AVAL = rdi;
    AVALC = put(AVAL, 8.1);
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
    AVALCAT1 = AVALC;
    AVISIT = 'ALL CYCLES';
    output;
run;

/* Add cycle level performance dose and adjustments */
data work.adex_cycle;
    set sdtm.ex(keep=usubjid exdose2 exseq exdsrcm exdelay);
    
    length PARAMCD $8 PARAM $40 AVALC $40 PARCAT1 $20 AVALCAT1 $20 AVISIT $40;
    format AVAL 8.2;
    
    /* Bring in ADSL demographics */
    merge adam.adsl(keep=studyid usubjid subjid siteid trt01p trt01pn saffl trtsdt trtedt trtdurd);
    by usubjid;
    where saffl = 'Y';
    
    AVISIT = catx(' ', 'CYCLE', put(exseq, 2.));
    
    /* 8. Actual Performance Dose Parameter */
    PARAMCD = 'PERFDOSE';
    PARAM = 'Actual Dose Administered (mg/m2)';
    PARCAT1 = 'INDIVIDUAL';
    AVAL = exdose2;
    AVALC = put(AVAL, 8.2);
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
data adam.adex;
    set work.adex_bds work.adex_cycle;
run;

proc sort data=adam.adex;
    by usubjid PARAMCD AVISIT;
run;

/* Clean up work library */
proc datasets lib=work nolist kill;
run;
quit;
