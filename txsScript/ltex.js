ltexVSMainPath = "%USERPROFILE%\\.vscode-oss\\extensions"
ltexScriptDir = ""
configPath = ""

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

if (ltexVSMainPath.length != 0) {
    ltexScriptDir = getSystemStdout("echo " + ltexVSMainPath)
    res = getSystemStdout("echo valentjn.vscode-ltex-*", ltexScriptDir)
    // possible multiple versions of ltex-vs plugin, not all have ltex
    for (let p of res.split(" ")) {
        sDir = joinPath([ltexScriptDir, p, "lib"]);
        sDir = joinPath([sDir, getSystemStdout("echo ltex-ls-*", sDir), "bin"]);
        if (checkFileExists("ltex-cli.bat", sDir)) {
            ltexScriptDir = sDir;
            break;
        } else {
            ltexScriptDir = "";
        }
    }
}


if (configPath.length != 0) {
    configPath = "--client-configuration=" + configPath;
}

tmpFileName = writeCurrentEditorToTmp();
getSystemStdout([joinPath([ltexScriptDir, "ltex-cli.bat"]), configPath, tmpFileName].join(" "), ltexScriptDir);
system(["rm", tmpFileName].join(" "));
