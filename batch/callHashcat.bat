@echo off
setlocal EnableDelayedExpansion 

@REM Setting
set hashcatPath=

set hashcatDir=
for /f %%p in ("!hashcatPath!") do set hashcatDir=%%~dpp
set colLen=0
set inputParas=
set isRelativePath=0
for /f "usebackq tokens=* delims=" %%l in (`mode con /status ^| awk 'FNR^=^=5 {print $2^; exit}'`) do (
    set colLen=%%l
)
for %%p in (%*) do (
    set isRelativePath=0
    if exist %%p (
        if exist %~dp0%%p (
            set isRelativePath=1
        )
    ) 
    if !isRelativePath!==0 (
        set inputParas=!inputParas! %%p
    ) else (
        set inputParas=!inputParas! %~dp0%%p
    )
)
@REM echo Expanded arguments !inputParas!
cd /D %hashcatDir%
hashcat.exe !inputParas!
echo Press Enter to clean up
pause
mode con cols=!colLen!
endlocal
