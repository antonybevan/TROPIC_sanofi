*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: 00_config.sas
   Version: 3.5.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-06-12
   Standard: CDISC ADaMIG v1.3 / OCCDS v1.0
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
       PROTOCOL CONSTANTS — governed study configuration for all programs
       Reference: TROPIC SAP v4.0 controlled draft (EFC6193 / XRP6258)
       ============================================================ */

    %include "&PGMDIR.&PATH_SEP.00_config_generated.sas";

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
