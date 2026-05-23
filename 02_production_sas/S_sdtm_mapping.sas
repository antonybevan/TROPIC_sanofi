*';*";*/;QUIT;RUN;
/* ==============================================================================
   Program: S_sdtm_mapping.sas
   Version: 2.0
   Author: Principal Clinical Data Infrastructure Architect
   Date: 2026-05-23
   Standard: SDTM IG v3.4
   Input: staging.*
   Output: sdtm.dm, sdtm.ae, sdtm.ex, sdtm.cm, sdtm.ds, sdtm.vs, sdtm.lb, sdtm.rs
   Description: Maps and harmonizes staging tables into standardized CDISC SDTM.
                Derives anchors like treatment start date (TRTSDT) and study days.
   ============================================================================== */

%include "00_config.sas";

/* 1. Calculate TRTSDT (Treatment Start Date) per USUBJID */
proc sql;
    create table work.trtsdt_map as
    select usubjid, min(input(substr(exstdtc, 1, 10), yymmdd10.)) as trtsdt format=yymmdd10.
    from staging.ex
    where not missing(exstdtc)
    group by usubjid;
quit;

/* 2. Map DM Domain */
proc sql;
    create table sdtm.dm as
    select 
        dm.studyid length=20,
        dm.subjid length=10,
        dm.usubjid length=40,
        dm.agegrp length=10,
        dm.ageu length=10,
        dm.sex length=1,
        dm.race length=40,
        dm.arm length=40,
        dm.armcd length=20,
        dm.arm2 length=40,
        dm.arma length=40,
        dm.armcd2 length=20,
        input(dm.bsabl, best32.) as bsabl,
        dm.itt length=1,
        dm.pprot length=1,
        dm.safety length=1,
        t.trtsdt as trtsdt format=yymmdd10.,
        input(substr(dm.rfstdtc, 1, 10), yymmdd10.) as randdt format=yymmdd10.,
        input(substr(dm.rfstdtc, 1, 10), yymmdd10.) as rfstdtc format=yymmdd10.,
        input(substr(dm.rfendtc, 1, 10), yymmdd10.) as rfendtc format=yymmdd10.
    from staging.dm as dm
    left join work.trtsdt_map as t on dm.usubjid = t.usubjid;
quit;

/* 3. Map EX Domain */
proc sql;
    create table sdtm.ex as
    select 
        dm.studyid,
        dm.usubjid,
        ex.extrt length=20,
        ex.exlot length=20,
        ex.exdose,
        ex.exdosu length=10,
        ex.exdosfrm length=20,
        ex.exroute length=20,
        ex.exseq,
        ex.visit length=40,
        ex.visitnum,
        input(substr(ex.exstdtc, 1, 10), yymmdd10.) as exstdt format=yymmdd10.,
        input(substr(ex.exendtc, 1, 10), yymmdd10.) as exendt format=yymmdd10.,
        ex.exdelay length=10,
        input(ex.excumd, best32.) as excumd,
        input(ex.excumd2, best32.) as excumd2,
        input(ex.exdose2, best32.) as exdose2,
        input(ex.extint, best32.) as extint,
        input(ex.extrint, best32.) as extrint,
        input(ex.expdose, best32.) as expdose,
        ex.exdsrcm length=100,
        ex.exdsrea length=100,
        case 
            when not missing(t.trtsdt) and not missing(ex.exstdtc) then input(substr(ex.exstdtc, 1, 10), yymmdd10.) - t.trtsdt + 1
            else .
        end as exstdy
    from staging.ex as ex
    left join sdtm.dm as dm on ex.usubjid = dm.usubjid
    left join work.trtsdt_map as t on dm.usubjid = t.usubjid;
quit;

/* 4. Map AE Domain */
proc sql;
    create table sdtm.ae as
    select 
        dm.studyid,
        dm.usubjid,
        ae.aedecod length=100,
        ae.aebodsys length=100,
        ae.aeseq,
        ae.aeser length=1,
        ae.aeacn length=40,
        ae.aecontrt length=1,
        ae.aerel length=20,
        ae.aepatt length=40,
        ae.aeout length=40,
        ae.aetoxgr length=5,
        input(ae.aetoxgrn, best32.) as aetoxgrn,
        ae.aetrtem length=1,
        ae.aestwk,
        ae.aeenwk,
        ae.aeterm length=200,
        ae.aehlgt length=100,
        ae.aehlt length=100,
        ae.aellt length=100,
        case 
            when not missing(dm.rfstdtc) and not missing(ae.aestwk) then dm.rfstdtc + ae.aestwk * 7
            else .
        end as aestdt format=yymmdd10.,
        case 
            when not missing(dm.rfstdtc) and not missing(ae.aeenwk) then dm.rfstdtc + ae.aeenwk * 7
            else .
        end as aeendt format=yymmdd10.
    from staging.ae as ae
    left join sdtm.dm as dm on ae.usubjid = dm.usubjid;
quit;

