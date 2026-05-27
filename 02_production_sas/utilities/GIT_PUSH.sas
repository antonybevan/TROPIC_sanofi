/******************************************************************************
 * Program:      GIT_PUSH.sas
 * Purpose:      Push changes to Git from SAS OnDemand or local SAS 9.4
 * Note:         Uses gitfn_* kernel functions (not PROC GIT)
 *               Compatible with SAS 9.4 and SAS OnDemand cloud sessions
 ******************************************************************************/

/* 1. Auto-detect and include 00_config.sas */
%macro init_env;
    %if %symexist(PROJ_ROOT) %then %return;
    
    %if %sysfunc(fileexist(00_config.sas)) %then %include "00_config.sas";
    %else %if %sysfunc(fileexist(02_production_sas/00_config.sas)) %then %include "02_production_sas/00_config.sas";
    %else %if %sysfunc(fileexist(../02_production_sas/00_config.sas)) %then %include "../02_production_sas/00_config.sas";
    %else %if %sysfunc(fileexist(../00_config.sas)) %then %include "../00_config.sas";
    %else %if %sysfunc(fileexist(../../00_config.sas)) %then %include "../../00_config.sas";
    %else %do;
        %let _home = %sysfunc(sysget(HOME));
        %if %length(&_home) = 0 %then %let _home = %sysfunc(sysget(USERPROFILE));
        %if %upcase(&SYSSCP) = WIN and %sysfunc(fileexist(&_home/OneDrive/Desktop/TROPIC/02_production_sas/00_config.sas)) %then
            %include "&_home/OneDrive/Desktop/TROPIC/02_production_sas/00_config.sas";
        %else %if %upcase(&SYSSCP) = WIN and %sysfunc(fileexist(&_home/Desktop/TROPIC/02_production_sas/00_config.sas)) %then
            %include "&_home/Desktop/TROPIC/02_production_sas/00_config.sas";
        %else %if %sysfunc(fileexist(&_home/TROPIC/02_production_sas/00_config.sas)) %then
            %include "&_home/TROPIC/02_production_sas/00_config.sas";
        %else %put ERROR: Cannot find 00_config.sas;
    %end;
%mend init_env;
%init_env;

%macro run_git_push;
    /* 2. Configure Git Parameters */
    %if not %symexist(GIT_REPO_PATH) or %superq(GIT_REPO_PATH)= %then %let GIT_REPO_PATH = &PROJ_ROOT;
    %if not %symexist(GIT_COMMIT_MSG) or %superq(GIT_COMMIT_MSG)= %then %let GIT_COMMIT_MSG = Pipeline update from SAS OnDemand;
    %if not %symexist(GIT_AUTHOR) or %superq(GIT_AUTHOR)= %then %let GIT_AUTHOR = %sysget(GIT_AUTHOR);
    %if not %symexist(GIT_EMAIL) or %superq(GIT_EMAIL)= %then %let GIT_EMAIL = %sysget(GIT_EMAIL);
    %if %superq(GIT_AUTHOR)= %then %let GIT_AUTHOR = Clinical Statistical Programmer;
    %if %superq(GIT_EMAIL)= %then %let GIT_EMAIL = programmer@sanofi.com;
    %if not %symexist(GITHUB_USER) or %superq(GITHUB_USER)= %then %let GITHUB_USER = %sysget(GITHUB_USER);
    %if not %symexist(GITHUB_PAT) or %superq(GITHUB_PAT)= %then %let GITHUB_PAT = %sysget(GITHUB_PAT);

    /* 3. Execute Git Operations */
    data _null_;
       put "NOTE: --------------------------------------------------";
       put "NOTE: GIT PUSH - Commit and Push";
       put "NOTE: Repo Path: &GIT_REPO_PATH";
       put "NOTE: --------------------------------------------------";

       rc_add = gitfn_add("&GIT_REPO_PATH", "*");
       put "NOTE: gitfn_add RC=" rc_add;

       rc_commit = gitfn_commit("&GIT_REPO_PATH", "&GIT_COMMIT_MSG", "&GIT_AUTHOR", "&GIT_EMAIL");
       put "NOTE: gitfn_commit RC=" rc_commit;

       %if %length(%superq(GITHUB_PAT)) > 0 and %length(%superq(GITHUB_USER)) > 0 %then %do;
          /* Mask credentials in log */
          options nonotes nosource;
          rc_push = gitfn_push("&GIT_REPO_PATH", "&GITHUB_USER", "&GITHUB_PAT");
          options notes source;
          put "NOTE: gitfn_push RC=" rc_push;
          if rc_push = 0 then put "NOTE: Push completed successfully.";
          else put "ERROR: Push failed. Check credentials and remote access.";
       %end;
       %else %do;
          put "ERROR: Missing Git credentials. Set GITHUB_USER and GITHUB_PAT macro vars or environment variables.";
       %end;

       put "NOTE: --------------------------------------------------";
    run;
%mend run_git_push;
%run_git_push;
