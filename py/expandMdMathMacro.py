# TODO deal with emoji in title with gfm identifier rule (w/ emoji package?)
# TODO topo sort marco in dependency order first

import argparse
import re
import pathlib as path
import subprocess
from urllib.parse import urlencode
from personalPylib import findThisMatchBracket as findBracket

parser = argparse.ArgumentParser()
parser.add_argument('--md', type=str, help="Path to target md file")
parser.add_argument('--json', type=str, help="Path to KaTeX macro json file")
parser.add_argument('--out', type=str, help="Path to output file")
parser.add_argument('--webtex', action='store_true',
                    help="Replace LaTeX with link to remotely rendered image")
parser.add_argument('--webLinkInline', type=str,
                    help="Path to remote server for inline TeX "
                    "used by --webtex. "
                    "Defaults to GitHub rendering server",
                    default=r'https://render.githubusercontent.com/'
                    r'render/math?mode=inline&math=')
parser.add_argument('--webLinkDisplay', type=str,
                    help="Path to remote server for display TeX "
                    "used by --webtex. "
                    "Defaults to GitHub rendering server",
                    default=r'https://render.githubusercontent.com/'
                    r'render/math?mode=display&math=')
parser.add_argument('--noConfirm', '-y', action='store_true',
                    help="Do not ask for confirmation")
pandocOption = parser.add_mutually_exclusive_group(required=False)
pandocOption.add_argument('--ipynb', action='store_true',
                          help="Convert output md to ipynb using pandoc. "
                          "Ignored if pandoc cannot be found")
pandocOption.add_argument('--html', action='store_true',
                          help="Convert output md to html5 "
                          "with MathML using pandoc. "
                          "Ignored if pandoc cannot be found")

args = parser.parse_args()

if args.noConfirm:
    print("Will not ask for confirmation")

if (args.ipynb or args.html) and subprocess.run(['pandoc', '--version'],
                                                stdout=subprocess.DEVNULL,
                                                stderr=subprocess.DEVNULL,
                                                shell=True).returncode != 0:
    print("Unable to call pandoc")
    print("Please check if pandoc is installed correctly "
          "and is in environment path")
    print("--ipynb and --html are ignored")
    args.ipynb = args.html = False


filePath = path.Path((args.md
                      if args.md is not None
                      else input("Enter target path to markdown file:\n")
                      ).strip('\'\" '))
if not filePath.is_file() or filePath.suffix != '.md':
    if not args.noConfirm:
        input("md is not a valid path to a markdown file")
    exit()

jsonPath = path.Path((args.json
                      if args.json is not None
                      else input("Enter path to ref json file:\n")
                      ).strip('\'\" '))
if not jsonPath.is_file() or jsonPath.suffix != '.json':
    if not args.noConfirm:
        input("json is not a valid path to a json file")
    exit()

outputPath = (
    filePath.parent.joinpath(args.out.strip('\'\" '))
    if args.out is not None
    else filePath.parent.joinpath(
        filePath.stem
        + '_export'
        + ('.ipynb' if args.ipynb else ('.html' if args.html else '.md'))
    )
)

print("Reading target file ...")
fileContent = None
with filePath.open('rt', encoding='utf-8') as f:
    fileContent = f.read()

print("Parsing macro json file ...")
macroDict = dict()
with jsonPath.open('rt', encoding='utf-8') as f:
    for line in f:
        if line.startswith('    \"'):
            matchObj = tuple(m.replace(r'\\', '\\')
                             for m in re.match(
                                 r'\s+"(\\\\.+?)":\s*"(.+?)",?\s*$',
                                 line).groups()
                             )
            paraCount = max(int(i)
                            for i in [0, ] + re.findall(r'#(\d+)',
                                                        matchObj[1]))
            macroDict[matchObj[0]] = (matchObj[1], paraCount)
macroList = tuple(macroDict.keys())
for cmd in macroList:
    macroDict[cmd] = macroDict[cmd] \
        + (list(m for m in macroList if m in macroDict[cmd][0]), )
    # content, paraCount, [depKeys]

# do topo sort on macros

topoSortMarkDict = dict()
topoSortOrdering = list()


def topoSortVisit(macroName):
    if macroName in topoSortMarkDict:
        if not topoSortMarkDict[macroName]:
            raise ValueError("Macro " + macroName
                             + " has recursive dependency")
        else:
            return
    topoSortMarkDict[macroName] = False
    for depKey in macroDict[macroName][2]:
        topoSortVisit(depKey)
    topoSortMarkDict[macroName] = True
    topoSortOrdering.append(macroName)


