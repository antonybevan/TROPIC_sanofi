*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: 00_config.sas
   Version: 2.2.0
   Author: Principal Clinical Data Infrastructure Architect
   Date: 2026-05-27
   Standard: CDISC ADaMIG v1.3 / OCCDS v1.1
   Description: Environment configuration, library allocations, and helper macros.
   ============================================================================== */

%macro load_config;
    %global PROJ_ROOT PGMDIR PATH_SEP;

    /* Detect Host Platform */
    %if %sysevalf(%superq(SYSSCP) = WIN, boolean) or %sysevalf(%superq(SYSSCP) = WINDOWS, boolean) %then %do;
        %let PATH_SEP = \;
    %end;
    %else %do;
        %let PATH_SEP = /;
    %end;

    /* Automatically derive project root if not already defined.
       Guard uses only %symexist (numeric result); path-containing macro variables
       cannot appear in OR conditions because %EVAL parses "/" as division. */
    %if %symexist(PROJ_ROOT) = 0 %then %do;
        %if %symexist(_SASPROGRAMFILE) %then %do;
            %if %superq(_SASPROGRAMFILE) ne %str() %then %do;
                %let prog_path = %sysfunc(dequote(&_SASPROGRAMFILE.));

                /* Detect starting index of the production folder to establish root */
                %let proj_idx = %sysfunc(find(%upcase(&prog_path.), %str(02_PRODUCTION_SAS)));

                %if &proj_idx. > 0 %then %do;
                    %let PROJ_ROOT = %substr(&prog_path., 1, %eval(&proj_idx. - 2));
                %end;
                %else %do;
                    /* Alternative: find last folder separator */
                    %let last_sep_idx = %sysfunc(find(&prog_path., &PATH_SEP., -999));
                    %if &last_sep_idx. > 0 %then %do;
                        %let PROJ_ROOT = %substr(&prog_path., 1, %eval(&last_sep_idx. - 1));
                    %end;
                    %else %do;
                        %let PROJ_ROOT = ..;
                    %end;
                %end;
            %end;
            %else %do;
                %let PROJ_ROOT = ..;
            %end;
        %end;
        %else %do;
            %let PROJ_ROOT = ..;
        %end;
    %end;

    /* PGMDIR: directory containing SAS programs — used for absolute %include in IOM mode.
       Pre-set by Python/SASPy before invoking master driver; here we set it as a
       fallback so standalone execution still resolves correctly via relative paths.
       Use only %symexist (numeric result) — path strings in OR conditions cause %EVAL errors. */
    %if %symexist(PGMDIR) = 0 %then %do;
        %global PGMDIR;
        %let PGMDIR = &PROJ_ROOT.&PATH_SEP.02_production_sas;
    %end;

    /* Define Libraries */
    options dlcreatedir;
    libname raw     "&PROJ_ROOT.&PATH_SEP.01_raw_source" access=readonly;
    libname realsdtm "&PROJ_ROOT.&PATH_SEP.01_raw_source&PATH_SEP.real_sdtm" access=readonly;
    libname staging "&PROJ_ROOT.&PATH_SEP.01_raw_source&PATH_SEP.real_sdtm";
    libname sdtm    "&PROJ_ROOT.&PATH_SEP.04_adam&PATH_SEP.sdtm_mapped";
    libname adam    "&PROJ_ROOT.&PATH_SEP.04_adam";
    
    /* Global SAS Options */
    options ls=120 ps=60 validvarname=upcase missing='' mergenoby=WARN;

    /* ============================================================
       PROTOCOL CONSTANTS — single source of truth for all programs
       Reference: TROPIC SAP v3.0 (EFC6193 / XRP6258)
       ============================================================ */

    /* Study identifiers */
    %global STUDYID TRT01P_CODE TRT01PN_CODE;
    %let STUDYID          = TROPIC-NCT00417079;
    %let TRT01P_CODE      = MP;           /* Mitoxantrone + Prednisone */
    %let TRT01PN_CODE     = 2;

    /* Study follow-up cutoff per DSMB decision (SAP §5.1) */
    %global STUDY_CUTOFF_DT;
    %let STUDY_CUTOFF_DT  = '25SEP2009'd;

    /* Drug exposure and stratification */
    %global PLANNED_DOSE AGE_STRAT_CUT;
    %let PLANNED_DOSE     = 12;           /* Mitoxantrone mg/m2 per cycle */
    %let AGE_STRAT_CUT    = 65;           /* Stratification age cutoff (years) */

    /* Missing data imputation defaults (SAP §6.3) */
    %global ECOGBL_DEFAULT PSABL_DEFAULT ALPBL_DEFAULT HGBBL_DEFAULT ALBBL_DEFAULT LDHBL_DEFAULT;
    %let ECOGBL_DEFAULT   = 1.0;          /* ECOG PS 1 = restricted light activity */
    %let PSABL_DEFAULT    = 110.0;        /* ng/mL */
    %let ALPBL_DEFAULT    = 140.0;        /* U/L   */
    %let HGBBL_DEFAULT    = 11.5;         /* g/dL  */
    %let ALBBL_DEFAULT    = 38.0;         /* g/dL — population reference mean      */
    %let LDHBL_DEFAULT    = 220.0;        /* U/L  — population reference mean      */

    /* RECIST v1.0 response thresholds (SAP §5.3) */
    %global RECIST_PD_PCT RECIST_PD_ABS RECIST_PR_PCT;
    %let RECIST_PD_PCT    = 20;           /* % increase from nadir = PD  */
    %let RECIST_PD_ABS    = 5;            /* mm absolute minimum = PD    */
    %let RECIST_PR_PCT    = -30;          /* % decrease from baseline = PR */

    /* PCWG3 PSA thresholds (SAP §5.4) */
    %global PSA_RESP_THRESHOLD PSA_RESP_CONFIRM PSA_PROG_MULT_RESP PSA_PROG_MULT_NORESP PSA_PROG_ABS PSA_PROG_CONFIRM;
    %let PSA_RESP_THRESHOLD   = 0.5;      /* >= 50% decline from baseline */
    %let PSA_RESP_CONFIRM     = 21;       /* days between confirming measurements */
    %let PSA_PROG_MULT_RESP   = 1.5;      /* PSA responder: >= 1.5x nadir */
    %let PSA_PROG_MULT_NORESP = 1.25;     /* Non-responder: >= 1.25x nadir */
    %let PSA_PROG_ABS         = 5;        /* Absolute increment >= 5 ng/mL */
    %let PSA_PROG_CONFIRM     = 7;        /* Confirmation within 7 days */

    /* OCCDS v1.1 continuous episode merging (SAP §5.2, Custom Query 02) */
    %global EPISODE_GAP_DAYS;
    %let EPISODE_GAP_DAYS     = 3;        /* <= 3-day gap = same episode */

    /* Project Optimus ANC kinetics (SAP §5.5) */
    %global ANC_RECOVERY_THRESHOLD;
    %let ANC_RECOVERY_THRESHOLD = 1.5;   /* x10^3/uL recovery target */

    /* LB analysis windows — study days from TRTSDT (SAP §5.6) */
    %global W_BL_HI W_C1D1_LO W_C1D1_HI W_C1D8_LO W_C1D8_HI;
    %global W_C1D15_LO W_C1D15_HI W_C2D1_LO W_C2D1_HI W_C2D8_LO W_C2D8_HI W_C3D1_LO W_C3D1_HI;
    %let W_BL_HI      = 0;
    %let W_C1D1_LO    = 1;   %let W_C1D1_HI    = 3;
    %let W_C1D8_LO    = 4;   %let W_C1D8_HI    = 13;
    %let W_C1D15_LO   = 14;  %let W_C1D15_HI   = 17;
    %let W_C2D1_LO    = 18;  %let W_C2D1_HI    = 24;
    %let W_C2D8_LO    = 25;  %let W_C2D8_HI    = 34;
    %let W_C3D1_LO    = 39;  %let W_C3D1_HI    = 45;

    %put NOTE: [CONFIG] Environment configured successfully on &SYSSCP..;
    %put NOTE: [CONFIG] Auto-resolved Project Root path: &PROJ_ROOT.;
%mend load_config;

%load_config;

/* Core Macro: Check error status and exit if failure.
   Batch mode (-sysin): hard stop via %abort cancel.
   IOM/SASPy mode: %abort cancel would cancel the remainder of the submitted
   block INCLUDING the SASPy end-of-submit marker, hanging the client forever.
   Instead, drain remaining steps in syntax-check mode (obs=0 noreplace) so the
   full log returns to the client with the ERROR lines intact.
   Note: getoption(SYSIN) returns a path; wrap in %length (numeric) because
   bare paths in %IF conditions trip %EVAL's "/" division parsing. */
%macro check_err(progname);
    %if &syscc. > 4 %then %do;
        %put ERROR: [PIPELINE] Execution failed in program &progname. with SYSCC=&syscc..;
        %if %length(%sysfunc(getoption(SYSIN))) > 0 %then %do;
            %abort cancel;
        %end;
        %else %do;
            options obs=0 syntaxcheck noreplace;
        %end;
    %end;
    %else %do;
        %put NOTE: [PIPELINE] Program &progname. executed successfully with SYSCC=&syscc..;
    %end;
%mend check_err;
