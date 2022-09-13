@echo off
setlocal EnableDelayedExpansion

set curlcmd=C:\Windows\System32\curl.exe -kLO
set curlToStdOutCmd=C:\Windows\System32\curl.exe -kL
set tarcmd=C:\Windows\System32\tar.exe -xf
set ctanURL=https://ctan.org/pkg/

cd %APPDATA%\MiKTeX\2.9

set targetPackage=l3backend l3kernel l3experimental l3packages unicode-data
set dlLink=
for %%a in (%targetPackage%) do (
    echo ----- Finding link for package %%a -----
    for /F usebackq^ tokens^=2^ delims^=^" %%l in (`%curlToStdOutCmd% %ctanURL%%%a ^| findstr https://.*tds.zip`) do @(
        set dlLink=%%l
    )
    echo ----- Downloading package %%a -----
    %curlcmd% !dlLink!
    echo ----- Extracting downloaded archive -----
    %tarcmd% %%a.tds.zip
    echo ----- Cleaning up -----
    del %%a.tds.zip
)

echo ----- Refreshing filename database -----
initexmf --update-fndb --mkmaps --mklangs --mklinks --verbose
echo ----- Done -----
cd %~dp0

