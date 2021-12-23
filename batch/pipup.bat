@echo off
setlocal
setlocal EnableDelayedExpansion
set updateList=
set hasChosenPackage=0
for /f "usebackq tokens=1" %%s in (`pip list -o ^| fzf --header-lines=2 -m --sort -n 1`) do (
    set hasChosenPackage=1
    if [!updateList!]==[] (
        set updateList=%%s
    ) else (
        set updateList=!updateList! %%s
    )
)
if !hasChosenPackage! geq 1 (
    echo Will execute the following command:
    echo pip install -U !updateList!
    choice /C YN /M "Press Y to proceed, N for cancel"
    if not errorlevel 2 (
        pip install -U !updateList!
    )
)
