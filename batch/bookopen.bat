@echo off
setlocal
setlocal EnableDelayedExpansion
REM get original chcp
set origChcp=
for /f "usebackq tokens=*" %%o in (`chcp`) do for %%w in (%%o) do set origChcp=%%w
REM set chcp to UTF-8 for display
chcp 65001 >NUL

REM script configs
@REM path to local files directories
set localPathArr[1]=%USERPROFILE%\Desktop\papers
set localPathArr[2]=%USERPROFILE%\Desktop\read
set localPathArr[3]=%USERPROFILE%\Desktop\alt
@REM dir of remote index on remote, leave blank if on drive root
set remoteIndexRemoteDir=
@REM file name of remote index, leave blank if no remote
set remoteIndexName=_bookIndex.txt
@REM where remote index is stored
set remoteIndexCacheDir=%USERPROFILE%\Downloads
@REM path to aggregated local index
set fileListPath=%USERPROFILE%\books\_bookIndex.txt
@REM file dir on remote
set rcloneDrive=gd:books
@REM base cmd for rclone
set rcloneBaseCmd=rclone --progress
@REM cmd used to get files from remote
set rcloneCmd=%rcloneBaseCmd% copy !rcloneDrive!/
@REM cmd used to get index from from remote
set rcloneIndexFetchCmd=!rcloneCmd!
@REM allow unknown para as query? 0/1: F/T
set unknownParaAsQuery=1
@REM use preview window to show long filename? 0/1: F/T
set useFzfPreview=1
@REM the keybind for fzf preview window. Only used for useFzfPreview=1
set fzfPreviewKey=ctrl-e
REM script configs end here

set remoteListPath=%remoteIndexCacheDir%\%remoteIndexName%
set localPathCount=1
:countLocalPathArrLen
if defined localPathArr[!localPathCount!] (
    set /a "localPathCount+=1"
    goto countLocalPathArrLen
)
set /a "localPathCount-=1"
set localPathIdxStr=
for /l %%i in (1,1,!localPathCount!) do (
    set localPathIdxStr=!localPathIdxStr!%%i
)
set localPathChoiceMsg=Where to put the file?
for /l %%i in (1,1,!localPathCount!) do (
    for /f %%p in ("!localPathArr[%%i]!") do (
        set localPathChoiceMsg=!localPathChoiceMsg! %%i: %%~np
    )
)
set localPath=!localPathArr[1]!
for /l %%i in (2,1,%localPathCount%) do (
    set localPath=!localPath! !localPathArr[%%i]!
)

set scriptDebugFlag=0
set needToReindex=0
set needToFetchRemoteIndex=0
set needHelp=0
set needToStartSearch=0
set cliQueryStr=
set inQueryStrings=0
set localFileOnly=0
set extraFzfPara=
set inFzfPara=0
set inDriveOverride=0

