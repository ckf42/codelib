@echo off

setlocal

for /F "usebackq" %%v in (`echo %CONDA_BAT%`) do @(
    set condaBinPath=%%~dpv
)

for /F "usebackq tokens=1,2" %%n in (`%CONDA_BAT% info --envs`) do @(
    if [%%o] NEQ [] @(
        if [%%o] NEQ [conda] @(
            if [%%n] NEQ [base] @(
                echo ----- %%n -----
                %CONDA_BAT% update --all --yes --name %%n
                %CONDA_BAT% clean --all --yes
                if [%1] EQU [/f] @(
                    dir /B %condaBinPath%\..\envs\%%n\Scripts\*.conda_trash
                    del /F %condaBinPath%\..\envs\%%n\Scripts\*.conda_trash
                )
            )
        )
    )
)

