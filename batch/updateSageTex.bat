@echo off
setlocal enabledelayedexpansion

@rem settings
set sageInstallParentDir=%LOCALAPPDATA%
set sageVersion=
set sageRuntimePath=
set texTree=

if [%sageVersion%] == [] (
    set sageInstallName=
    for /f "usebackq tokens=* delims=" %%r in (`dir /b %sageInstallParentDir% ^| findstr /C:"SageMath"`) do set sageInstallName=%%r
    set sageVersion=!sageInstallName:~9,12!
    set sageRuntimePath=%LOCALAPPDATA%\!sageInstallName!\runtime
)
set sagetexPath=!sageRuntimePath!\opt\sagemath-!sageVersion!\local\share\texmf
if not exist "!sagetexPath!\tex\latex\sagetex\sagetex.sty" (
    echo Cannot find sagetex.sty
    exit /b
)
echo sagePath
echo "!sagetexPath!"

for /f %%l in ('where kpsewhich ^| find /c /v ""') do (
    if %%l equ 0 (
        echo No TeX distribution found
        exit /b
    )
    if %%l geq 1 (
        choice /M "Multiple TeX distribution found, install on all of them?"
        if ERRORLEVEL 2 (
            echo Exiting ...
            exit /b
        )
    )
)

set kpsePath=
for /f "tokens=*" %%k in ('where kpsewhich') do (
    set kpsePath=%%k
    set texhashPath=%%~dpktexhash
    @REM echo !kpsePath!
    @REM echo !texhashPath!
    @REM echo "!kpsePath:~!" -var-value TEXMFLOCAL
    for /f %%p in ('"!kpsePath:~!" -var-value TEXMFLOCAL') do (
        set texTree=%%~dpnp
    )
    if [!texTree!]==[] (
        echo %%k does not give a TEXMFLOCAL
    ) else (
        echo TEXHFMLOCAL at "!texTree!"
        xcopy /E /-Y "!sagetexPath!" "!texTree!"
        !texhashPath!
    )
)

if not exist "!texTree!" (
    echo Cannot locate any texmf tree
    exit /b
)

