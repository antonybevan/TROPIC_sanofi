/* QUOTE & MACRO KILLER BLOCK - Resets SAS state if previous errors left things open */
*';*";*/;QUIT;RUN;
%macro _null_; %mend;

/* Release any active library, file, and ODS locks to avoid in-use errors during cleanup */
ods _all_ close;

/* Remove _mclib from the sasautos autocall path list to release system-level directory locks */
options sasautos=(SASAUTOS);

%macro _clear_libs;
    /* pathname() returns blank when a libref is NOT assigned — reliable on all SAS platforms */
    %if %length(%sysfunc(pathname(sdtm)))   > 0 %then %do; libname sdtm   clear; %end;
    %if %length(%sysfunc(pathname(adam)))   > 0 %then %do; libname adam   clear; %end;
    %if %length(%sysfunc(pathname(raw)))    > 0 %then %do; libname raw    clear; %end;
    %if %length(%sysfunc(pathname(legacy))) > 0 %then %do; libname legacy clear; %end;
%mend _clear_libs;
%_clear_libs;
/* Silently deassign _mclib — SAS holds an internal lock on the fileref even after removing it
   from sasautos, so using %sysfunc(filename()) avoids the "still in use" ERROR in the log.   */
%let _rc = %sysfunc(filename(_mclib));

/******************************************************************************
 * Program:      GIT_RESCUE.sas
 * Purpose:      Force-sync SAS OnDemand or SAS 9.4 with TROPIC GitHub Repository
 * Compatibility: SAS 9.4 (Linux / Windows) + SAS OnDemand for Academics
 *
 * NOTES:
 *   - Locates project root dynamically, or defaults safely based on OS.
 *   - gitfn_pull / gitfn_clone require SAS Foundation 9.4 TS1M5+ or ODA.
 * *****************************************************************************/

%let repo_url   = https://github.com/antonybevan/TROPIC_sanofi.git;

/* 1. Auto-detect project root (safe_path) */
%macro get_safe_path;
    %global safe_path;
    
    /* If PROJ_ROOT is already defined via 00_config.sas */
    %if %symexist(PROJ_ROOT) %then %do;
        %if %length(&PROJ_ROOT) > 1 %then %do;
            %let safe_path = &PROJ_ROOT;
            %return;
        %end;
    %end;

    /* Otherwise hunt for the repository signature file */
    %let SLSH = /;
    %let _sig = 02_production_sas&SLSH.00_config.sas;

    %if %sysfunc(fileexist(&_sig)) %then %let safe_path = %sysfunc(abspath(.));
    %else %if %sysfunc(fileexist(..&SLSH.&_sig)) %then %let safe_path = %sysfunc(abspath(..));
    %else %if %sysfunc(fileexist(..&SLSH..&SLSH.&_sig)) %then %let safe_path = %sysfunc(abspath(..&SLSH..));
    %else %do;
        /* OS-specific fallback checking standard home folder paths dynamically */
        %let _home = %sysfunc(sysget(HOME));
        %if %length(&_home) = 0 %then %let _home = %sysfunc(sysget(USERPROFILE));
        
        %if %sysfunc(fileexist(&_home/OneDrive/Desktop/TROPIC/02_production_sas/00_config.sas)) %then
            %let safe_path = &_home/OneDrive/Desktop/TROPIC;
        %else %if %sysfunc(fileexist(&_home/Desktop/TROPIC/02_production_sas/00_config.sas)) %then
            %let safe_path = &_home/Desktop/TROPIC;
        %else %let safe_path = &_home/TROPIC;
    %end;
%mend get_safe_path;
%get_safe_path;

%put NOTE: [GIT_RESCUE] Target Sync path: &safe_path;

