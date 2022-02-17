@echo off
setlocal EnableDelayedExpansion

set checkDomain=example.com
set requiredFailCount=10
set doSimpleBeep=0
set doPowershellBeep=1
set beepFreq=550
set beepDuration=800
set doTTS=1
set ttsSentence=network disconnected

set currentFailCount=0
echo Hold CTRL-C to quit
:pingLoopBegin

ping %checkDomain% -n 1 >NUL
if ERRORLEVEL 1 (
    set /A "currentFailCount=currentFailCount+1"
) else (
    set currentFailCount=0
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
)

goto pingLoopBegin
