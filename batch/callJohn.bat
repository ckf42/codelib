@echo off
setlocal EnableDelayedExpansion

set johnPath=

set johnDir=
for /f %%p in ("!johnPath!") do set johnDir=%%~dpp
set cliArg=%*
set processedCliArg=john.exe
:argProc
for /F "tokens=1*" %%c in ("!cliArg!") do (
    @REM echo arg:%%c
    set processedSubArg=
    set postProcessedArg=
    for %%e in (%%c) do (
        if exist %CD%\%%e (
            set postProcessedArg=%CD%\%%e
        ) else (
            set postProcessedArg=%%e
        )
        if defined processedSubArg (
            set processedSubArg=!processedSubArg!=!postProcessedArg!
        ) else (
            set processedSubArg=!postProcessedArg!
        )
    )
    set processedCliArg=!processedCliArg! !processedSubArg!
    set cliArg=%%d
)
if defined cliArg goto argProc

cd /d !johnDir!
!processedCliArg!

endlocal