/*
   NATIVE RECURSIVE DIRECTORY CLEANUP MACRO
   Does NOT use system shell escape (call system / 'rm -rf'), 
   making it 100% compatible with locked-down SAS OnDemand sessions.
*/
%macro clean_dir_native(dir);
    %macro _rmdir_rec(path);
        %local d_id rc member subpath fileref num_members i sub_fref is_dir f_delete dir_delete;
        
        %let rc = %sysfunc(filename(fileref, &path));
        %let d_id = %sysfunc(dopen(&fileref));
        
        %if &d_id > 0 %then %do;
            %let num_members = %sysfunc(dnum(&d_id));
            %do i = 1 %to &num_members;
                %let member = %sysfunc(dread(&d_id, &i));
                %let subpath = &path/&member;
                
                /* Check if subdirectory or file */
                %let rc = %sysfunc(filename(sub_fref, &subpath));
                %let is_dir = %sysfunc(dopen(&sub_fref));
                
                %if &is_dir > 0 %then %do;
                    %let rc = %sysfunc(dclose(&is_dir));
                    %let rc = %sysfunc(filename(sub_fref));
                    %_rmdir_rec(&subpath);
                %end;
                %else %do;
                    %let rc = %sysfunc(filename(sub_fref));
                    %let rc = %sysfunc(filename(f_delete, &subpath));
                    %let rc = %sysfunc(fdelete(&f_delete));
                    %let rc = %sysfunc(filename(f_delete));
                %end;
            %end;
            %let rc = %sysfunc(dclose(&d_id));
        %end;
        %let rc = %sysfunc(filename(fileref));
        
        /* Delete current empty directory */
        %let rc = %sysfunc(filename(dir_delete, &path));
        %let rc = %sysfunc(fdelete(&dir_delete));
        %let rc = %sysfunc(filename(dir_delete));
    %end; %mend _rmdir_rec;

    %if %sysfunc(fileexist(&dir)) %then %do;
        %put NOTE: [GIT_RESCUE] Directory exists. Executing native recursive delete: &dir;
        %_rmdir_rec(&dir);
    %end;
    %else %do;
        %put NOTE: [GIT_RESCUE] Directory does not exist: &dir;
    %end;
%mend clean_dir_native;

/*
   SYNCHRONOUS GIT RESCUE ENGINE
   Executes rescue steps sequentially within the macro compiler,
   preventing DATA step asynchronous queuing issues.
*/
%macro git_rescue;
    %local rc rc_clone;

    %put NOTE: --------------------------------------------------;
    %put NOTE: Starting GIT RESCUE Operation...;

    /* 1. Only attempt pull if local directory is an initialized Git repo (.git/config exists) */
    %if %sysfunc(fileexist(&safe_path/.git/config)) %then %do;
        %put NOTE: Local repository detected. Attempting gitfn_pull...;
        %let rc = %sysfunc(gitfn_pull(&safe_path));
        %put NOTE: gitfn_pull returned RC=&rc;

        %if &rc = 0 %then %do;
            %put NOTE: SUCCESS! Project updated from GitHub.;
        %end;
        %else %if &rc = 1 %then %do;
            %put NOTE: Repository is already up to date.;
        %end;
        %else %do;
            %put NOTE: Pull failed with RC=&rc.. Initiating FRESH CLONE Protocol...;

            /* Native recursive delete executes synchronously */
            %clean_dir_native(&safe_path);

            %put NOTE: Cloning from &repo_url...;
            %let rc_clone = %sysfunc(gitfn_clone(&repo_url, &safe_path));

            %if &rc_clone = 0 %then %do;
                %put NOTE: SUCCESS! Project reset and re-cloned.;
            %end;
            %else %do;
                %put ERROR: Clone failed. RC=&rc_clone;
            %end;
        %end;
    %end;
    %else %do;
        %put NOTE: No local repository found at &safe_path.. Initiating FRESH CLONE Protocol...;

        %clean_dir_native(&safe_path);

        %put NOTE: Cloning from &repo_url...;
        %let rc_clone = %sysfunc(gitfn_clone(&repo_url, &safe_path));

        %if &rc_clone = 0 %then %do;
            %put NOTE: SUCCESS! Project reset and re-cloned.;
        %end;
        %else %do;
            %put ERROR: Clone failed. RC=&rc_clone;
        %end;
    %end;

    %put NOTE: --------------------------------------------------;
%mend git_rescue;
%git_rescue;
