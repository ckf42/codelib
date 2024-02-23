import argparse
import pathlib as path
import re
import subprocess
import typing as tp
from shutil import copy2
from sys import stdout


def getArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--tex',
        type=str,
        help="Path to target tex file")
    parser.add_argument(
        '--sty',
        type=str,
        help="Path to reference sty file. "
        "By default it is determined by --kpsewhich")
    parser.add_argument(
        '--out',
        type=str,
        help="Path to output cmd tex file as fragment that can be \\include. "
        "Default to umm.tex in tex path")
    parser.add_argument(
        '--embed',
        action='store_true',
        help="Insert umm directly into tex file. Higher precedence over --out. "
        "No fragment is produced")
    parser.add_argument(
        '--stdout',
        action='store_true',
        help="Force output to stdout. Higher precedence over --out and --embed")
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Show verbose debug msg")
    parser.add_argument(
        '--kpsepath',
        type=str,
        default='kpsewhich',
        help="The path of kpsewhich to use to find the macro sty. "
        "Use this to specify TeX installation if you have multiple. "
        "Defaults to the first `kpsewhich` in PATH")
    parser.add_argument(
        '--nobackup',
        action='store_true',
        help="Do not save a backup copy when using --embed. "
        "Ignored if --embed is not present")
    args = parser.parse_args()
    # process para
    args.texPath = path.Path((
        args.tex
        if args.tex is not None
        else input("Enter path to target .tex file:\n")).strip('\'\" '))
    if not args.texPath.is_file() or args.texPath.suffix != '.tex':
        parser.error("tex is not a valid path")
    args.styPath = path.Path(
        args.sty.strip('\'\" ')
        if args.sty is not None
        else subprocess.run(
            f'{args.kpsepath} usefulmathmacro.sty',
            stdout=subprocess.PIPE,
            shell=True,
            universal_newlines=True).stdout.strip('\r\n'))
    if not args.styPath.is_file() or args.styPath.suffix != '.sty':
        parser.error(f"ref sty \"{str(args.styPath)}\" is not a valid path")
    args.outputPath = path.Path(
        args.out.strip('\'\" ')
        if args.out is not None
        else args.texPath.with_name(args.texPath.stem + '_umm.tex'))
    if args.embed:
        args.outputPath = args.texPath
    args.printToStdOut = False
    if not args.stdout and not args.embed and args.outputPath.is_file():
        print(f"Warning: \"{str(args.outputPath)}\" already exists. "
              "Will write to stdout instead")
        args.printToStdOut = True
    elif args.stdout:
        args.embed = False  # does not make sense to set as True
        args.printToStdOut = True
    return args


def findThisMatchBracket(
        inputStr: str,
        startPos: int = 0,
        bracketPair: str = '{}',
        escapeChar: str = '\\') -> int:
    if len(bracketPair) != 2:
        raise ValueError("bracketPair is not a string of length 2")
    if inputStr[startPos] != bracketPair[0]:
        raise ValueError(
            f"character at startPos ({startPos}) is not an opening bracket. \n"
            "Context: "
            + inputStr[max(0, startPos - 10):min(len(inputStr), startPos + 10)])
    isEscaped: bool = False
    charIdx: int = startPos - 1
    while charIdx >= 0 and inputStr[charIdx] == escapeChar:
        isEscaped = not isEscaped
        charIdx -= 1
    if isEscaped:
        raise ValueError("bracket at startPos is escaped")
    charIdx = startPos
    inputLen = len(inputStr)
    bracketCounter = 0
    while charIdx < inputLen:
        thisChar = inputStr[charIdx]
        if thisChar == escapeChar:
            isEscaped = not escapeChar
        else:
            if not isEscaped:
                if thisChar == bracketPair[0]:
                    bracketCounter += 1
                elif thisChar == bracketPair[1]:
                    bracketCounter -= 1
                    if bracketCounter == 0:
                        return charIdx
            isEscaped = False
        charIdx += 1
    raise ValueError("No matching close bracket")


def getUsedCommandsInDoc(args: argparse.Namespace) -> frozenset[str]:
    print("Parsing tex file")
    usedCmd: set[str] = set()
    packageFound: bool = False
    with args.texPath.open('rt', encoding='UTF-8') as f:
        for line in f:
            line = line.lstrip()
            if line.startswith(r'\usepackage{usefulmathmacro}'):
                packageFound = True
            if len((matchLst := re.findall(r'(\\[a-zA-Z]+?)\b', line))) != 0:
                usedCmd.update(matchLst)
            elif (match := re.match(r'\\begin\{([a-zA-Z]+?)\}', line)) is not None:
                usedCmd.update(match.groups())
    if not packageFound:
        input("UMM not used")
        exit(1)
    if args.verbose:
        print("cmd found: ")
        for cmd in usedCmd:
            print(cmd)
    return frozenset(usedCmd)