/* 5. Map LB Domain */
proc sql;
    create table sdtm.lb as
    select 
        dm.studyid,
        dm.usubjid,
        lb.lbseq,
        lb.lbtestcd length=8,
        lb.lbtest length=40,
        lb.lbcat length=40,
        lb.lbscat length=40,
        lb.lborres length=20,
        lb.lborresu length=20,
        lb.lbornrlo length=20,
        lb.lbornrhi length=20,
        lb.lbstresc length=20,
        lb.lbstresn,
        lb.lbstresu length=20,
        lb.lbstnrlo,
        lb.lbstnrhi,
        lb.lbnrind length=20,
        lb.visit length=40,
        lb.visitnum,
        input(substr(lb.lbdtc, 1, 10), yymmdd10.) as lbdt format=yymmdd10.,
        case 
            when not missing(t.trtsdt) and not missing(lb.lbdtc) then input(substr(lb.lbdtc, 1, 10), yymmdd10.) - t.trtsdt + 1
            else .
        end as lbdy
    from staging.lb as lb
    left join sdtm.dm as dm on lb.usubjid = dm.usubjid
    left join work.trtsdt_map as t on dm.usubjid = t.usubjid;
quit;

/* 6. Map CM Domain */
proc sql;
    create table sdtm.cm as
    select 
        dm.studyid,
        dm.usubjid,
        cm.cmseq,
        cm.cmtrt length=100,
        cm.cmdecod length=100,
        cm.cmcat length=40,
        cm.cmindc length=100,
        cm.cmdose length=20,
        cm.cmdosu length=20,
        cm.cmdosrgm length=20,
        cm.visitlength length=40,
        cm.visitnum,
        cm.visit length=40,
        case when not missing(cm.cmstdtc) then input(substr(cm.cmstdtc, 1, 10), yymmdd10.) else . end as cmstdt format=yymmdd10.,
        case when not missing(cm.cmendtc) then input(substr(cm.cmendtc, 1, 10), yymmdd10.) else . end as cmendt format=yymmdd10.,
        case 
            when not missing(t.trtsdt) and not missing(cm.cmstdtc) then input(substr(cm.cmstdtc, 1, 10), yymmdd10.) - t.trtsdt + 1
            else .
        end as cmstdy
    from staging.cm as cm
    left join sdtm.dm as dm on cm.usubjid = dm.usubjid
    left join work.trtsdt_map as t on dm.usubjid = t.usubjid;
quit;

/* 7. Map DS Domain */
proc sql;
    create table sdtm.ds as
    select 
        dm.studyid,
        dm.usubjid,
        ds.dsseq,
        ds.dsdecod length=40,
        ds.dsterm length=100,
        ds.dscat length=40,
        ds.sscat length=40,
        ds.epoch length=40,
        ds.visitnum,
        ds.visit length=40,
        ds.dsstwk,
        case 
            when not missing(dm.rfstdtc) and not missing(ds.dsstwk) then dm.rfstdtc + ds.dsstwk * 7
            else .
        end as dsstdt format=yymmdd10.,
        case 
            when not missing(t.trtsdt) and not missing(ds.dsstwk) then (dm.rfstdtc + ds.dsstwk * 7) - t.trtsdt + 1
            else .
        end as dsstdy
    from staging.ds as ds
    left join sdtm.dm as dm on ds.usubjid = dm.usubjid
    left join work.trtsdt_map as t on dm.usubjid = t.usubjid;
quit;

/* 8. Map VS Domain */
proc sql;
    create table sdtm.vs as
    select 
        dm.studyid,
        dm.usubjid,
        vs.vsseq,
        vs.vstestcd length=8,
        vs.vstest length=40,
        vs.vsorres length=20,
        vs.vsorresu length=20,
        vs.vsstresc length=20,
        vs.vsstresn,
        vs.vsstresu length=20,
        vs.vsblfl length=1,
        vs.visitnum,
        vs.visit length=40,
        input(substr(vs.vsdtc, 1, 10), yymmdd10.) as vsdt format=yymmdd10.,
        case 
            when not missing(t.trtsdt) and not missing(vs.vsdtc) then input(substr(vs.vsdtc, 1, 10), yymmdd10.) - t.trtsdt + 1
            else .
        end as vsdy
    from staging.vs as vs
    left join sdtm.dm as dm on vs.usubjid = dm.usubjid
    left join work.trtsdt_map as t on dm.usubjid = t.usubjid;
quit;

/* 9. Derive RS Domain from Staging DS Efficacy Milestones (Standard Efficacy Fallback) */
proc sql;
    create table sdtm.rs as
    select 
        dm.studyid,
        dm.usubjid,
        case 
            when ds.dsdecod in ('DISEASE PROGRESSION', 'PROGRESSION') then 'PROGRESSIVE DISEASE'
            else 'DEATH'
        end as rstest length=40,
        case 
            when ds.dsdecod in ('DISEASE PROGRESSION', 'PROGRESSION') then 'PD'
            else 'DEATH'
        end as rsorres length=20,
        case 
            when ds.dsdecod in ('DISEASE PROGRESSION', 'PROGRESSION') then 'PD'
            else 'DEATH'
        end as rsstresc length=20,
        case 
            when not missing(dm.rfstdtc) and not missing(ds.dsstwk) then dm.rfstdtc + ds.dsstwk * 7
            else .
        end as rsdt format=yymmdd10.,
        ds.visit length=40,
        'SPONSOR' as rseval length=40,
        case 
            when not missing(t.trtsdt) and not missing(ds.dsstwk) then (dm.rfstdtc + ds.dsstwk * 7) - t.trtsdt + 1
            else .
        end as rsdy
    from staging.ds as ds
    left join sdtm.dm as dm on ds.usubjid = dm.usubjid
    left join work.trtsdt_map as t on dm.usubjid = t.usubjid
    where ds.dsdecod in ('DISEASE PROGRESSION', 'PROGRESSION', 'DEATH', 'DEAD');
quit;

/* Clean up work library */
proc datasets lib=work nolist kill;
run;
quit;
