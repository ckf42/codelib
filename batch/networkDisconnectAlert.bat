@echo off
setlocal EnableDelayedExpansion

@REM
@REM networkDisconnectAlert.bat
@REM
@REM This batch checks network connectivity by pinging
@REM a remote location at a fixed time interval.
@REM
@REM If numerous pings fail, it sends out predefined alerts.
@REM 
@REM Currently available alerts:
@REM simple batch beep
@REM powershell beep with customizable frequency and duration
@REM TTS by Microsoft Speech API
@REM popup cmd window
@REM
@REM For customization, edit the config below:
@REM

@REM Settings
@REM
@REM The location to ping
     set checkDomain=google.com
     @REM uncomment the following one to test alert
     @REM set checkDomain=0.0.0.0
@REM Number of continuous fail pings before alerting
     set requiredFailCount=3
@REM Time to wait after a successful ping
     set pingWaitTime=30
@REM Time to wait after a failed ping
@REM NOTE: should be smaller than pingWaitTime for speedup
     set pingWaitTimeAfterFailed=5
@REM prompt for pause or quit after a ping? 0/1
@REM NOTE: output more verbose
     set interactiveMode=0
@REM
@REM Alert
@REM
@REM Should we do a simple beep? 0/1
     set doSimpleBeep=0
@REM Should we do a beep with powershell? 0/1
@REM NOTE: there will be a small delay to start powershell  
     set doPowershellBeep=0
@REM Frequency of powershell beep
     set beepFreq=550
@REM Duration of powershell beep, in ms
     set beepDuration=850
@REM Should we do an alert with TTS? 0/1
     set doTTS=0
@REM The sentence to be read with TTS
     set ttsSentence=network disconnected
@REM Should we display a popup window? 0/1
@REM NOTE: will halt until popup window is closed
     set doCmdPopup=1
@REM The sentence to be displayed in popup
     set cmdPopupMsg=Network disconnected!
@REM
@REM Settings end here

set currentFailCount=0
set currentWaitTime=%pingWaitTime%
for /F %%a in ('copy /Z "%~F0" NUL') do set "CR=%%a"

echo You may press CTRL+C to quit while waiting
if %interactiveMode% EQU 0 (
    echo or press any key to skip waiting
)

:pingLoopBegin
if %interactiveMode% EQU 1 (
    echo Waiting !currentWaitTime! second^(s^) for the next ping ...
    choice /C SPQ /D S /T !currentWaitTime! /M "Press [S] to skip waiting, [P] to pause, or [Q] to quit"
    if ERRORLEVEL 3 ( goto endLabel )
    if ERRORLEVEL 2 ( pause )
) else ( 
    <NUL set /P "=Waiting !currentWaitTime! second(s) for the next ping ... "
    >NUL timeout /t !currentWaitTime!
)

set msg=
for /f "usebackq skip=2 tokens=5" %%l in (`ping -n 1 %checkDomain%`) do (
    set msg=%%l
    goto pingParseLoopBreak
)
:pingParseLoopBreak
if ["!msg:~0,4!"]==["time"] (
    set currentFailCount=0
    set currentWaitTime=!pingWaitTime!
    @REM echo Ping succeed at %time%
    <NUL set /P "=Ping succeed at %time% with !msg!!CR!"
) else (
    set /A "currentFailCount=currentFailCount+1"
    set currentWaitTime=!pingWaitTimeAfterFailed!
    echo Ping failed !currentFailCount! / %requiredFailCount% at %time%^^!^^! 
)
if !currentFailCount! GEQ %requiredFailCount% (
    if %doSimpleBeep% EQU 1 (
        rundll32 user32.dll,MessageBeep
    )
    if %doPowershellBeep% EQU 1 (
        powershell "[console]::Beep(%beepFreq%, %beepDuration%)"
    )
    if %doTTS% EQU 1 (
        mshta "javascript:code(close((V=(v=new ActiveXObject('SAPI.SpVoice')).GetVoices().count&&v.Speak('%ttsSentence%'))))"
    )
    if %doCmdPopup% EQU 1 (
        start "" /wait cmd /c "echo %cmdPopupMsg%&echo(&pause"
    )
)
goto pingLoopBegin
:endLabel

