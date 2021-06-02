import re
import argparse
import pathlib as path
from sys import stdout as stdout

parser = argparse.ArgumentParser()
parser.add_argument('--tex', type=str, help="Path to target tex file")
parser.add_argument('--bib', type=str, nargs='*',
                    help="Path to target tex file")
parser.add_argument('--out', type=str,
                    help="Path to output bib file. "
                    "Default to bib in tex path")
args = parser.parse_args()

texPath = path.Path(args.tex
                    if args.tex is not None
                    else input("Enter path to target .tex file:\n"
                               ).strip('\'\" '))
if not texPath.is_file():
    input(f"\"{str(texPath)}\" is not a valid path")
    exit()
usedBib = []
for bibPath in args.bib:
    bibPath = path.Path(bibPath.strip('\'\" '))
    if bibPath.is_file() and bibPath.suffix == '.bib':
        usedBib.append(bibPath)
    else:
        print(f"\"{str(bibPath)}\" is not a valid path to a bib file. "
              "Disposed. ")
outputBibPath = path.Path(args.out.strip('\'\" ')
                          if args.out is not None
                          else texPath.with_suffix('.bib'))
printToStdOut = False
if outputBibPath.is_file():
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
    print(f"parsing {str(bibPath)}")
    with bibPath.open('rt', encoding='utf-8') as bibFile:
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
                    citedKeyList.remove(lineMatchObj.group(1))
                    doCollecting = True
                    citedEntryList.append(line.rstrip())

if len(citedKeyList) != 0:
    print("some citekeys are not found in ref bib:")
    for citedKey in citedKeyList:
        print('\t', citedKey)
    input("enter to generate bib anyways")

print(f"writing to {str(outputBibPath) if not printToStdOut else 'stdout'}")
f = None
try:
    if printToStdOut:
        f = stdout
    else:
        f = outputBibPath.open('xt', encoding='UTF-8')
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
    for line in citedEntryList:
        print(line, file=f)
    if f is stdout:
        print("------------------ copy before this line ------------------")
    else:
        f.close()
input("Done")
