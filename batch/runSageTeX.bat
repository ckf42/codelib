@echo off
setlocal
setlocal enabledelayedexpansion

@rem settings
set sageInstallParentDir=%LOCALAPPDATA%
set sageVersion=
set sageRuntimePath=

if [%sageVersion%] == [] (
    set sageInstallName=
    for /f "usebackq tokens=* delims=" %%r in (`dir /b %sageInstallParentDir% ^| findstr /C:"SageMath"`) do set sageInstallName=%%r
    set sageVersion=!sageInstallName:~9,12!
    set sageRuntimePath=%LOCALAPPDATA%\SageMath !sageVersion!\runtime
)

set sageCmd="%sageRuntimePath%\bin\bash.exe" -l "%sageRuntimePath%\opt\sagemath-%sageVersion%\sage"
set dirPath=
for /f "usebackq tokens=* delims=" %%r in (`"%sageRuntimePath%\bin\cygpath.exe" -m %~dp1`) do set dirPath=%%r
set filePath=
for /f "usebackq tokens=* delims=" %%r in (`echo %~n1`) do set filePath=%%r

echo SageMath Version %sageVersion%
@REM echo %sageCmd% -c "os.chdir('%dirPath%'); load('%filePath%.sagetex.sage')"
%sageCmd% -c "os.chdir('%dirPath%'); load('%filePath%.sagetex.sage')"
