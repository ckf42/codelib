# TODO parse bbl only

import re
import argparse
import os.path as path
from sys import stdout

parser = argparse.ArgumentParser()
parser.add_argument('--bbl', type=str, help="Path to generated bbl file")
inputArg = parser.add_mutually_exclusive_group("Input source")
inputArg.add_argument('--ref', type=str, help="Path to reference bib file")
inputArg.add_argument('--tex', type=str, help="Path to target tex file. "
                      "Only the first \\addbibresource command with no "
                      "option is processed")
parser.add_argument('--out', type=str,
                    help="Path to output bib file. "
                    "Default to bbl path but with bib extension")
parser.add_argument('--replace', action='store_true',
                    help="Also replace the ref path in tex file. "
                    "The absolute path is used. "
                    "Ignored if --ref is used or only prints to stdout")
args = parser.parse_args()

bblPath = (args.bbl
           if args.bbl is not None
           else input("Enter path to generated .bbl file:\n")).strip('\'\" ')
if not path.isfile(bblPath) or path.splitext(bblPath)[1] != '.bbl':
    input("bbl is not a valid path")
    exit()
if args.tex is not None:
    # get bib path from tex
    if not path.isfile(args.tex):
        input("ref tex is not a valid path")
        exit()
    with open(args.tex, 'rt') as texFile:
        for line in texFile:
            line = line.strip()
            if line.startswith(r'\addbibresource{'):
                args.ref = path.abspath(
                    path.join(path.dirname(args.tex, line[16:-1])))
                break
refBibPath = (args.ref
              if args.ref is not None
              else input("Enter path to global bib db:\n")).strip('\'\" ')
if not path.isfile(refBibPath) or path.splitext(refBibPath)[1] != '.bib':
    input("ref bib is not a valid path")
    exit()
outputBibPath = (args.out.strip('\'\" ')
                 if args.out is not None
                 else path.splitext(bblPath)[0] + '.bib')
printToStdOut = False
if path.isfile(outputBibPath):
    input(f"\"{outputBibPath}\" already exists. \n"
          "Will print to stdout instead")
    printToStdOut = True

print("parsing bbl file")
citedKeyList = []
with open(bblPath, 'rt', encoding='UTF-8') as bblFile:
    for line in bblFile:
        line = line.strip()
        if line.startswith(r'\entry'):
            citedKeyList.append(re.split('{|}', line, maxsplit=2)[1])

print("parsing reference bib file")
citedEntryList = [r'% Encoding: UTF-8']
doCollecting = False
with open(refBibPath, 'rt', encoding='UTF-8') as bibFile:
    for line in bibFile:
        linelstrip = line.lstrip()
        if linelstrip == '' \
                or linelstrip.startswith(('%', 'readstatus', 'groups')):
            continue
        if doCollecting:
            citedEntryList.append(line.rstrip())
            if line[0] == '}':
                doCollecting = False
        else:
            lineMatchObj = re.match(r'@[a-zA-Z]+\{(\w+),', line)
            if lineMatchObj is not None \
                    and lineMatchObj.group(1) in citedKeyList:
                doCollecting = True
                citedEntryList.append(line.rstrip())

print(f"writing to {outputBibPath if not printToStdOut else 'stdout'}")
f = None
try:
    if printToStdOut:
        f = stdout
    else:
        f = open(outputBibPath, 'xt', encoding='UTF-8')
except FileExistsError:
    print(f"File \"{outputBibPath}\" already exists. \n"
          "Please check if path is valid and delete the old file. \n"
          "Will fallback to stdout")
    f = stdout
except Exception as e:
    print("ERROR:\nUnknown error occurred", e, "Fallback to stdout")
    f = stdout
finally:
    if f is stdout:
        print("-------------------- copy after this line --------------------")
    for line in citedEntryList:
        print(line, file=f)
    if f is stdout:
        print("------------------ copy before this line ------------------")
    else:
        f.close()

if args.tex is not None and args.replace and not printToStdOut:
    fileContent = []
    with open(args.tex, 'rt') as f:
        for line in f:
            if line.startswith(r'\addbibresource{'):
                line = r'\addbibresource{' + args.out + '}'
            fileContent.append(line)
    with open(args.tex, 'r+t') as f:
        for line in fileContent:
            print(line, file=f)
input("Done")
