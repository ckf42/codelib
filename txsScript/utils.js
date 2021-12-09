// TODO block printing in TXS console
function getSystemStdout(cmd, wd = "", readStdout = true) {
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
    res = getSystemStdout(["where", fileName].join(" "), wd, false);
    return !res.startsWith("INFO: ");
}

function joinPath(pathFragArr) {
    return pathFragArr.join("\\")
}

function writeCurrentEditorToTmp() {
    tmpFileDir = getSystemStdout("echo %TEMP%");
    tmpFileName = joinPath([tmpFileDir, ".tmp." + new Date().getTime() + ".tex"]);
    writeFile(tmpFileName, editor.text());
    return tmpFileName;
}