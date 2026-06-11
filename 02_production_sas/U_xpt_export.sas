*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: U_xpt_export.sas
   Version: 2.2.0
   Author: Principal Clinical Data Infrastructure Architect
   Date: 2026-05-27
   Standard: CDISC compliant transport v5 (XPT)
   Input: adam.*
   Output: 04_adam/*_prod.xpt
   Description: Programmatic export engine utilizing PROC COPY and libname xport
                to output compliant transport files under strict character constraints.
   ============================================================================= */

/* PGMDIR guard: allows standalone execution (CWD=02_production_sas) and IOM/ODA mode.
   Wrapped in a macro for portability (open-code %IF requires 9.4M5+). */
%macro set_pgmdir;
    %if not %symexist(PGMDIR) %then %global PGMDIR;
    %if "&PGMDIR." = "" %then %let PGMDIR = .;
%mend set_pgmdir;
%set_pgmdir;
%include "&PGMDIR./00_config.sas";

%macro export_xpt(dataset);
    /* Set up Transport Library path */
    libname _xout xport "&PROJ_ROOT.&PATH_SEP.04_adam&PATH_SEP.&dataset._prod.xpt";
    
    /* Programmatically copy with constraint check variables */
    proc copy in=adam out=_xout memtype=data;
        select &dataset.;
    run;
    
    libname _xout clear;
    %put NOTE: [EXPORT] Exported transport file: &dataset._prod.xpt;
%mend export_xpt;

%export_xpt(adsl);
%export_xpt(adex);
%export_xpt(adcm);
%export_xpt(adae);
%export_xpt(adlb);
%export_xpt(adrs);
%export_xpt(adtte);
