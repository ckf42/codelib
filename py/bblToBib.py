import re
import argparse
import os.path as path

parser = argparse.ArgumentParser()
parser.add_argument('--bbl', type=str, help="Path to generated bbl file")
parser.add_argument('--ref', type=str, help="Path to reference bib file")
parser.add_argument('--out', type=str, help="Path to output bib file")
args = parser.parse_args()

bblPath = (args.bbl
           if args.bbl is not None
           else input("Enter path to generated .bbl file:\n")).strip('\'\" ')
if not path.isfile(bblPath) or path.splitext(bblPath)[1] != '.bbl':
    print("not valid path")
    exit()
refBibPath = (args.ref
              if args.ref is not None
              else input("Enter path to global bib db:\n")).strip('\'\" ')
if not path.isfile(refBibPath) or path.splitext(refBibPath)[1] != '.bib':
    print("not valid path")
    exit()
outputBibPath = (args.out
                 if args.out is not None
                 else path.join(path.dirname(bblPath),
                                path.splitext(bblPath)[0] + '.bib'))
if path.isfile(outputBibPath):
    print(f"\"{outputBibPath}\" already exists. \n"
          "Please delete the file first before generating a new one")

print("parsing bbl file")
citedKeyList = []
with open(bblPath, 'rt', encoding='UTF-8') as bblFile:
    for line in bblFile:
        line = line.strip()
        if line.startswith(r'\entry'):
            citedKeyList.append(re.split('{|}', line, maxsplit=2)[1])

print("parsing reference bib file")
citedEntryList = []
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
            lineMatchObj = re.match('@[a-zA-Z]+\{(\w+),', line)
            if lineMatchObj is not None \
                    and lineMatchObj.group(1) in citedKeyList:
                doCollecting = True
                citedEntryList.append(line.rstrip())

print(f"writing to {outputBibPath}")
try:
    with open(outputBibPath, 'xt', encoding='UTF-8') as outputFile:
        for line in citedEntryList:
            print(line, file=outputFile)
    print("Done")
except FileExistsError:
    print("ERROR\n"
          f"\"{outputBibPath}\" already exists. \n"
          "Please delete the file first before generating a new one")
