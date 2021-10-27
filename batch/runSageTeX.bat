@echo off
setlocal

@rem settings
set sageVersion=9.2
set sageRuntimePath=%LOCALAPPDATA%\SageMath %sageVersion%\runtime

set sageCmd="%sageRuntimePath%\bin\bash.exe" -l "%sageRuntimePath%\opt\sagemath-%sageVersion%\sage"
set dirPath=
for /f "usebackq tokens=* delims=" %%r in (`"%sageRuntimePath%\bin\cygpath.exe" -m %~dp1`) do set dirPath=%%r
set filePath=
for /f "usebackq tokens=* delims=" %%r in (`echo %~n1`) do set filePath=%%r

echo SageMath Version %sageVersion%
@REM echo %sageCmd% -c "os.chdir('%dirPath%'); load('%filePath%.sagetex.sage')"
%sageCmd% -c "os.chdir('%dirPath%'); load('%filePath%.sagetex.sage')"
