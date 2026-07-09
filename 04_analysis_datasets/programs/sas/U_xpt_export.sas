*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: U_xpt_export.sas
   Version: 2.2.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-05-27
   Standard: CDISC compliant transport v5 (XPT)
   Input: adam.*
   Output: 04_analysis_datasets/adam/*_prod.xpt
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
/* spec-sourced variable labels (GENERATED: platform/gen_adam_labels.R from
   03_metadata/adam/ADaM_spec.xlsx, the metadata control source -- audit C-4 inversion).
   Applies %lbl_<ds> so every ADaM variable carries its spec label (ADaMIG conformance). */
%include "&PGMDIR./_adam_labels.sas";

%macro assert_spec_vars(dataset);
    %local expected actual missing extra i v;
    %let expected = %upcase(%sysfunc(compbl(%vars_&dataset.)));
    proc sql noprint;
        select upcase(name)
          into :actual separated by ' '
          from dictionary.columns
         where libname = 'ADAM'
           and memname = "%upcase(&dataset.)"
         order by varnum;
    quit;
    %let actual = %upcase(%sysfunc(compbl(&actual.)));

    %let missing = ;
    %do i = 1 %to %sysfunc(countw(&expected.));
        %let v = %scan(&expected., &i.);
        %if not %sysfunc(indexw(&actual., &v.)) %then %let missing = &missing. &v.;
    %end;

    %let extra = ;
    %do i = 1 %to %sysfunc(countw(&actual.));
        %let v = %scan(&actual., &i.);
        %if not %sysfunc(indexw(&expected., &v.)) %then %let extra = &extra. &v.;
    %end;

    %if %length(%superq(missing)) or %length(%superq(extra)) %then %do;
        %put ERROR: [EXPORT] &dataset. variables do not match ADaM spec.;
        %put ERROR: [EXPORT] Missing from data: &missing.;
        %put ERROR: [EXPORT] Extra in data: &extra.;
        %abort cancel;
    %end;
%mend assert_spec_vars;

%macro export_xpt(dataset);
    /* DATA step write to XPORT: avoids SORTEDBY WARNING (not preserved by DATA step)
       and avoids PROC COPY NOREPLACE ERROR when the XPT already exists. */
    %assert_spec_vars(&dataset.);
    libname _xout xport "&PROJ_ROOT.&PATH_SEP.04_analysis_datasets/adam&PATH_SEP.&dataset._prod.xpt";
    data _xout.&dataset.;
        %ord_&dataset.;
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
