*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: L_staging_ingest.sas
   Version: 2.2.0
   Author: Principal Clinical Data Infrastructure Architect
   Date: 2026-05-27
   Standard: ADaMIG v1.3
   Input: real_sdtm.*.sas7bdat
   Output: staging.*
   Description: Ingests real SDTM datasets and performs automated transpositions
                and merging of supplemental SDTM variables.
   ============================================================================== */

%include "00_config.sas";

%macro transpose_supp(domain);
    %put NOTE: [INGEST] Ingesting and transposing domain: &domain..;
    
    /* Check if supplemental table exists and is non-empty */
    %let supp_exists = 0;
    proc sql noprint;
        select count(*) into :supp_exists
        from dictionary.tables
        where libname="REAL_SDTM" and memname="SUPP&domain.";
    quit;
    
    %if &supp_exists. > 0 %then %do;
        /* Sort supplemental dataset */
        proc sort data=real_sdtm.supp&domain. out=_supp_sorted;
            by usubjid idvar idvarval;
        run;
        
        /* Pivot supplemental variables from long to wide */
        proc transpose data=_supp_sorted out=_supp_transposed(drop=_name_ _label_);
            by usubjid idvar idvarval;
            id qnam;
            var qval;
        run;
        
        %if %upcase(&domain.) = DM %then %do;
            /* For DM, merge solely by USUBJID */
            proc sort data=real_sdtm.dm out=_main_sorted;
                by usubjid;
            run;
            proc sort data=_supp_transposed out=_supp_sorted2;
                by usubjid;
            run;
            data staging.dm;
                merge _main_sorted(in=a) _supp_sorted2(drop=idvar idvarval);
                by usubjid;
                if a;
            run;
        %end;
        %else %do;
            /* For other domains, extract standard IDVAR name (e.g. AESEQ) */
            %let idvar_name = ;
            proc sql noprint;
                select distinct idvar into :idvar_name trimmed
                from real_sdtm.supp&domain.
                where not missing(idvar);
            quit;
            
            %if &idvar_name. ne %str() %then %do;
                /* Convert IDVARVAL to numeric matching standard ID variable name */
                data _supp_ready;
                    set _supp_transposed;
                    if not missing(idvarval) then do;
                        &idvar_name. = input(idvarval, best32.);
                    end;
                    drop idvar idvarval;
                run;
                
                proc sort data=real_sdtm.&domain. out=_main_sorted;
                    by usubjid &idvar_name.;
                run;
                proc sort data=_supp_ready out=_supp_sorted2;
                    by usubjid &idvar_name.;
                run;
                data staging.&domain.;
                    merge _main_sorted(in=a) _supp_sorted2;
                    by usubjid &idvar_name.;
                    if a;
                run;
            %end;
            %else %do;
                /* Fallback merge by USUBJID only */
                proc sort data=real_sdtm.&domain. out=_main_sorted;
                    by usubjid;
                run;
                proc sort data=_supp_transposed out=_supp_sorted2;
                    by usubjid;
                run;
                data staging.&domain.;
                    merge _main_sorted(in=a) _supp_sorted2(drop=idvar idvarval);
                    by usubjid;
                    if a;
                run;
            %end;
        %end;
    %end;
    %else %do;
        /* Supplemental table does not exist; copy primary domain directly */
        data staging.&domain.;
            set real_sdtm.&domain.;
        run;
    %end;
    
    %put NOTE: [INGEST] Successfully completed staging domain: &domain..;
%mend transpose_supp;

%transpose_supp(dm);
%transpose_supp(ae);
%transpose_supp(ex);
%transpose_supp(cm);
%transpose_supp(lb);
%transpose_supp(ds);
%transpose_supp(vs);
%transpose_supp(ls);
%transpose_supp(pn);

/* Clean up temporary utility datasets in work library */
proc datasets lib=work nolist kill;
run;
quit;
