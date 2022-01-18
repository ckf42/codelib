@echo off

for /F "usebackq tokens=1,2" %%n in (`%CONDA_BAT% info --envs`) do @(
    if [%%o] NEQ [] @(
        if [%%o] NEQ [conda] @(
            if [%%n] NEQ [base] @(
                echo %%n
                %CONDA_BAT% update --all --yes --name %%n
            ))))


