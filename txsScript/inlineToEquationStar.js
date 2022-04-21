%SCRIPT

cursor.beginEditBlock(); 
editor.find("(?=^|[^\\\\])(?=\\\\\\\\)*(\\$)", true, true, false, false, true, false);
var endCol = cursor.columnNumber() - 1;
var endLin = cursor.lineNumber();
cursor.deletePreviousChar()
editor.findPrev();
var begLin = cursor.anchorLineNumber();
cursor.deleteChar();
editor.relayPanelCommand("Search", "display", [0, false]);

if (endLin < begLin){
    cursor.movePosition(begLin - endLin, cursorEnums.Up, cursorEnums.KeepAnchor);
}
if (endLin > begLin){
    cursor.movePosition(endLin - begLin, cursorEnums.Down, cursorEnums.KeepAnchor);
}
cursor.movePosition(1, cursorEnums.StartOfLine, cursorEnums.KeepAnchor);
cursor.movePosition(endCol - (begLin == endLin ? 1 : 0), cursorEnums.Right, cursorEnums.KeepAnchor);

var formulaContent = cursor.selectedText();
cursor.removeSelectedText();
editor.insertText([
    "",
    "\\begin{equation*}", 
    formulaContent,
    "\\end{equation*}",
    ""
].join('\n'));
while ([" ", ".", ","].includes(editor.text(cursor.lineNumber())[cursor.columnNumber()])){
    cursor.deleteChar();
}
cursor.endEditBlock(); 
