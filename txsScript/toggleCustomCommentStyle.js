%SCRIPT

var commentSignAdd = "% ";
var commentSignRemoveRegex = new RegExp("^" + commentSignAdd);

cursor.beginEditBlock();

function moveCursor(newLine, newCol, withAnchorKept=false){
    var currentLine = cursor.lineNumber();
    if (currentLine < newLine){
        cursor.movePosition(newLine - currentLine, 
                            cursorEnums.Down,
                            withAnchorKept ? cursorEnums.KeepAnchor : cursorEnums.MoveAnchor);
    }
    if (currentLine > newLine){
        cursor.movePosition(currentLine - newLine, 
                            cursorEnums.Up,
                            withAnchorKept ? cursorEnums.KeepAnchor : cursorEnums.MoveAnchor);
    }  
    cursor.movePosition(1,
                        newCol >= 0 ? cursorEnums.StartOfLine : cursorEnums.EndOfLine,
                        withAnchorKept ? cursorEnums.KeepAnchor : cursorEnums.MoveAnchor);
    cursor.movePosition(newCol >= 0 ? newCol : (-1 - newCol),
                        newCol >= 0 ? cursorEnums.Right : cursorEnums.Left,
                        withAnchorKept ? cursorEnums.KeepAnchor : cursorEnums.MoveAnchor);
}

var cursorLine = cursor.lineNumber();
var cursorCol = cursor.columnNumber();
var anchorLine = cursor.anchorLineNumber();
var anchorCol = cursor.anchorColumnNumber();

var lineArray = [];
for (var i = Math.min(cursorLine, anchorLine); i <= Math.max(cursorLine, anchorLine); ++i){
    lineArray.push(editor.text(i));
}
var cursorOffset = lineArray[0].length;
if (commentSignRemoveRegex.test(lineArray[0])){
    // to uncomment
    for (var i = 0; i < lineArray.length; ++i){
        lineArray[i] = lineArray[i].replace(commentSignRemoveRegex, "");
    }
} else {
    // to comment
    for (var i = 0; i < lineArray.length; ++i){
        lineArray[i] = commentSignAdd + lineArray[i];
    }
}
cursorOffset = lineArray[0].length - cursorOffset;
var replaceText = lineArray.join("\n");

// text replacement
moveCursor(Math.min(cursorLine, anchorLine), 0);
moveCursor(Math.max(cursorLine, anchorLine), -1, true);
cursor.replaceSelectedText(replaceText);

// reset cursor and anchor position
moveCursor(anchorLine, Math.max(0, anchorCol + cursorOffset));
if (cursorLine != anchorLine || cursorCol != anchorCol){
    moveCursor(cursorLine, Math.max(0, cursorCol + cursorOffset), true);
}

cursor.endEditBlock();
