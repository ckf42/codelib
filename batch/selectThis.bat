@echo off
setlocal EnableDelayedExpansion

set para=

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
set para="!para!"
if exist !para! (
    explorer /select,!para!
) else (
    echo !para! does not exist
)

