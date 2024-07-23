# Description

Some AutoHotkey (v2) scripts.

Being ahk scripts, they are Windows only. Still, I may have hardcoded some constants in the scripts, so I am not sure if they work on other machines.

## MsgGui.ahk

A simple class that shows a simple popup window display text then fades away.

## soundControl.ahk

A simple script that allows controlling speaker / microphone volume by scrolling mouse wheel on taskbar while pressing certain keys. Uses `MsgGui.ahk`

The key bindings are: while mouse on taskbar,

* ctrl + wheel: speaker
* alt + wheel: microphone
    * alt + mid button: mute microphone
* win + x: quit

