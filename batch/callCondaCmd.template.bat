@echo off
setlocal

set TargetCondaEnv=CondaEnvironmentToActivate
set TargetCmd=CmdToCall

if [%CONDA_DEFAULT_ENV%]==[%TargetCondaEnv%] (
    %TargetCmd% %*
) else (
    call conda activate %TargetCondaEnv%
    call %0 %*
    call conda deactivate
)