:handleParameters
if [%1]==[] goto endHandleParameters
if !scriptDebugFlag! neq 0 echo(para %1

if !inQueryStrings! geq 1 (
    @REM all are query string
    if [!cliQueryStr!]==[] (
        set cliQueryStr=%1
    ) else (
        set cliQueryStr=!cliQueryStr! %1
    )
) else if !inFzfPara! geq 1 (
    if [!extraFzfPara!]==[] (
        set extraFzfPara=%~1
    ) else (
        set extraFzfPara=!extraFzfPara! %~1
    )
    set inFzfPara=0
) else if !inDriveOverride! geq 1 (
    set rcloneDrive=%~1
    set rcloneCmd=%rcloneBaseCmd% copy !rcloneDrive!/
    set inDriveOverride=0
    echo Using remote !rcloneDrive!
) else (
    @REM normal para handling
    if "%~1"=="/help" (
        set needHelp=1
    ) else if "%~1"=="/h" (
        set needHelp=1
    ) else if "%~1"=="/?" (
        set needHelp=1
    ) else if "%~1"=="-h" (
        set needHelp=1
    ) else if "%~1"=="--help" (
        set needHelp=1
    )
    if !needHelp! equ 1 (
        echo %~nx0 switches:
        echo(/?, /h, /help, -h, --help  Display this help message and exit
        echo /r, /refresh               Reindex local files
        echo /f, /fetch                 Fetch remote index file
        @REM echo /R, /rf, /r/f              Equivalent to /f /r
        echo /R                         Equivalent to /f /r
        echo /s, /search                Start searching after /r or /f
        echo /l, /local                 Consider local files only
        echo /-l, /-local               Consider remote files only
        echo /fzf                       The next parameter is to be passed to FZF
        echo /drive                     The next parameter is rclone remote base override
        if %unknownParaAsQuery% geq 1 (
            echo --                         Stop parsing parameters and treat everything afterward as query string
        )
        @REM echo /d, /debug                 Print all debug messages
        goto endCleanUp
    )
    if "%~1"=="/debug" (
        set /a "scriptDebugFlag+=1"
    ) else if "%~1"=="/d" (
        set /a "scriptDebugFlag+=1"
    ) else if "%~1"=="/r" (
        set needToReindex=1
    ) else if "%~1"=="/refresh" (
        set needToReindex=1
    ) else if "%~1"=="/R" (
        set needToReindex=1
        set needToFetchRemoteIndex=1
    @REM ) else if "%~1"=="/rf" (
    @REM     set needToReindex=1
    @REM     set needToFetchRemoteIndex=1
    @REM ) else if "%~1"=="/r/f" (
    @REM     set needToReindex=1
    @REM     set needToFetchRemoteIndex=1
    ) else if "%~1"=="/f" (
        set needToFetchRemoteIndex=1
    ) else if "%~1"=="/fetch" (
        set needToFetchRemoteIndex=1
    ) else if "%~1"=="/s" (
        set needToStartSearch=1
    ) else if "%~1"=="/search" (
        set needToStartSearch=1
    ) else if "%~1"=="/l" (
        set localFileOnly=1
    ) else if "%~1"=="/local" (
        set localFileOnly=1
    ) else if "%~1"=="/-l" (
        set localFileOnly=-1
    ) else if "%~1"=="/-local" (
        set localFileOnly=-1
    ) else if "%~1"=="/fzf" (
        set inFzfPara=1
    ) else if "%~1"=="/drive" (
        set inDriveOverride=1
    ) else if %unknownParaAsQuery% geq 1 (
        @REM special para: query strings
        if "%~1"=="--" (
            set inQueryStrings=1
        ) else if [!cliQueryStr!]==[] (
            set cliQueryStr=%1
        ) else (
            set cliQueryStr=!cliQueryStr! %1
        )
    ) else (
        echo("%1" is not a recognized switch
        goto endCleanUp
    )

)
shift /1
goto handleParameters
:endHandleParameters
if %unknownParaAsQuery% geq 1 (
    if !scriptDebugFlag! neq 0 (
        echo Cli query string:
        echo !cliQueryStr!
    )
)

if !scriptDebugFlag! geq 1 (
    echo debug verbose mode
)
if !scriptDebugFlag! geq 2 (
    echo echoing every command
    echo on
)
if !needToReindex! equ 1 goto reindexPart
if !needToFetchRemoteIndex! equ 1 goto reindexPart
goto startfzfPart

:reindexPart
for %%f in (%remoteListPath%) do echo Cached remote index timestamp %%~tf
for %%f in (%fileListPath%) do echo Current index timestamp %%~tf
if !needToFetchRemoteIndex! equ 1 (
    if defined remoteIndexName (
        echo Fetching remote index ...
        set rcloneFetchRemoteCmd=%rcloneIndexFetchCmd%%remoteIndexRemoteDir%%remoteIndexName% %remoteIndexCacheDir%
        if !scriptDebugFlag! neq 0 (echo rclone command !rcloneFetchRemoteCmd!)
        !rcloneFetchRemoteCmd!
        if !errorlevel! neq 0 (
            echo error occured with exitcode !errorlevel!
            goto endCleanUp
        )
        if not !needToReindex! equ 1 (echo Local index is not updated)
    ) else ( echo No remote index setup )
)
if !needToReindex! equ 1 (
    echo Refreshing index ...
    set remoteFileCount=0
    set localFileCount=0
    if defined remoteIndexName (
        for /f %%r in ('type %remoteListPath% ^| find /c /v ""') do (
            set remoteFileCount=%%r
            echo Remote file count: %%r
        )
    )
    if !scriptDebugFlag! neq 0 echo truncating local index
    break>%fileListPath%
    if !scriptDebugFlag! neq 0 echo rewriting local index
    dir /s /b /o:-dn !localPath!>>%fileListPath%
    for /f %%r in ('type %fileListPath% ^| find /c /v ""') do (
        set localFileCount=%%r
        echo Local file count: %%r
    )

    @rem find local file in remote and remove from cached remote index
    for %%f in ("%fileListPath%") do (
        if !scriptDebugFlag! neq 0 (echo Writing local filenames in %TEMP%\%%~nxf.tmp)
        break>%TEMP%\%%~nxf.tmp
        for /f "tokens=*" %%l in (%%~f) do (
            >>%TEMP%\%%~nxf.tmp echo %%~nxl
        )
        if !scriptDebugFlag! neq 0 (echo Writing filtered remote filepaths in %TEMP%\%%~nxf.tmp.tmp)
        break>%TEMP%\%%~nxf.tmp.tmp
        if defined remoteIndexName (
            findstr /L /V /G:"%TEMP%\%%~nxf.tmp" %remoteListPath% >%TEMP%\%%~nxf.tmp.tmp
        )
        @REM type %%f >>%TEMP%\%%~nxf.tmp.tmp
        type %TEMP%\%%~nxf.tmp.tmp >>%%f
        if !scriptDebugFlag! neq 0 (echo Cleaning up tmp files)
        del %TEMP%\%%~nxf.tmp %TEMP%\%%~nxf.tmp.tmp
    )
)
if !needToStartSearch! equ 1 goto startfzfPart
goto endCleanUp

:startfzfPart
REM san check
if not exist %fileListPath% (
    echo %fileListPath% not found
    goto endCleanUp
)
set fzfCmd=fzf
if !useFzfPreview! neq 0 (
    set fzfCmd=!fzfCmd! --preview "echo {}" --preview-window "hidden:wrap" ^
--bind "!fzfPreviewKey!:toggle-preview"
)
if not [!cliQueryStr!]==[] (
    set fzfCmd=!fzfCmd! -q "!cliQueryStr!"
)
if not [!extraFzfPara!]==[] (
    set fzfCmd=!fzfCmd! !extraFzfPara!
)
if !scriptDebugFlag! neq 0 (echo fzfCmd !fzfCmd!)

set fileFilterCmd=type %fileListPath%
if !localFileOnly! neq 0 (
    set findStrPattern=/C:!localPathArr[1]!
    for /l %%i in (2,1,%localPathCount%) do (
        set findStrPattern=!findStrPattern! /C:!localPathArr[%%i]!
    )
    set fileFilterCmd=!fileFilterCmd! ^| findstr !findStrPattern!
    if !localFileOnly! equ -1 (
        set fileFilterCmd=!fileFilterCmd! /V
    )
)
if !scriptDebugFlag! neq 0 (echo !fileFilterCmd!)

for /f "usebackq tokens=* delims=;" %%r in (`!fileFilterCmd! ^| !fzfCmd!`) do set fzfResult=%%r
if !scriptDebugFlag! neq 0 (echo fzfResult is !fzfResult!)
if not [!fzfResult!]==[] (
    if exist "!fzfResult!" (
        echo Selected local file
        echo "!fzfResult!"
        choice /C YNS /M "Open file? ([Y]es / [N]o / [S]elect instead)?"
        if errorlevel 3 (
            echo Selecting file ...
            @REM assumed local file is recorded with full path
            explorer /select,"!fzfResult!"
        ) else if errorlevel 2 (
            echo Action cancelled
        ) else if errorlevel 1 (
            echo Opening file ...
            explorer "!fzfResult!"
        ) else (
            echo Error occured
            goto endCleanUp
        )
    ) else (
        echo File
        echo "!fzfResult!"
        echo is on remote
        choice /M "Download from remote?"
        if errorlevel 2 (
            echo Action cancelled
            goto endCleanUp
        )
        @REM set downloadPath=0
        set downloadPath=
        choice /M "!localPathChoiceMsg!" /C !localPathIdxStr!
        @REM set selectedDownloadPathIdx=!errorlevel!
        for /f %%i in ("!errorlevel!") do set downloadPath=!localPathArr[%%i]!
        if !scriptDebugFlag! neq 0 (echo download path "!downloadPath!")
        if not defined downloadPath (
            echo Error occured
            goto endCleanUp
        )
        echo Confirm download
        echo !fzfResult!
        echo to
        choice /M "!downloadPath!?"
        if errorlevel 2 (
            echo Action cancelled
            goto endCleanUp
        )
        echo Downloading ...
        if !scriptDebugFlag! neq 0 (echo !rcloneCmd!"!fzfResult!" !downloadPath!)
        ( !rcloneCmd!"!fzfResult!" !downloadPath! ) && (
            REM touching file
            for %%r in ("!fzfResult!") do @( copy /b "!downloadPath!\%%~nxr"+,, "!downloadPath!\" )
        ) && (
            echo Updating index ...
            for %%r in ("!fzfResult!") do @(
                for %%f in ("%fileListPath%") do (
                    if !scriptDebugFlag! neq 0 (
                        echo %TEMP%\%%~nxf.tmp
                        echo %%~nxr
                    )
                    break>%TEMP%\%%~nxf.tmp
                    type %fileListPath% >%TEMP%\%%~nxf.tmp
                    type %TEMP%\%%~nxf.tmp | findstr /L /V /C:"%%~nxr" >%fileListPath%
                    del %TEMP%\%%~nxf.tmp
                )
                echo !downloadPath!\%%~nxr >>%fileListPath%
                if !scriptDebugFlag! neq 0 (
                    echo downloaded path "!downloadPath!\%%~nxr"
                )
            )
            choice /C YNS /M "Open file? ([Y]es / [N]o / [S]elect instead)?"
            if errorlevel 3 (
                echo Selecting file ...
                @REM assumed local file is recorded with full path
                for %%r in ("!fzfResult!") do (
                    if !scriptDebugFlag! neq 0 (echo explorer /select,"!downloadPath!\%%~nxr")
                    explorer /select,"!downloadPath!\%%~nxr"
                )
            ) else if errorlevel 2 (
                echo Action cancelled
            ) else if errorlevel 1 (
                echo Opening file ...
                for %%r in ("!fzfResult!") do (
                    if !scriptDebugFlag! neq 0 (echo explorer "!downloadPath!\%%~nxr")
                    explorer "!downloadPath!\%%~nxr"
                )
            ) else (
                echo Error occured
                goto endCleanUp
            )
            break>nul
        ) || ( echo download failed )
    )
) else (
    if !scriptDebugFlag! neq 0 (echo cancelled)
)

:endCleanUp
@REM reset chcp
chcp !origChcp! >NUL
endlocal
