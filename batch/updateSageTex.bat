@echo off
setlocal
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
set sageTexStyPath=!sageRuntimePath!\opt\sagemath-!sageVersion!\local\share\texmf\tex\latex\sagetex\sagetex.sty

if not exist "!sageTexStyPath!" (
    echo Cannot find sagetex.sty
    exit /b
)
echo sagePath
echo "!sageTexStyPath!"

if [%texTree%] == [] (
    for /f %%p in ('kpsewhich -var-value TEXMFLOCAL') do (
        set texTree=%%~dpnp
    )
    echo texTree
    echo "!texTree!"
)
if not exist "!texTree!" (
    echo Cannot locate texmf tree
    exit /b
)

copy /-Y "!sageTexStyPath!" "!texTree!\tex\latex\sagetex\sagetex.sty"

