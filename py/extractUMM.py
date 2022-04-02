import re
import argparse
import pathlib as path
import subprocess
from sys import stdout

parser = argparse.ArgumentParser()
parser.add_argument('--tex', type=str, help="Path to target tex file")
parser.add_argument('--sty', type=str,
                    help="Path to reference sty file. "
                    "By default determined by kpsewhich")
parser.add_argument('--out', type=str,
                    help="Path to output cmd tex file. "
                    "Default to umm.tex in tex path")
parser.add_argument('--embed',
                    action='store_true',
                    help="Insert umm directly into tex file. "
                    "Ignores --out")
parser.add_argument('--stdout',
                    action='store_true',
                    help="Force output to stdout. Ignores --out and --embed")
parser.add_argument('--verbose',
                    action='store_true',
                    help="Verbose msg")
parser.add_argument('--kpsepath',
                    type=str,
                    help="The path of kpsewhich to use to find the macro sty. "
                    "Useful if you have multiple TeX installations. "
                    "Defaults to the first one in PATH")
args = parser.parse_args()


def findThisMatchBracket(inputStr: str, startPos: int = 0,
                         bracketPair: str = '{}',
                         escapeChar: str = '\\') -> int:
    if len(bracketPair) != 2:
        raise ValueError("bracketPair is not a string of length 2")
    if inputStr[startPos] != bracketPair[0]:
        raise ValueError("character at startPos "
                         f"({startPos}) is not an opening bracket. \n"
                         "Context: "
                         + inputStr[max(0, startPos - 10):
                                    min(len(inputStr), startPos + 10)])
    isEscaped = False
    charIdx = startPos - 1
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


texPath = path.Path((args.tex
                     if args.tex is not None
                     else input("Enter path to target .tex file:\n")
                     ).strip('\'\" '))
if not texPath.is_file() or texPath.suffix != '.tex':
    input("tex is not a valid path")
    exit()

if args.kpsepath is None:
    args.kpsepath = 'kpsewhich'

styPath = path.Path(args.sty.strip('\'\" ')
                    if args.sty is not None
                    else subprocess.run(f'{args.kpsepath} usefulmathmacro.sty',
                                        stdout=subprocess.PIPE,
                                        shell=True,
                                        universal_newlines=True
                                        ).stdout.strip('\r\n'))
if not styPath.is_file() or styPath.suffix != '.sty':
    input(f"ref sty \"{str(styPath)}\" is not a valid path")
    exit()
outputPath = path.Path(args.out.strip('\'\" ')
                       if args.out is not None
                       else texPath.with_name(texPath.stem + '_umm.tex'))
printToStdOut = False
if not args.stdout and not args.embed and outputPath.is_file():
    print(f"\"{str(outputPath)}\" already exists. "
          "Will write to stdout instead")
    printToStdOut = True
elif args.stdout:
    args.embed = False
    printToStdOut = True

print("Parsing tex file")
usedCmd = set()
packageFound = False
with texPath.open('rt', encoding='UTF-8') as f:
    for line in f:
        if not packageFound \
                and line.strip() == r'\usepackage{usefulmathmacro}':
            packageFound = True
        for match in (re.findall(r'(\\[a-zA-Z]+?)\b', line), ):
            if len(match) != 0:
                usedCmd.update(match)
        for match in (re.match(r'\\begin\{([a-zA-Z]+?)\}', line.lstrip()), ):
            if match is not None:
                usedCmd.update(match.groups())

if not packageFound:
    input("UMM not used")
    exit()

if args.verbose:
    print("cmd found: ")
    for cmd in usedCmd:
        print(cmd)

print("Parsing sty file")
# macroDefDict = dict()
# collectedMacroLines = list()
# currentMacroName = ''
# doCollecting = False
# with styPath.open('rt', encoding='UTF-8') as f:
#     for line in f:
#         line = line.rstrip()
#         if doCollecting:
#             # doing multiline collection
#             collectedMacroLines.append(line)
#             if len(line) == 1 and line[0] == '}':
#                 # multiline collection ends
#                 doCollecting = False
#                 macroDefDict[currentMacroName] = collectedMacroLines[:]
#         elif (match := re.match(r'\\ProvideDocument[a-zA-Z]+\{([^}]+?)\}',
#                                 line)) is not None:
#             # start multiline collection
#             collectedMacroLines.clear()
#             currentMacroName = match.group(1)
#             doCollecting = True
#             collectedMacroLines.append(line)
#         elif (match := re.match(r'\\(providecommand|DeclareMathOperator)'
#                                 r'\{(\\[^}]+?)\}(\[\d+\])?',
#                                 line)) is not None:
#             # single line cmd
#             collectedMacroLines.clear()
#             doCollecting = False
#             macroDefDict[match.group(2)] = [line, ]
macroFileContent = list()
with styPath.open('rt', encoding='utf-8') as f:
    for line in f:
        if (lineContent := re.split(r'(?<!\\)(?:\\\\)*%',
                                    line, maxsplit=1)[0]) != '':
            macroFileContent.append(lineContent)
