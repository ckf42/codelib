@echo off
setlocal EnableDelayedExpansion

set para=
set multiPara=0

:paraProcessing
if [%1]==[] goto endParaProcessing
if [!para!]==[] (
    set para=%1
) else (
    set multiPara=1
    set para=!para! %1
)
shift /1
goto paraProcessing
:endParaProcessing

if [!para!]==[] exit /b
if !multiPara! GEQ 1 (
    set para="!para!"
)
if exist !para! (
    explorer /select,!para!
) else (
    echo !para! does not exist
)

