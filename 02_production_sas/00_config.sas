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
    %global PROJ_ROOT PATH_SEP;
    
    /* Detect Host Platform */
    %if %sysevalf(%superq(SYSSCP) = WIN, boolean) or %sysevalf(%superq(SYSSCP) = WINDOWS, boolean) %then %do;
        %let PATH_SEP = \;
    %end;
    %else %do;
        %let PATH_SEP = /;
    %end;
    
    /* Automatically derive project root if not already defined */
    %if %symexist(PROJ_ROOT) = 0 or &PROJ_ROOT = %str() %then %do;
        /* Default to active workspace layout. For ODA, user will pull to remote. */
        %let PROJ_ROOT = .;
    %end;

    /* Define Libraries */
    libname raw "&PROJ_ROOT.&PATH_SEP.01_raw_source" access=readonly;
    libname real_sdtm "&PROJ_ROOT.&PATH_SEP.01_raw_source&PATH_SEP.real_sdtm" access=readonly;
    libname staging "&PROJ_ROOT.&PATH_SEP.04_adam" ;
    libname sdtm "&PROJ_ROOT.&PATH_SEP.04_adam" ;
    libname adam "&PROJ_ROOT.&PATH_SEP.04_adam" ;
    
    /* Global SAS Options */
    options ls=120 ps=60 validvarname=upcase missing='' mergenoby=WARN;
    
    %put NOTE: [CONFIG] Environment configured successfully on &SYSSCP..;
%mend load_config;

%load_config;

/* Core Macro: Check error status and exit if failure */
%macro check_err(progname);
    %if &syscc. > 4 %then %do;
        %put ERROR: [PIPELINE] Execution failed in program &progname. with SYSCC=&syscc..;
        %abort cancel;
    %end;
    %else %do;
        %put NOTE: [PIPELINE] Program &progname. executed successfully with SYSCC=&syscc..;
    %end;
%mend check_err;
