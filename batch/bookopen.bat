@echo off
setlocal
setlocal EnableDelayedExpansion
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
set fileListPath=%USERPROFILE%\Desktop\aggregatedFileList.txt
@REM file dir on remote
set rcloneDrive=gd:books
@REM cmd used to get files from remote
set rcloneCmd=rclone --drive-shared-with-me copy --progress %rcloneDrive%/
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

:handleParameters
if [%1]==[] goto endHandleParameters
if !scriptDebugFlag! neq 0 echo(para %1
if "%1"=="/help" (
    set needHelp=1
) else if "%1"=="/h" (
    set needHelp=1
) else if "%1"=="/?" (
    set needHelp=1
) else if "%1"=="-h" (
    set needHelp=1
) else if "%1"=="--help" (
    set needHelp=1
)
if !needHelp! equ 1 (
    echo %~nx0 switches:
    echo(/?, /h, /help, -h, --help  Display this help message and exit
    echo /r, /refresh               Reindex local files
    echo /f, /fetch                 Fetch remote index file
    echo /R, /rf, /r/f              Equivalent to /r /f
    echo /s, /search                Start searching after /r or /f
    REM echo /debug Print all debug messages
    goto endCleanUp
)
if "%1"=="/debug" (
    set /a "scriptDebugFlag+=1"
) else if "%1"=="/r" (
    set needToReindex=1
) else if "%1"=="/refresh" (
    set needToReindex=1
) else if "%1"=="/R" (
    set needToReindex=1
    set needToFetchRemoteIndex=1
) else if "%1"=="/rf" (
    set needToReindex=1
    set needToFetchRemoteIndex=1
) else if "%1"=="/r/f" (
    set needToReindex=1
    set needToFetchRemoteIndex=1
) else if "%1"=="/f" (
    set needToFetchRemoteIndex=1
) else if "%1"=="/fetch" (
    set needToFetchRemoteIndex=1
) else if "%1"=="/s" (
    set needToStartSearch=1
) else if "%1"=="/search" (
    set needToStartSearch=1
) else (
    echo("%1" is not a recognized switch
    goto endCleanUp
)
shift /1
goto handleParameters
:endHandleParameters

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
        set rcloneFetchRemoteCmd=%rcloneCmd%%remoteIndexRemoteDir%%remoteIndexName% %remoteIndexCacheDir%
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
    @REM set processedFileCount=0
    @REM set processedFileRatio=0
    @REM set processedFileRatioOld=999
    if defined remoteIndexName (
        for /f %%r in ('type %remoteListPath% ^| find /c /v ""') do (
            set remoteFileCount=%%r
            echo Remote file count: %%r
        )
    )
    if !scriptDebugFlag! neq 0 echo truncating local index
    break>%fileListPath%
    REM %FZF_DEFAULT_COMMAND% . %localPath%>>%fileListPath%
    if !scriptDebugFlag! neq 0 echo rewriting local index
    dir /s /b !localPath!>>%fileListPath%
    for /f %%r in ('type %fileListPath% ^| find /c /v ""') do (
        set localFileCount=%%r
        echo Local file count: %%r
    )

    rem find remote file not in local and append to local index
    rem for /f "tokens=*" %%f in (%remoteListPath%) do (
    rem     findstr /L /C:"%%~nxf" %fileListPath% >nul
    rem     if errorlevel 1 (
    rem         if !scriptDebugFlag! neq 0 (echo "%%f" not in local)
    rem         echo %%f>>%fileListPath%
    rem     )
    rem     set /a "processedFileCount+=1"
    rem     set /a "processedFileRatio=processedFileCount*100/remoteFileCount"
    rem     if not !processedFileRatio! equ !processedFileRatioOld! (
    rem         if not !processedFileCount! equ 1 (
    rem             REM not first print, need to overwrite past progress
    rem             set /p="A[1M" <nul
    rem         )
    rem         set /p="Processed !processedFileRatio!%%" <nul
    rem         set processedFileRatioOld=!processedFileRatio!
    rem     )
    rem )
    rem echo(
    rem echo Done

    rem find local file in remote and remote from cached remote index
    for %%f in ("%fileListPath%") do (
        if !scriptDebugFlag! neq 0 (echo Writing %TEMP%\%%~nxf.tmp)
        break>%TEMP%\%%~nxf.tmp
        break>%TEMP%\%%~nxf.tmp.tmp
        for /f "tokens=*" %%l in (%%~f) do (
            >>%TEMP%\%%~nxf.tmp echo %%~nxl
        )
        if !scriptDebugFlag! neq 0 (echo Writing %TEMP%\%%~nxf.tmp.tmp)
        if defined remoteIndexName (
            findstr /V /G:"%TEMP%\%%~nxf.tmp" %remoteListPath% >%TEMP%\%%~nxf.tmp.tmp
        )
        type %%f >>%TEMP%\%%~nxf.tmp.tmp
        type %TEMP%\%%~nxf.tmp.tmp >%%f
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
for /f "tokens=* delims=;" %%r in ('type %fileListPath% ^| fzf') do set fzfResult=%%r
if !scriptDebugFlag! neq 0 (echo fzfResult is !fzfResult!)
if not [!fzfResult!]==[] (
    @REM if !scriptDebugFlag! neq 0 (
    @REM     echo file selected
    @REM     echo decision part "!fzfResult:~0,25!"
    @REM )
    @REM if "!fzfResult:~0,25!"=="C:\Users\akfchan\Desktop\" (
    if exist "!fzfResult!" (
        echo Selected local file
        echo "!fzfResult!"
        choice /M "Open file?"
        if errorlevel 2 (
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
        set downloadPath=0
        @REM choice /M "Where to put the file? 1: read, 2: papers, 3: alt" /C 123
        choice /M "!localPathChoiceMsg!" /C !localPathIdxStr!
        @REM if errorlevel 3 (
        @REM     set downloadPath=%altDirPath%
        @REM ) else if errorlevel 2 (
        @REM     set downloadPath=%papersDirPath%
        @REM ) else if errorlevel 1 (
        @REM     set downloadPath=%readDirPath%
        @REM ) else (
        @REM     echo Error occured
        @REM     goto endCleanUp
        @REM )
        set selectedDownloadPathIdx=!errorlevel!
        set downloadPath=
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
        if !scriptDebugFlag! neq 0 (echo %rcloneCmd%"!fzfResult!" !downloadPath!)
        ( %rcloneCmd%"!fzfResult!" !downloadPath! ) && (
            REM touching file
            for %%r in ("!fzfResult!") do @( copy /b "!downloadPath!\%%~nxr"+,, "!downloadPath!\" )
        ) && (
            echo Updating index ...
            for %%r in ("!fzfResult!") do @( echo !downloadPath!\%%~nxr>>%fileListPath% )
            for %%f in ("%fileListPath%") do @(
                if !scriptDebugFlag! neq 0 (echo %TEMP%\%%~nxf.tmp)
                break>%TEMP%\%%~nxf.tmp
                type %fileListPath%>%TEMP%\%%~nxf.tmp
                type %TEMP%\%%~nxf.tmp | findstr /v /C:"!fzfResult!">%fileListPath%
                del %TEMP%\%%~nxf.tmp
            )
            if !scriptDebugFlag! neq 0 (
                for %%r in ("!fzfResult!") do (
                    echo downloaded path "!downloadPath!\%%~nxr"
                )
            )
            choice /M "Open downloaded file?" /C NY
            if errorlevel 2 (
                for %%r in ("!fzfResult!") do @( explorer "!downloadPath!\%%~nxr" )
            )
            break>nul
        ) || ( echo download failed )
    )
) else (
    if !scriptDebugFlag! neq 0 (echo cancelled)
)

:endCleanUp
REM reset chcp to en-US
chcp 437 >NUL
endlocal
