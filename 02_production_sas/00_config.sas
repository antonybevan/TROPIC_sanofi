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
    %if %symexist(PROJ_ROOT) = 0 or &PROJ_ROOT = %str() or &PROJ_ROOT = . %then %do;
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

    /* Define Libraries */
    libname raw "&PROJ_ROOT.&PATH_SEP.01_raw_source" access=readonly;
    libname real_sdtm "&PROJ_ROOT.&PATH_SEP.01_raw_source&PATH_SEP.real_sdtm" access=readonly;
    libname staging "&PROJ_ROOT.&PATH_SEP.04_adam" ;
    libname sdtm "&PROJ_ROOT.&PATH_SEP.04_adam" ;
    libname adam "&PROJ_ROOT.&PATH_SEP.04_adam" ;
    
    /* Global SAS Options */
    options ls=120 ps=60 validvarname=upcase missing='' mergenoby=WARN;
    
    %put NOTE: [CONFIG] Environment configured successfully on &SYSSCP..;
    %put NOTE: [CONFIG] Auto-resolved Project Root path: &PROJ_ROOT.;
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
