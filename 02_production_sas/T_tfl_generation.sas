*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: T_tfl_generation.sas
   Version: 1.1.0
   Author:  Antony Bevan, Clinical Programming
   Standard: ICH E3 TFL Catalogue / NEJM & Lancet publication style
   Description: SAS production-track statistical figures, rendered natively via ODS
                Graphics. The R / pharmaverse track (09_tfl/tfl_generation.R) is the
                primary TFL deliverable; this program demonstrates that the production
                environment can produce the same regulatory-grade efficacy/safety
                figures, and serves as an independent visual check that the SAS analyses
                (Cox HR, KM survival, subjects-at-risk) agree with the R reporting track.
                Real MP arm comes from production ADaM (adam.*); the SYNTHETIC
                comparator (CbzP) is read from the bridged *_cbzp.xpt files.
   Output: &PROJ_ROOT/09_tfl/output/sas/F-*.png  (300 dpi PNG, Lancet style)
   ============================================================================= */

%macro set_pgmdir;
    %if not %symexist(PGMDIR) %then %global PGMDIR;
    %if "&PGMDIR." = "" %then %let PGMDIR = .;
%mend set_pgmdir;
%set_pgmdir;
%include "&PGMDIR./00_config.sas";

%let CBZDIR = &PROJ_ROOT.&PATH_SEP.01_raw_source&PATH_SEP.cbzp_reconstructed;
%let SASFIG = &PROJ_ROOT.&PATH_SEP.09_tfl&PATH_SEP.output&PATH_SEP.figures&PATH_SEP.sas;

/* Ensure the SAS figure output directory tree exists on the host (no XCMD needed) */
data _null_;
    if fileexist("&PROJ_ROOT.&PATH_SEP.09_tfl") = 0
        then rc1 = dcreate('09_tfl', "&PROJ_ROOT.");
    if fileexist("&PROJ_ROOT.&PATH_SEP.09_tfl&PATH_SEP.output") = 0
        then rc2 = dcreate('output', "&PROJ_ROOT.&PATH_SEP.09_tfl");
    if fileexist("&PROJ_ROOT.&PATH_SEP.09_tfl&PATH_SEP.output&PATH_SEP.figures") = 0
        then rc3 = dcreate('figures', "&PROJ_ROOT.&PATH_SEP.09_tfl&PATH_SEP.output");
    if fileexist("&SASFIG.") = 0
        then rc4 = dcreate('sas', "&PROJ_ROOT.&PATH_SEP.09_tfl&PATH_SEP.output&PATH_SEP.figures");
run;

/* Publication style: the SAS built-in JOURNAL3 (clean, journal-grade). Each plot
   additionally sets the exact Lancet blue (cx005A9C) / red (cxA6192E) via its own
   STYLEATTRS / attribute map, so a custom style template is unnecessary. */
ods listing gpath="&SASFIG." style=journal3 image_dpi=300;
ods graphics on / reset=all imagefmt=png width=8in height=5.5in noborder antialiasmax=100000;

%let LRED = cxA6192E;
%let SYNTHFN = %str(CbzP is a SYNTHETIC, illustrative comparator (PH-scaled from the real MP arm); between-arm statistics are circular by construction - NOT clinical findings.);

/* ---- Bridge the synthetic CbzP arm. The XPORT engine does NOT expand _ALL_ in
   a SET statement, so reference the explicit member name written by haven, which
   is upcase(domain)||"_C" truncated to 8 chars (e.g. adtte -> ADTTE_C). --------- */
%macro rdcbz(dom);
    %local mname;
    %let mname = %upcase(&dom.)_C;   /* haven member name, e.g. adtte -> ADTTE_C (all <=8 chars) */
    libname _cz xport "&CBZDIR.&PATH_SEP.&dom._cbzp.xpt";
    data cbz_&dom.; set _cz.&mname.; run;
    libname _cz clear;
