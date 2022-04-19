%SCRIPT

selectedText = cursor.selectedText();
if (selectedText.length != 0){
    doDelPrevChar = false;
    doDelNextChar = false;
    contentOffset = 0;
    if (selectedText[0] == "$"){
        selectedText = selectedText.slice(1);
    } else {
        doDelPrevChar = true;
    }
    if (selectedText[selectedText.length - 1] == "$"){
        selectedText = selectedText.slice(0, -1);
        contentOffset = 1;
    } else {
        doDelNextChar = true;
    }
    matchObj = selectedText.match(RegExp("(?:^|[^\\\\])(?:\\\\\\\\)*\\$"));
    if (matchObj !== null){
        cursor.movePosition(selectedText.length + contentOffset, cursorEnums.Left);
        cursor.movePosition(matchObj.index + matchObj[0].length - 1, cursorEnums.Right);
        cursor.movePosition(1, cursorEnums.Right, cursorEnums.KeepAnchor);
    } else {
        cursor.removeSelectedText();
        if (doDelPrevChar){cursor.deletePreviousChar();}
        if (doDelNextChar){cursor.deleteChar();}
        editor.insertText([
            "",
            "\\begin{equation*}", 
            selectedText,
            "\\end{equation*}",
            ""
        ].join('\n'));
        while ([" ", ".", ","].includes(editor.text(cursor.lineNumber())[cursor.columnNumber()])){
            cursor.deleteChar();
        }
    }
}
