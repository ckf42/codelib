texindentPath = "latexindent.exe"
settingYamlFilePath = "latexindent-settings.yaml"
texindentPara = "-s -m"

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

function joinPath(pathFragArr) {
    return pathFragArr.join("\\")
}

function writeCurrentEditorToTmp() {
    tmpFileDir = getSystemStdout("echo %TEMP%");
    tmpFileName = joinPath([tmpFileDir, ".tmp." + new Date().getTime() + ".tex"]);
    writeFile(tmpFileName, editor.text());
    return tmpFileName;
}

tmpFileName = writeCurrentEditorToTmp();
indentCmd = [
    texindentPath,
    texindentPara,
    "-l",
    settingYamlFilePath,
    tmpFileName,
    "-o",
    tmpFileName
].join(" ");
indentCmdProcess = system(indentCmd, tmpFileDir);
indentCmdProcess.waitForFinished();
cmdRes = readFile(tmpFileName);
system(["rm", tmpFileName].join(" "));
editor.setText(cmdRes.split("\r\n").join("\n"));