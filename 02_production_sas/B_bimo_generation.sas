*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: B_bimo_generation.sas
   Version: 1.1.0
   Author: Antony Bevan, Clinical Programming
   Date: 2026-06-16
   Standard: FDA BIMO Technical Conformance Guide (Appendix 3 - clinsite), partial
   Input: adam.adsl, adam.adae
   Output: adam.clinsite -> 04_adam/clinsite_prod.xpt
   Description: Builds the summary-level clinical-site dataset (clinsite) used by FDA
                Bioresearch Monitoring (BIMO) to prioritise sites for inspection.

   SCOPE / HONEST LIMITATIONS (see 08_reviewers_guides/BDRG.md):
     - The full BIMO TCG Appendix-3 structure specifies ~39 site-level variables.
       This program implements the subset that is HONESTLY DERIVABLE from the public,
       de-identified TROPIC release (Project Data Sphere). It does NOT fabricate the
       variables that the de-identified source cannot support, namely:
         * INVESTIGATOR IDENTITY  - the release carries no PI name/address/contact;
                                     INVNAM below is a clearly-labelled SYNTHETIC
                                     placeholder, never a real investigator.
         * COUNTRY / site geography - not present in the de-identified release.
         * PROTOCOL DEVIATIONS      - no SDTM DV (deviations) domain is available.
         * SCREEN/COMPLETE/DISCONTINUE disposition counts - DS disposition reasons
                                     are not separable in the de-identified release.
     - Populations follow ICH E9: Randomized, Safety (treated), ITT, and Per-Protocol
       are DISTINCT analysis sets. ITT is NOT relabelled "Efficacy" (audit C-5 fix).
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

/* Site-level population counts from ADSL (one row per subject). */
proc sql;
    create table work.bimo_adsl as
    select studyid as STUDYID length=20,
           siteid  as SITEID  length=10,
           count(distinct usubjid)                          as N_RAND,
           sum(case when saffl   = 'Y' then 1 else 0 end)   as N_SAF,
           sum(case when ittfl   = 'Y' then 1 else 0 end)   as N_ITT,
           sum(case when pprotfl = 'Y' then 1 else 0 end)   as N_PPROT,
           sum(case when dthfl   = 'Y' then 1 else 0 end)   as N_DEATH
    from adam.adsl
    group by studyid, siteid;
quit;

/* Site-level safety counts from ADAE. ADAE carries no SITEID, so subjects are routed
   to their site via ADSL; COUNT(DISTINCT ... CASE) counts unique subjects per site. */
proc sql;
    create table work.bimo_ae as
    select a.siteid as SITEID length=10,
           count(distinct case when b.aeser   = 'Y' then b.usubjid end) as N_SAE,
           count(distinct case when b.trtemfl = 'Y' then b.usubjid end) as N_TEAE
    from adam.adsl a
    left join adam.adae b
        on a.usubjid = b.usubjid
    group by a.siteid;
quit;

/* Final CLINSITE: merge populations + safety; attach BIMO labels. */
proc sql;
    create table adam.clinsite as
    select a.STUDYID  label="Study Identifier",
           a.SITEID   label="Study Site Identifier",
           catx("_", "PI", a.SITEID) as INVNAM length=40
               label="Principal Investigator (SYNTHETIC placeholder - see BDRG)",
           a.N_RAND   label="Number of Subjects Randomized",
           a.N_SAF    label="Number of Subjects Treated (Safety Population)",
           a.N_ITT    label="Number of Subjects in ITT Population",
           a.N_PPROT  label="Number of Subjects in Per-Protocol Population",
           a.N_DEATH  label="Number of Subjects Who Died",
           coalesce(b.N_SAE, 0)  as N_SAE  label="Number of Subjects with a Serious AE",
           coalesce(b.N_TEAE, 0) as N_TEAE label="Number of Subjects with a TEAE"
    from work.bimo_adsl a
    left join work.bimo_ae b
        on a.SITEID = b.SITEID
    order by a.STUDYID, a.SITEID;
quit;

/* Export to transport file using the proven DATA-step XPORT idiom (matches
   U_xpt_export.sas): preserves labels and avoids PROC COPY NOREPLACE errors. */
libname _xout xport "&PROJ_ROOT.&PATH_SEP.04_adam&PATH_SEP.clinsite_prod.xpt";
data _xout.clinsite;
    set adam.clinsite;
run;
libname _xout clear;
%put NOTE: [BIMO] Exported transport file: clinsite_prod.xpt (one row per study site);