%mend rdcbz;
%rdcbz(adtte);
%rdcbz(adsl);
%rdcbz(adlb);
%rdcbz(adex);

/* ============================================================================
   FIGURE F-11-1 / F-11-2 : Kaplan-Meier OS & PFS (with number-at-risk table)
   ============================================================================ */
%macro km(paramcd, fig, xmax, ylab, title);
    data _km;
        set adam.adtte(keep=usubjid trt01p paramcd aval cnsr)
            cbz_adtte(keep=usubjid trt01p paramcd aval cnsr);
        if paramcd = "&paramcd.";
        avalm = aval / 30.4375;
    run;

    %global _hr _lcl _ucl;
    %let _hr = .; %let _lcl = .; %let _ucl = .;
    proc phreg data=_km;
        class trt01p (ref='MP');
        model avalm*cnsr(1) = trt01p / ties=efron;
        hazardratio 'CbzP vs MP' trt01p / cl=wald;
        ods output HazardRatios=_hr_ds;
    run;
    data _null_;
        set _hr_ds;
        call symputx('_hr',  put(hazardratio, 4.2));
        call symputx('_lcl', put(WaldLower,   4.2));
        call symputx('_ucl', put(WaldUpper,   4.2));
    run;

    /* Survival estimates + censor points (SGPLOT gives full title/footnote control) */
    proc lifetest data=_km outsurv=_su noprint;
        time avalm*cnsr(1);
        strata trt01p;
    run;
    data _curve;
        set _su;
        sp = survival * 100;
        if _censor_ = 1 then cens = sp;
    run;
    data _anchor;
        length trt01p $8;
        do trt01p = 'CbzP', 'MP'; avalm = 0; sp = 100; output; end;
    run;
    /* Number at risk at each tick, by arm */
    data _tk; do _t = 0 to &xmax. by 3; output; end; run;
    proc sql;
        create table _ar as
        select t._t as avalm, k.trt01p, sum(k.avalm >= t._t) as nrisk
        from _tk t, _km k group by t._t, k.trt01p;
    quit;
    data _plot; set _anchor _curve _ar; run;

    ods graphics on / reset=index imagename="&fig._SAS";
    title  j=l h=12pt  c=cx111111 "&title. - SAS Production Track";
    title2 j=l h=9.5pt c=cx444444 "Cabazitaxel+Prednisone (CbzP, synthetic) vs Mitoxantrone+Prednisone (MP, real)   |   HR = &_hr. (95% CI &_lcl. - &_ucl.)";
    footnote j=l h=7.5pt c=&LRED. "&SYNTHFN.";
    proc sgplot data=_plot noautolegend nocycleattrs;
        styleattrs datacontrastcolors=(cx005A9C cxA6192E);
        step x=avalm y=sp / group=trt01p lineattrs=(thickness=2) name='km';
        scatter x=avalm y=cens / group=trt01p markerattrs=(symbol=plus size=7);
        xaxistable nrisk / x=avalm class=trt01p colorgroup=trt01p location=outside
            valueattrs=(size=8pt) classdisplay=cluster title="Number at risk:";
        keylegend 'km' / location=inside position=topright;
        xaxis label="Months from Randomization" values=(0 to &xmax. by 3) grid;
        yaxis label="&ylab." min=0 max=100 grid;
    run;
    title; title2; footnote;
%mend km;

%km(OS,  F-11-1_KM_OS,  24, Overall Survival Probability,          %str(F-11-1: Kaplan-Meier Overall Survival (OS)))
%km(PFS, F-11-2_KM_PFS, 18, Progression-Free Survival Probability, %str(F-11-2: Kaplan-Meier Progression-Free Survival (PFS)))

/* ============================================================================
   FIGURE F-12-1 : OS Subgroup Forest Plot (univariate Cox HRs, CbzP vs MP)
   ============================================================================ */
data _adsl_all;
    set adam.adsl(keep=usubjid agegr1 ecogbl measdisf viscfl painbl docprog)
        cbz_adsl(keep=usubjid agegr1 ecogbl measdisf viscfl painbl docprog);