macroFileContent = ''.join(macroFileContent)
macroDefDict = dict()
for macroMatchObj in re.finditer(
    r'^\\(ProvideDocumentCommand|providecommand|DeclareMathOperator)',
    macroFileContent, re.M
):
    matchBegin = macroMatchObj.start()
    matchEnd = macroMatchObj.end()
    macroNameEnd = findThisMatchBracket(macroFileContent, matchEnd)
    macroName = macroFileContent[matchEnd + 1:macroNameEnd]
    contentEnd = macroNameEnd
    if macroMatchObj.group(1) == 'ProvideDocumentCommand':
        contentEnd = findThisMatchBracket(
            macroFileContent,
            findThisMatchBracket(macroFileContent, contentEnd + 1) + 1
        )
    elif macroMatchObj.group(1) == 'providecommand':
        # TODO: deal with brackets in default argument?
        contentEnd = findThisMatchBracket(
            macroFileContent,
            macroFileContent.find('{', contentEnd)
        )
    else:  # DeclareMathOperator
        contentEnd = findThisMatchBracket(macroFileContent, contentEnd + 1)
    contentEnd = macroFileContent.find('\n', contentEnd)
    macroDefDict[macroName] = macroFileContent[matchBegin:contentEnd]\
        .split(sep='\n')

definedMacros = list(macroDefDict.keys())
usedCmd = sorted([m for m in usedCmd if m in definedMacros])

if args.verbose:
    print("Defined cmd: ")
    for cmd in definedMacros:
        print(cmd)

    print("Used cmd: ")
    for cmd in usedCmd:
        print(cmd)

# find dep
macroDepDict = dict()
for m in definedMacros:
    depList = list()
    for line in macroDefDict[m]:
        for match in re.findall(r'(\\[a-zA-Z]+?)\b', line):
            if match in definedMacros and match not in depList and match != m:
                depList.append(match)
    macroDepDict[m] = depList


# resolve dep
topoSortMarkDict = dict()
topoSortOrdering = list()


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


for m in usedCmd:
    if not topoSortMarkDict.get(m, False):
        topoSortVisit(m)

outputBuffer = [
    r'\usepackage{amsmath}',
    r'\usepackage{amssymb}',
    r'\usepackage{amsthm}',
    r'\usepackage{xparse}',
]
for cmdName in topoSortOrdering:
    outputBuffer.extend(macroDefDict.get(cmdName, []))
# for cmdName in usedCmd:
#     outputBuffer.extend(macroDefDict.get(cmdName, []))

if args.embed:
    fileLines = texPath.open('r', encoding='utf-8').readlines()
    lineLoc = next((idx
                    for idx in range(len(fileLines))
                    if fileLines[idx].strip()
                    == '\\usepackage{usefulmathmacro}'),
                   None)
    with texPath.open('w', encoding='utf-8') as f:
        for line in (
            outputBuffer + fileLines
            if lineLoc is None
            else fileLines[:lineLoc] + outputBuffer + fileLines[lineLoc + 1:]
        ):
            print(line.rstrip(), file=f)
else:
    f = stdout
    try:
        if not printToStdOut:
            f = outputPath.open('xt', encoding='UTF-8')
    except FileExistsError:
        print(f"\"{str(outputPath)}\" already exists. \n"
              "Fallback to stdout")
        f = stdout
    except Exception as e:
        print("ERROR:\nUnknown error occurred", e, "Fallback to stdout")
        f = stdout
    finally:
        if f is stdout:
            print("------------------ copy after this line ------------------")
        for line in outputBuffer:
            print(line, file=f)
        if f is stdout:
            print("---------------- copy before this line ----------------")
        else:
            f.close()
            print(f"File written at {str(outputPath)}")
input("Done")