for m in macroDict.keys():
    if not topoSortMarkDict.get(m, False):
        topoSortVisit(m)

print("Processing ...")
for key in topoSortOrdering[::-1]:
    cmdInfo = macroDict[key]
    if key not in fileContent:
        continue
    if cmdInfo[1] == 0:
        fileContent = re.sub(key.replace('\\', r'\\') + r'(?=\b|[^a-zA-Z])',
                             cmdInfo[0].replace('\\', r'\\'),
                             fileContent)
    else:
        keyLen = len(key)
        keyIdxList = tuple(match.start()
                           for match
                           in re.finditer(key.replace('\\', r'\\')
                                          + r'(?=\b|[^a-zA-Z])',
                                          fileContent))[::-1]
        for startIdx in keyIdxList:
            replacementCmd = cmdInfo[0]
            paraDict = dict()
            startPos = startIdx + keyLen
            endPos = 0
            for i in range(1, cmdInfo[1] + 1):
                endPos = findBracket(fileContent, startPos)
                paraDict[i] = fileContent[startPos + 1:endPos]
                startPos = endPos + 1
            for i in range(cmdInfo[1], 0, -1):
                replacementCmd = replacementCmd.replace(f'#{i}', paraDict[i])
            fileContent = fileContent[:startIdx] \
                + replacementCmd \
                + fileContent[endPos + 1:]

if args.webtex:
    fileContent = re.sub(r'\n*\$\$([^$]+)\$\$\n*',
                         lambda mObj: ('\n![Display: "'
                                       + re.sub(r'(\[|\])',
                                                r'\\\1',
                                                mObj.group(1))
                                       + '"]('
                                       + args.webLinkDisplay
                                       + urlencode({'': mObj.group(1)})[1:]
                                       + ')\n'),
                         fileContent)
    fileContent = re.sub(r'(?<!\$)\$([^$]+)\$(?!\$)',
                         lambda mObj: (r'![Inline: "'
                                       + re.sub(r'(\[|\])',
                                                r'\\\1',
                                                mObj.group(1))
                                       + '"]('
                                       + args.webLinkInline
                                       + urlencode({'': mObj.group(1)})[1:]
                                       + r')'),
                         fileContent)

print(f"Writing result {'with pandoc' if args.ipynb or args.html else ''}...")
if outputPath.is_file():
    print(f"{str(outputPath)} already exists!")
    if not args.noConfirm:
        input("Press Enter to overwrite file\n")
    print("Overwriting ...")
if args.ipynb:
    print("To ipynb, Pandoc return code: ",
          subprocess.run(('pandoc',
                          '--standalone',
                          '-f', 'markdown',
                          '-t', 'ipynb',
                          '-o', str(outputPath)),
                         input=fileContent,
                         shell=True,
                         encoding='utf-8').returncode)
elif args.html:
    fileSplit = fileContent.split('\n', maxsplit=1)
    fileTitle = fileSplit[0].replace('#', '', 1).strip()
    fileTitleTag = fileTitle.lower().replace(' ', '-')
    for c in '!"#$%&\'()*+,./:;<=>?@[\\]^`{|}~':
        fileTitleTag = fileTitleTag.replace(c, '')
    fileContent = fileSplit[1].lstrip().replace(f"#{fileTitleTag}",
                                                "#title-block-header")
    targetInsertLoc = list(findBracket(fileContent,
                                       matchObj.start(1),
                                       '()') + 1
                           for matchObj
                           in re.finditer(r'\[.+\](\(https?)', fileContent))
    fileContent = '{target="_blank"}'.join(fileContent[idxPair[0]:idxPair[1]]
                                           for idxPair
                                           in zip([None] + targetInsertLoc,
                                                  targetInsertLoc + [None]))
    print("To HTML, Pandoc return code: ",
          subprocess.run(('pandoc',
                          '--standalone',
                          '-f', 'markdown+gfm_auto_identifiers',
                          '-t', 'html5',
                          '-o', str(outputPath),
                          '--mathml',
                          f'--metadata=title:{fileTitle}'),
                         input=fileContent,
                         shell=True,
                         encoding='utf-8').returncode)
else:
    with outputPath.open('wt', encoding='UTF-8') as f:
        print(fileContent, file=f)