run;
data _os;
    set adam.adtte(keep=usubjid trt01p paramcd aval cnsr)
        cbz_adtte(keep=usubjid trt01p paramcd aval cnsr);
    if paramcd='OS'; avalm = aval/30.4375;
run;
proc sql;
    create table _ossub as
    select a.*, b.agegr1, b.ecogbl, b.measdisf, b.viscfl, b.painbl, b.docprog
    from _os a left join _adsl_all b on a.usubjid=b.usubjid;
quit;

proc datasets lib=work nolist; delete forest; quit;
%macro sgcox(var, lvl, lbl, ord, num=0);
    proc phreg data=_ossub;
        %if &num. = 1 %then %do; where &var. = &lvl.; %end;
        %else %do; where &var. = "&lvl."; %end;
        class trt01p (ref='MP');
        model avalm*cnsr(1) = trt01p / ties=efron;
        hazardratio 'h' trt01p / cl=wald;
        ods output HazardRatios=_h;
    run;
    data _h2;
        set _h;
        length subgroup $34; subgroup = "&lbl."; ord = &ord.;
        keep subgroup ord hazardratio waldlower waldupper;
    run;
    proc append base=forest data=_h2 force; run;
%mend sgcox;

proc phreg data=_os;
    class trt01p(ref='MP'); model avalm*cnsr(1)=trt01p / ties=efron;
    hazardratio 'h' trt01p / cl=wald;
    ods output HazardRatios=_hov;
run;
data forest;
    set _hov; length subgroup $34; subgroup='All Patients'; ord=1;
    keep subgroup ord hazardratio waldlower waldupper;
run;

%sgcox(agegr1,  <65,  %str(Age < 65),                2)
%sgcox(agegr1,  >=65, %str(Age >= 65),               3)
%sgcox(ecogbl,  0,    %str(ECOG 0),                  4, num=1)
%sgcox(ecogbl,  1,    %str(ECOG 1),                  5, num=1)
%sgcox(measdisf, Y,   %str(Measurable Disease: Yes), 6)
%sgcox(measdisf, N,   %str(Measurable Disease: No),  7)
%sgcox(viscfl,  Y,    %str(Visceral Mets: Yes),      8)
%sgcox(viscfl,  N,    %str(Visceral Mets: No),       9)
%sgcox(painbl,  Y,    %str(Baseline Pain: Yes),      10)
%sgcox(painbl,  N,    %str(Baseline Pain: No),       11)
%sgcox(docprog, AFTER, %str(Docetaxel Prog: After),  12)
%sgcox(docprog, DURING,%str(Docetaxel Prog: During), 13)

proc sort data=forest; by descending ord; run;
data forest;
    set forest; length hrtext $24;
    hrtext = catx(' ', put(hazardratio,4.2), cats('(',put(waldlower,4.2),'-',put(waldupper,4.2),')'));
run;

/* Export the figure's own forest HRs for numerical SAS<->R reconciliation
   (05_reconciliation/forest_reconcile.R). Exporting the figure dataset (not an
   independent re-derivation) makes the gate validate the actual deliverable. */
proc export data=forest(keep=subgroup hazardratio waldlower waldupper)
    outfile="&PROJ_ROOT.&PATH_SEP.04_adam&PATH_SEP.forest_hr_prod.csv"
    dbms=csv replace;
run;