def getDefinedCommands(args: argparse.Namespace) -> dict[str, tuple[str, ...]]:
    print("Parsing sty file")
    macroFileContentBuffer: list[str] = list()
    with args.styPath.open('rt', encoding='utf-8') as f:
        for line in f:
            lstr = line.lstrip()
            if len(lstr) == 0 or lstr[0] == '%':
                continue
            if (lineContent := \
                    re.split(r'(?<!\\)(?:\\\\)*%', line, maxsplit=1)[0]) != '':
                if lineContent[-1] != '\n':
                    lineContent += '\n'
                macroFileContentBuffer.append(lineContent)
    macroFileContent: str = ''.join(macroFileContentBuffer)
    macroDefDict: dict[str, tuple[str, ...]] = dict()
    for macroMatchObj in re.finditer(
            r'^\\(ProvideDocumentCommand|providecommand|DeclareMathOperator)',
            macroFileContent,
            re.MULTILINE):
        matchBegin = macroMatchObj.start()
        matchEnd = macroMatchObj.end()
        macroNameEnd = findThisMatchBracket(macroFileContent, matchEnd)
        macroName = macroFileContent[matchEnd + 1:macroNameEnd]
        contentEnd = macroNameEnd
        if macroMatchObj.group(1) == 'ProvideDocumentCommand':
            contentEnd = findThisMatchBracket(
                macroFileContent,
                findThisMatchBracket(macroFileContent, macroNameEnd + 1) + 1)
        elif macroMatchObj.group(1) == 'providecommand':
            # TODO: deal with brackets in default argument?
            contentEnd = findThisMatchBracket(
                macroFileContent,
                macroFileContent.find('{', macroNameEnd))
        else:  # DeclareMathOperator
            contentEnd = findThisMatchBracket(
                macroFileContent, macroNameEnd + 1)
        contentEnd = macroFileContent.find('\n', contentEnd)
        macroContent = macroFileContent[matchBegin:contentEnd].split(sep='\n')
        macroDefDict[macroName] = tuple(macroContent)
    return macroDefDict


def main() -> None:
    args: argparse.Namespace = getArgs()
    definedMacros: dict[str, tuple[str, ...]] = getDefinedCommands(args)
    usedCmds: tuple[str, ...] = tuple(
        cmd
        for cmd in getUsedCommandsInDoc(args)
        if cmd in definedMacros)
    # resolve defined macro dependency
    macroDepDict: dict[str, tuple[str, ...]] = dict()
    for m in definedMacros:
        depList: list[str] = list()
        for line in definedMacros[m]:
            for match in re.findall(r'(\\[a-zA-Z]+?)\b', line):
                if match in definedMacros and match not in depList and match != m:
                    depList.append(match)
        macroDepDict[m] = tuple(depList)
    # resolve used macro output order
    topoSortMarkDict: dict[str, bool] = dict()
    topoSortOrdering: list[str] = list()

    def topoSortVisit(macroName):
        if macroName in topoSortMarkDict:
            if not topoSortMarkDict[macroName]:
                raise ValueError(f"Macro {macroName} has recursive dependency")
            else:
                return
        topoSortMarkDict[macroName] = False
        for depKey in macroDepDict[macroName]:
            topoSortVisit(depKey)
        topoSortMarkDict[macroName] = True
        topoSortOrdering.append(macroName)

    for m in usedCmds:
        if not topoSortMarkDict.get(m, False):
            topoSortVisit(m)
    # prepare output
    # TODO: only include if not already?
    outputBuffer: list[str] = [
        '% UMM content',
        r'\usepackage{amsmath}',
        r'\usepackage{amssymb}',
        r'\usepackage{amsthm}',
        r'\usepackage{xparse}',
    ]
    for cmdName in topoSortOrdering:
        outputBuffer.extend(definedMacros.get(cmdName, list()))
    # do backup
    if args.embed and not args.nobackup:
        baseBackupName = args.texPath.stem + '_ummbackup'
        backupName = baseBackupName
        backupCounter = 0
        while (args.texPath.parent / (backupName + args.texPath.suffix)).exists():
            backupCounter += 1
            backupName = baseBackupName + f"({backupCounter})"
        copy2(args.texPath, args.texPath.parent /
              (backupName + args.texPath.suffix))
        print(f"Backup saved as {backupName + args.texPath.suffix}")
    # load file content for embed
    if args.embed:
        fileLines: list[str] = []
        with args.texPath.open('rt', encoding='utf-8') as f:
            fileLines.extend((line.rstrip() for line in f.readlines()))
        lineLoc: int | None = next(
                (idx
                 for idx, line in enumerate(fileLines)
                 if line.strip().startswith('\\usepackage{usefulmathmacro}')),
                None)
        assert lineLoc is not None, "Cannot find umm in tex"
        fileLines[lineLoc:lineLoc + 1] = outputBuffer
        outputBuffer = fileLines
    # prepare file handle
    fileHandler: tp.TextIO = stdout
    if not args.printToStdOut:
        try:
            fileHandler = args.outputPath.open('wt', encoding='UTF-8')
        # except FileExistsError:
        #     print(f"{str(args.outputPath)} already exists. \nFallback to stdout")
        #     fileHandler = stdout
        #     args.printToStdOut = True
        except Exception as e:
            print(f"ERROR:\nUnknown error occurred\n{e}\nFallback to stdout")
            fileHandler = stdout
            args.printToStdOut = True
    if args.printToStdOut:
        print("----- copy after this line -----")
    for line in outputBuffer:
        print(line, file=fileHandler)
    if not args.printToStdOut:
        fileHandler.close()
        print(f"File outputed \"{str(args.outputPath)}\"")
    else:
        print("----- copy before this line -----")
    print("Done")


if __name__ == '__main__':
    main()
