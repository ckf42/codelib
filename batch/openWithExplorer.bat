@echo off
setlocal EnableDelayedExpansion

set para=
@REM set multiPara=0

:paraProcessing
if ["%~1"]==[""] goto endParaProcessing
if [!para!]==[] (
    for /f "tokens=*" %%p in ("%~1") do set para=%%p
) else (
    @REM set multiPara=1
    for /f "tokens=*" %%p in ("%~1") do set para=!para! %%p
)
shift /1
goto paraProcessing
:endParaProcessing

if [!para!]==[] exit /b
@REM if !multiPara! GEQ 1 (
set para="!para!"
@REM )
if exist !para! (
    explorer !para!
) else (
    echo !para! does not exist
)