ods graphics on / reset=index imagename="F-12-1_Subgroup_Forest_SAS";
title  j=l h=12pt c=cx111111 "F-12-1: OS Prognostic Subgroup Forest Plot - SAS Production Track";
title2 j=l h=9pt  c=cx444444 "Univariate Cox hazard ratios (CbzP vs MP) with 95% Wald CIs";
footnote j=l h=7pt c=&LRED. "&SYNTHFN.";
proc sgplot data=forest noautolegend nocycleattrs;
    refline 1 / axis=x lineattrs=(pattern=shortdash color=gray55);
    highlow y=subgroup low=waldlower high=waldupper / type=line lineattrs=(color=cx1A5276 thickness=2);
    scatter y=subgroup x=hazardratio / markerattrs=(symbol=squarefilled size=10 color=cx1A5276);
    yaxistable hrtext / location=outside position=right valueattrs=(size=8pt) labelattrs=(size=8.5pt weight=bold) title="HR (95% CI)";
    xaxis type=log logbase=2 label="Hazard Ratio (Favors CbzP <-- | --> Favors MP)" values=(0.2 0.5 1 2 4) min=0.15 max=4.5;
    yaxis display=(noline noticks) label=' ';
run;
title; title2; footnote;

/* ============================================================================
   FIGURE F-13-1 : PSA Waterfall (best % change from baseline, by arm)
   ============================================================================ */
data _psa;
    set adam.adlb(keep=usubjid trt01p paramcd pchg)
        cbz_adlb(keep=usubjid trt01p paramcd pchg);
    if paramcd='PSA' and not missing(pchg);
run;
proc sql;
    create table _psab as
    select usubjid, trt01p, min(pchg) as best
    from _psa group by usubjid, trt01p;
quit;
proc sort data=_psab; by trt01p best; run;
data _psab;
    set _psab; by trt01p;
    if first.trt01p then rank=0;
    rank+1;
    length respcat $26;
    if best <= -50 then respcat='PSA Response (>=50% dec)';
    else if best < 0 then respcat='PSA Decrease (<50%)';
    else respcat='PSA Increase';
run;

/* Explicit category->color binding (alphabetical styleattrs would scramble it) */
data _psamap;
    length id $5 value $26 fillcolor $9 linecolor $9;
    id='psa';
    value='PSA Response (>=50% dec)'; fillcolor='cx005A9C'; linecolor='cx005A9C'; output;
    value='PSA Decrease (<50%)';      fillcolor='cx7FB3D3'; linecolor='cx7FB3D3'; output;
    value='PSA Increase';             fillcolor='cxA6192E'; linecolor='cxA6192E'; output;
run;

ods graphics on / reset=index imagename="F-13-1_PSA_Waterfall_SAS";
title  j=l h=12pt c=cx111111 "F-13-1: PSA Best % Change from Baseline (Waterfall) - SAS Production Track";
title2 j=l h=9pt  c=cx444444 "Each bar = one subject's best PSA change; sorted within arm";
footnote j=l h=7pt c=&LRED. "&SYNTHFN.";
proc sgpanel data=_psab dattrmap=_psamap;
    panelby trt01p / columns=2 novarname spacing=8 headerattrs=(weight=bold size=10pt);
    vbarparm category=rank response=best / group=respcat attrid=psa;
    refline -50 / lineattrs=(pattern=shortdash color=cx005A9C);
    colaxis display=none;
    rowaxis label="Best PSA % Change from Baseline" grid values=(-100 to 200 by 50);
    keylegend / position=bottom title='Response Category:';
run;
title; title2; footnote;

/* ============================================================================
   FIGURE F-14-1 : Treatment Exposure Swimmer (top 30 per arm)
   ============================================================================ */
data _swim;
    set adam.adsl(keep=usubjid trt01p trtdurd dthfl)
        cbz_adsl(keep=usubjid trt01p trtdurd dthfl);
    if not missing(trtdurd);
    durm = trtdurd / 30.4375;
run;
proc sort data=_swim; by trt01p descending durm; run;
data _swim30;
    set _swim; by trt01p;
    if first.trt01p then k=0;
    k+1;
    if k <= 30;
    death = (dthfl='Y');
run;
proc sort data=_swim30; by trt01p durm; run;
data _swim30; set _swim30; row=_n_; run;

