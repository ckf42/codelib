function getSystemStdout(cmd, wd = "", readStdout = true) {
    // execute cmd in system shell with working dir wd
    // and returns the output as string
    // by default, wd is empty (dir of TXS executable)
    // if readStdout is true, the output is stdout
    // otherwise the output is stderr
    // the output is always displayed in TXS console
    // TODO block output in TXS console
    res = "";
    sysproc = system(cmd, wd);
    if (readStdout) {
        sysproc.standardOutputRead.connect(function (x) { res += x });
    } else {
        sysproc.standardErrorRead.connect(function (x) { res += x });
    }
    sysproc.waitForFinished();
    return res;
}

function checkFileExists(fileName, wd = "") {
    // chech if fileName exists in wd on a Windows system
    // wd defaults to empty (dir of TXS executable)
    res = getSystemStdout(["where", fileName].join(" "), wd, false);
    return !res.startsWith("INFO: ");
}

function joinPath(pathFragArr) {
    // join paths with Windows path sep
    return pathFragArr.join("\\");
}

function writeCurrentEditorToTmp() {
    // write the current editor content in a temp file in temp dir
    // returns the filename of the temp file
    // useful to pass content to external tools
    // filename is decided by time so do not call twice in one second
    tmpFileDir = getSystemStdout("echo %TEMP%");
    tmpFileName = joinPath([tmpFileDir, ".tmp." + new Date().getTime() + ".tex"]);
    writeFile(tmpFileName, editor.text());
    return tmpFileName;
}

function moveCursor(newLine, newCol, withAnchorKept = false){
    // move the cursor to the position defined by (newLine, newCol)
    // if newCol is negative, index will be counted from the end of line (like Python)
    // if withAnchorKept is true, a cursor selection will be made
    // note that both newLine and newCol are 0-based
    // and are capped to the maximum range without warning
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

