@echo off
setlocal EnableDelayedExpansion

set explorerCmd=explorer 
set para=

if ["%~1"]==["/select"] (
    set explorerCmd=!explorerCmd!/select,
    shift /1
)

:paraProcessing
if ["%~1"]==[""] goto endParaProcessing
if [!para!]==[] (
    for /f "tokens=*" %%p in ("%~1") do set para=%%p
) else (
    for /f "tokens=*" %%p in ("%~1") do set para=!para! %%p
)
shift /1
goto paraProcessing
:endParaProcessing

if [!para!]==[] exit /b
call :normalizePath "!para!"
if exist !para! (
    !explorerCmd!!para!
) else (
    echo !para! does not exist
)

exit /b
:normalizePath
@REM https://stackoverflow.com/a/33404867
set para=%~f1
exit /b