ods graphics on / reset=index imagename="F-14-1_Swimmer_Plot_SAS";
title  j=l h=12pt c=cx111111 "F-14-1: Treatment Exposure Duration (Swimmer) - SAS Production Track";
title2 j=l h=9pt  c=cx444444 "Bar = months on treatment; X = death on study. Top 30 subjects per arm.";
footnote j=l h=7pt c=&LRED. "&SYNTHFN.";
proc sgpanel data=_swim30;
    panelby trt01p / columns=2 novarname spacing=8 headerattrs=(weight=bold size=10pt);
    styleattrs datacolors=(cx005A9C cxA6192E);
    hbarparm category=row response=durm / group=trt01p barwidth=0.85 nooutline;
    scatter x=durm y=row / markerattrs=(symbol=x size=9 color=cx111111) freq=death
        name='death' legendlabel='Death on study';
    /* Fix the months axis to the data range (~9 mo) so bars fill the panel as in
       the R figure; the default auto-range stretched to ~60 and shrank the bars. */
    colaxis label="Months on Treatment" grid values=(0 to 9 by 3);
    rowaxis display=none;
    keylegend / position=bottom title='Treatment Arm:';
run;
title; title2; footnote;

/* ============================================================================
   FIGURE F-17-1 : Project Optimus Exposure-Response (RDI vs ANC Nadir)
   ============================================================================ */
data _rdi;
    set adam.adex(keep=usubjid trt01p paramcd avisit aval rename=(aval=rdi))
        cbz_adex(keep=usubjid trt01p paramcd avisit aval rename=(aval=rdi));
    if paramcd='RDI' and avisit='ALL CYCLES'; keep usubjid trt01p rdi;
run;
data _nadir;
    set adam.adlb(keep=usubjid paramcd avisit aval rename=(aval=anc))
        cbz_adlb(keep=usubjid paramcd avisit aval rename=(aval=anc));
    /* CYCLE 1 only: ANCNADIR exists at cycles 1-3 for the real MP arm; without this
       filter MP subjects are plotted ~3x and the LOESS is inflated (R uses CYCLE 1). */
    if paramcd='ANCNADIR' and avisit='CYCLE 1'; keep usubjid anc;
run;
proc sql;
    create table _er as
    select a.usubjid, a.trt01p, a.rdi, b.anc
    from _rdi a inner join _nadir b on a.usubjid=b.usubjid
    where a.rdi is not null and b.anc is not null;
quit;

ods graphics on / reset=index imagename="F-17-1_Optimus_Scatter_SAS";
title  j=l h=12pt c=cx111111 "F-17-1: Project Optimus Exposure-Response - SAS Production Track";
title2 j=l h=9pt  c=cx444444 "Continuous ANC nadir (Cycle 1) vs Relative Dose Intensity, LOESS fit by arm";
footnote j=l h=7pt c=&LRED. "&SYNTHFN.";
proc sgplot data=_er nocycleattrs;
    styleattrs datacontrastcolors=(cx005A9C cxA6192E);
    scatter x=rdi y=anc / group=trt01p markerattrs=(symbol=circlefilled size=5) transparency=0.65;
    /* degree=2 + smooth=1.0 mirrors R's loess(span=1.0, degree=2). No CLM: the
       sparse low-RDI MP tail (p5 RDI=79) makes confidence bands fan out into
       slashing artifacts; R's shaded ribbon is cosmetic and not reproduced. */
    loess x=rdi y=anc / group=trt01p nomarkers lineattrs=(thickness=3.5) smooth=1.0 degree=2;
    refline 0.5 / axis=y lineattrs=(pattern=shortdash color=cxE74C3C)
        label="Grade 4 Neutropenia (< 0.5)" labelloc=inside labelpos=min;
    xaxis label="Relative Dose Intensity (%)" grid max=105;
    yaxis label="ANC Nadir Value (x10^3/uL)" min=0 max=6 grid;
    keylegend / position=top title='Treatment Group:';
run;
title; title2; footnote;

ods graphics off;
%put NOTE: [TFL-SAS] All SAS production figures rendered to &SASFIG..;
