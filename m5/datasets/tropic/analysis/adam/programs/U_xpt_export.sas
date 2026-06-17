*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: U_xpt_export.sas
   Version: 2.2.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-05-27
   Standard: CDISC compliant transport v5 (XPT)
   Input: adam.*
   Output: 04_adam/*_prod.xpt
   Description: Programmatic export engine utilizing PROC COPY and libname xport
                to output compliant transport files under strict character constraints.
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
/* spec-sourced variable labels (GENERATED: 06_telemetry/gen_adam_labels.R from
   00_specifications/ADaM_spec.xlsx, the single source of truth -- audit C-4 inversion).
   Applies %lbl_<ds> so every ADaM variable carries its spec label (ADaMIG conformance). */
%include "&PGMDIR./_adam_labels.sas";

%macro export_xpt(dataset);
    /* DATA step write to XPORT: avoids SORTEDBY WARNING (not preserved by DATA step)
       and avoids PROC COPY NOREPLACE ERROR when the XPT already exists. */
    libname _xout xport "&PROJ_ROOT.&PATH_SEP.04_adam&PATH_SEP.&dataset._prod.xpt";
    data _xout.&dataset.;
        set adam.&dataset.;
        %lbl_&dataset.;
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
