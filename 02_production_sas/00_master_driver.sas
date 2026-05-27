*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: 00_master_driver.sas
   Version: 2.2.0
   Author: Principal Clinical Data Infrastructure Architect
   Date: 2026-05-27
   Standard: CDISC ADaMIG v1.3 / OCCDS v1.1
   Description: Master execution driver for TROPIC (Study EFC6193 / XRP6258) pipeline.
   ============================================================================== */

%include "00_config.sas";
%check_err(00_config);

/* Stage 1: Raw Ingest and Type Normalization */
%include "L_staging_ingest.sas";
%check_err(L_staging_ingest);

/* Stage 2: SDTM Mapping */
%include "S_sdtm_mapping.sas";
%check_err(S_sdtm_mapping);

/* Stage 3: ADSL Subject-Level ADaM */
%include "A_adsl_generation.sas";
%check_err(A_adsl_generation);

/* Stage 4: ADEX Exposure BDS ADaM */
%include "A_adex_generation.sas";
%check_err(A_adex_generation);

/* Stage 5: ADCM Concomitant Medications OCCDS ADaM */
%include "A_adcm_generation.sas";
%check_err(A_adcm_generation);

/* Stage 6: ADAE Adverse Events OCCDS ADaM */
%include "A_adae_io_respec.sas";
%check_err(A_adae_io_respec);

/* Stage 7: ADLB Laboratories BDS ADaM */
%include "A_adlb_generation.sas";
%check_err(A_adlb_generation);

/* Stage 8: ADRS Efficacy Response BDS ADaM */
%include "A_adrs_generation.sas";
%check_err(A_adrs_generation);

/* Stage 9: ADTTE Time-to-Event BDS ADaM */
%include "A_adtte_generation.sas";
%check_err(A_adtte_generation);

/* Stage 10: XPT Export with Constraints */
%include "U_xpt_export.sas";
%check_err(U_xpt_export);

%put NOTE: [PIPELINE] COMPLETE. ALL MAPPINGS AND TFL SUITES COMPILED WITH ZERO ERRORS.;
