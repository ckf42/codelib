#include MsgGui.ahk

MouseIsOver(WinTitle) {
    MouseGetPos(, , &Win)
    return WinExist(WinTitle . " ahk_id " . Win)
}

mbox := MsgGui("Mic vol: ", "Microphone volume")
micDevName := SoundGetName(1)

; when mouse is on taskbar
#HotIf MouseIsOver("ahk_class Shell_TrayWnd") 
; ctrl + wheel up : speaker vol up
^WheelUp::Send "{Volume_Up}"
; ctrl + wheel down : speaker vol down
^WheelDown::Send "{Volume_Down}"
; alt + wheel up : mic vol up
!WheelUp::
{
    SoundSetVolume("+1", , micDevName)
    newVol := Round(SoundGetVolume(, micDevName))
    if (newVol != 0)
    {
        SoundSetMute(false, , micDevName)
    }
    mbox.Show(newVol)

}
; alt + wheel down : mic vol down
!WheelDown::
{
    SoundSetVolume("-1", , micDevName)
    newVol := Round(SoundGetVolume(, micDevName))
    if (newVol = 0)
    {
        SoundSetMute(true, , micDevName)
    }
    mbox.Show(newVol)
}
; alt + wheel btn : mute mic, set vol 0
!MButton::
{
    SoundSetVolume("0", , micDevName)
    SoundSetMute(true, , micDevName)
    newVol := Round(SoundGetVolume(, micDevName))
    mbox.Show(newVol)
}
; win + x : quit
#x::ExitApp
#HotIf

