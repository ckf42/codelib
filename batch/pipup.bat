@echo off
setlocal
setlocal EnableDelayedExpansion
set pipUpdateCmd=pip install -U
set hasChosenPackage=0
for /f "usebackq tokens=1" %%s in (`pip list -o ^| fzf --header-lines=2 -m --sort -n 1`) do (
    set hasChosenPackage=1
    set pipUpdateCmd=!pipUpdateCmd! %%s
    if "%%s"=="pip" (
        set pipUpdateCmd=python -m !pipUpdateCmd!
    )
)
if !hasChosenPackage! geq 1 (
    echo Will execute the following command:
    echo !pipUpdateCmd!
    choice /C YN /M "Press Y to proceed, N for cancel"
    if not errorlevel 2 (
        !pipUpdateCmd!
    )
)
