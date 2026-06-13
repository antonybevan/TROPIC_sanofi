*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: 00_master_driver.sas
   Version: 2.2.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-05-27
   Standard: CDISC ADaMIG v1.3 / OCCDS v1.1
   Description: Master execution driver for TROPIC (Study EFC6193 / XRP6258) pipeline.
   ============================================================================== */

/* PGMDIR is pre-set by the Python/SASPy caller; fall back to relative "." for
   standalone batch execution where the CWD is already 02_production_sas/.
   Wrapped in a macro for portability (open-code %IF requires 9.4M5+). */
%macro set_pgmdir;
    %if not %symexist(PGMDIR) %then %global PGMDIR;
    %if "&PGMDIR." = "" %then %let PGMDIR = .;
%mend set_pgmdir;
%set_pgmdir;

%include "&PGMDIR./00_config.sas";
%check_err(00_config);

/* Stage 1: Raw Ingest and Type Normalization */
%include "&PGMDIR./L_staging_ingest.sas";
%check_err(L_staging_ingest);

/* Stage 2: SDTM Mapping */
%include "&PGMDIR./S_sdtm_mapping.sas";
%check_err(S_sdtm_mapping);

/* Stage 3: ADSL Subject-Level ADaM */
%include "&PGMDIR./A_adsl_generation.sas";
%check_err(A_adsl_generation);

/* Stage 4: ADEX Exposure BDS ADaM */
%include "&PGMDIR./A_adex_generation.sas";
%check_err(A_adex_generation);

/* Stage 5: ADCM Concomitant Medications OCCDS ADaM */
%include "&PGMDIR./A_adcm_generation.sas";
%check_err(A_adcm_generation);

/* Stage 6: ADAE Adverse Events OCCDS ADaM */
%include "&PGMDIR./A_adae_io_respec.sas";
%check_err(A_adae_io_respec);

/* Stage 7: ADLB Laboratories BDS ADaM */
%include "&PGMDIR./A_adlb_generation.sas";
%check_err(A_adlb_generation);

/* Stage 8: ADRS Efficacy Response BDS ADaM */
%include "&PGMDIR./A_adrs_generation.sas";
%check_err(A_adrs_generation);

/* Stage 9: ADTTE Time-to-Event BDS ADaM */
%include "&PGMDIR./A_adtte_generation.sas";
%check_err(A_adtte_generation);

/* Stage 10: XPT Export with Constraints */
%include "&PGMDIR./U_xpt_export.sas";
%check_err(U_xpt_export);

/* Final status banner — must reflect drained-error runs (IOM syntaxcheck mode) */
%macro pipeline_done;
    %if &syscc. > 4 %then %do;
        %put ERROR: [PIPELINE] FINISHED WITH ERRORS. SYSCC=&syscc.. See log above for the failing program.;
    %end;
    %else %do;
        %put NOTE: [PIPELINE] COMPLETE. SDTM MAPPING, ADaM DERIVATION, AND XPT EXPORT COMPILED WITH ZERO ERRORS.;
    %end;
%mend pipeline_done;
%pipeline_done;
