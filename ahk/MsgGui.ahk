class MsgGui
{
    __New(msgPrefix := "", title := "")
    {
        this.msgPrefix := msgPrefix
        this.gui := Gui("+AlwaysOnTop -Caption +Owner -SysMenu", title)
        this.fontOption := "s20 cWhite"
        this.fontName := "Verdana"
        this.gui.backColor := "Black"
        this.gui.SetFont(this.fontOption, this.fontName)
        this.textCtrl := this.gui.AddText(, "")
        this.fadeFunc := this.Fade.Bind(this)
        this.fadeLevel := 0
    }

    SetFont(opt)
    {
        this.fontOption := opt
        this.gui.SetFont(opt, this.fontName)
    }

    Fade()
    {
        if (this.fadeLevel >= 4)
        {
            this.gui.Hide()
            return
        }
        ++this.fadeLevel
        WinSetTransparent(255 - 51 * this.fadeLevel, this.gui)
        SetTimer(this.fadeFunc, -80)
    }

    Show(msg)
    {
        ; method adapted from https://stackoverflow.com/a/49354127
        SetTimer(this.fadeFunc, 0)
        this.fadeLevel := 0
        WinSetTransparent(255, this.gui)
        displayText := this.msgPrefix . msg
        tempGui := Gui()
        tempGui.SetFont(this.fontOption, this.fontName)
        tempTextCtrl := tempGui.AddText(, displayText)
        tempTextCtrl.GetPos(, , &w, &h)
        tempGui.Destroy()
        tempGui := ""
        this.textCtrl.Text := displayText
        this.textCtrl.Move(, , w, h)
        this.gui.Show("X30 Y30 AutoSize NA")
        SetTimer(this.fadeFunc, -2000)
    }

}


