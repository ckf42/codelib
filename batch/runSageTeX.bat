@echo off
setlocal
setlocal EnableDelayedExpansion
set sageCmd="%LOCALAPPDATA%\SageMath 9.2\runtime\bin\bash.exe" -l "%LOCALAPPDATA%/SageMath 9.2/runtime/opt/sagemath-9.2/sage"
set dirPath=
set filePath=
for /f "usebackq tokens=* delims=" %%r in (`cygpath -m %~dp1`) do set dirPath=%%r
@rem for /f "usebackq tokens=* delims=" %%r in (`cygpath -m %~dpn1`) do set filePath=%%r
for /f "usebackq tokens=* delims=" %%r in (`echo %~n1`) do set filePath=%%r

echo %sageCmd% -c "os.chdir('%dirPath%'); load('%filePath%.sagetex.sage')"
%sageCmd% -c "os.chdir('%dirPath%'); load('%filePath%.sagetex.sage')"
