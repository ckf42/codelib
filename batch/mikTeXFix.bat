@echo off
setlocal
cd %APPDATA%\MiKTeX\2.9
set curlcmd=C:\Windows\System32\curl.exe -kLO
set tarcmd=C:\Windows\System32\tar.exe -xf

@REM latex package
set targetPackage=l3backend l3kernel l3experimental l3packages
for %%a in (%targetPackage%) do (
    echo ----- Downloading package %%a -----
    %curlcmd% http://mirrors.ctan.org/install/macros/latex/contrib/%%a.tds.zip
    echo ----- Extracting downloaded archive -----
    %tarcmd% %%a.tds.zip
    echo ----- Cleaning up -----
    del %%a.tds.zip
)
@REM special case for unicode-data, generic package, different download link
echo ----- Downloading package unicode-data -----
%curlcmd% http://mirrors.ctan.org/install/macros/generic/unicode-data.tds.zip
echo ----- Extracting downloaded archive -----
%tarcmd% unicode-data.tds.zip
echo ----- Cleaning up -----
del unicode-data.tds.zip

echo ----- Refreshing filename database -----
initexmf --update-fndb --mkmaps --mklangs --mklinks --verbose
echo ----- Done -----
cd %~dp0
