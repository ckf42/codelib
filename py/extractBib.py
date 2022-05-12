import re
import argparse
import pathlib as path
from sys import stdout
from shutil import copy2


parser = argparse.ArgumentParser()
parser.add_argument('--tex', type=str, help="Path to target tex file")
parser.add_argument('--bib', type=str, nargs='*',
                    help="Path to reference bib file. "
                    "Can omit if added in tex with addbibresource command")
parser.add_argument('--out', type=str,
                    help="Path to output bib file. "
                    "Put \"stdout\" to output to stdout. "
                    "Default to bib in tex path")
parser.add_argument('--forceout',
                    action='store_true',
                    help="Overwrite output bib file if it already exists. "
                    "Will truncate the existing file. "
                    "Ignored if output to stdout")
parser.add_argument('--frag', action='store_true',
                    help="Output as filecontents fragment. "
                    "Implies output to stdout")
parser.add_argument('--inject', action='store_true',
                    help="Inject addbibresource command in file. "
                    "Command will replace the first addbibresource command, "
                    "and all other addbibresource command will be removed. "
                    "Path will be absolute if out is given, "
                    "relative otherwise. "
                    "Ignored if output to stdout")
parser.add_argument('--nobackup',
                    action='store_true',
                    help="Do not save a backup copy. "
                    "Ignored if --inject is not present")
args = parser.parse_args()

ignoredBibLineHead = ('%', 'readstatus', 'groups', 'abstract', 'comment')

texPath = path.Path(args.tex
                    if args.tex is not None
                    else input("Enter path to target .tex file:\n"
                               ).strip('\'\" '))
if not texPath.is_file():
    input(f"\"{str(texPath)}\" is not a valid path")
    exit()
usedBib = []
for bibPath in (args.bib if args.bib is not None else tuple()):
    bibPath = path.Path(bibPath.strip('\'\" '))
    if bibPath.is_file() and bibPath.suffix == '.bib':
        usedBib.append(bibPath)
    else:
        print(f"\"{str(bibPath)}\" is not a valid path to a bib file. "
              "Disposed. ")
printToStdOut = False
if args.frag:
    args.out = ''
    printToStdOut = True
isOutGivenByUser = args.out is not None
outputBibPath = path.Path(args.out.strip('\'\" ')
                          if isOutGivenByUser
                          else texPath.with_suffix('.bib'))
if str(outputBibPath).lower() == 'stdout':
    printToStdOut = True
elif outputBibPath.is_file() and not args.forceout:
    input(f"\"{str(outputBibPath)}\" already exists. \n"
          "Will print to stdout instead")
    printToStdOut = True

print("reading tex file")
fileContent = []
citedKeyList = set()
with texPath.open('rt', encoding='utf-8') as f:
    for line in f:
        fileContent.append(line)
        if line.lstrip().startswith(r'\addbibresource{'):
            usedBib.append(re.match(r'\\addbibresource\{(.+?\.bib)\}',
                                    line).group(1))
        for match in re.findall(r'\\[a-zA-Z]*cite[a-zA-Z]*'
                                r'(?:\[.*?\])*?\{([a-zA-Z0-9, ]+)\}',
                                line):
            citedKeyList.update(match.split(', '))

print("parsing bib files")
basePath = texPath.parent
citedEntryList = [r'% Encoding: UTF-8']
doCollecting = False
for bib in usedBib:
    bibPath = basePath / bib
    if not bibPath.is_file():
        print(f"\"{bibPath}\" is not a valid file")
        continue
    print(f"parsing {str(bibPath)}")
    with bibPath.open('rt', encoding='utf-8') as bibFile:
        citeEntry = list()
        citeEntryName = list()
        for line in bibFile:
            linelstrip = line.lstrip()
            if linelstrip == '' or linelstrip.startswith(ignoredBibLineHead):
                continue
            if doCollecting:
                citeEntry.append(line.rstrip())
                if (matchObj := re.match(r'ids\s*=\s*\{(\w+)\}',
                                         linelstrip)) is not None:
                    citeEntryName.append(matchObj.group(1))
                elif line[0] == '}':
                    doCollecting = False
                    if any((entryName in citedKeyList)
                            for entryName in citeEntryName):
                        citedEntryList.extend(citeEntry)
                        for entryName in citeEntryName:
                            if entryName in citedKeyList:
                                citedKeyList.remove(entryName)
            else:
                if (matchObj := re.match(r'@[a-zA-Z]+\{(\w+),',
                                         linelstrip)) is not None:
                    doCollecting = True
                    citeEntry = [line.rstrip()]
                    citeEntryName = [matchObj.group(1)]

if len(citedKeyList) != 0:
    print("some citekeys are not found in ref bib:")
    for citedKey in citedKeyList:
        print('\t', citedKey)
    input("Press Enter to ignore and generate bib anyways")

print(f"writing to {str(outputBibPath) if not printToStdOut else 'stdout'}")
f = stdout
try:
    if not printToStdOut:
        f = outputBibPath.open('wt', encoding='UTF-8')
except FileExistsError:
    print(f"File \"{str(outputBibPath)}\" already exists. \n"
          "Please check if path is valid and delete the old file. \n"
          "Will fallback to stdout")
    f = stdout
except Exception as e:
    print("ERROR:\nUnknown error occurred", e, "Fallback to stdout")
    f = stdout
finally:
    if f is stdout:
        print("-------------------- copy after this line --------------------")
    if args.frag:
        print('\\begin{filecontents}'
              f'{{{str(texPath.with_suffix(".bib").name)}}}')
    for line in citedEntryList:
        if args.frag:
            print('    ', end='')
        print(line, file=f)
    if args.frag:
        print('\\end{filecontents}')
    if f is stdout:
        print("------------------ copy before this line ------------------")
    else:
        f.close()

if args.inject and not printToStdOut:
    if not args.nobackup:
        baseBackupName = texPath.stem + '_bibbackup'
        backupName = baseBackupName
        backupCounter = 0
        while (texPath.parent / (backupName + texPath.suffix)).exists():
            backupCounter += 1
            backupName = baseBackupName + f"({backupCounter})"
        copy2(texPath, texPath.parent / (backupName + texPath.suffix))
        print(f"Backup saved as {backupName + texPath.suffix}")
    addResLineIdx = sorted([idx
                            for (idx, line) in enumerate(fileContent)
                            if line.lstrip().startswith('\\addbibresource')],
                           reverse=True)
    firstResLineIdx = addResLineIdx.pop()
    fileContent = [line.rstrip('\n')
                   for (idx, line) in enumerate(fileContent)
                   if idx not in addResLineIdx]
    fileContent[firstResLineIdx] = re.sub(
        r'(?<=\\addbibresource\{)(.+?\.bib)(?=\})',
        outputBibPath.as_posix() if isOutGivenByUser else outputBibPath.name,
        fileContent[firstResLineIdx]
    )
    with texPath.open('w', encoding='utf-8') as f:
        for line in fileContent:
            print(line, file=f)

input("Done")
