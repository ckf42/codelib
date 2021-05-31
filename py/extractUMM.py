import re
import argparse
import os.path as path
from sys import stdout as stdout

parser = argparse.ArgumentParser()
parser.add_argument('--tex', type=str, help="Path to target tex file")
parser.add_argument('--sty', type=str, help="Path to reference sty file")
parser.add_argument('--out', type=str,
                    help="Path to output cmd tex file. "
                    "Default to umm.tex in tex path")
args = parser.parse_args()

texPath = (args.tex
           if args.tex is not None
           else input("Enter path to target .tex file:\n")).strip('\'\" ')
if not path.isfile(texPath) or path.splitext(texPath)[1] != '.tex':
    input("tex is not a valid path")
    exit()
styPath = (args.sty
           if args.sty is not None
           else input("Enter path to ref sty file:\n")).strip('\'\" ')
if not path.isfile(styPath) or path.splitext(styPath)[1] != '.sty':
    input("ref sty is not a valid path")
    exit()
outputPath = (args.out.strip('\'\" ')
              if args.out is not None
              else path.join(path.dirname(texPath), 'umm.tex'))
printToStdOut = False
if path.isfile(outputPath):
    print(f"\"{outputPath}\" already exists. Will write to stdout instead")
    printToStdOut = True

print("Parsing tex file")
usedCmd = set()
with open(texPath, 'rt', encoding='UTF-8') as f:
    for line in f:
        for match in (re.findall(r'(\\[a-zA-Z]+?)\b', line), ):
            if len(match) != 0:
                usedCmd.update(match)
        for match in (re.match(r'\\begin\{([a-zA-Z]+?)\}', line.lstrip()), ):
            if match is not None:
                usedCmd.update(match.groups())

print("Parsing sty file")
outputBuffer = [
    r'\usepackage{amsmath}',
    r'\usepackage{amssymb}',
    r'\usepackage{amsthm}',
    r'\usepackage{xparse}',
]
doCollecting = False
with open(styPath, 'rt', encoding='UTF-8') as f:
    for line in f:
        line = line.rstrip()
        if doCollecting:
            outputBuffer.append(line)
            if len(line) > 0 and line[0] == '}':
                doCollecting = False
        else:
            match = re.match(r'\\ProvideDocument[a-zA-Z]+\{([^}]+?)\}', line)
            if match is not None and match.group(1) in usedCmd:
                doCollecting = True
                outputBuffer.append(line)

f = None
try:
    f = open(outputPath, 'xt', encoding='UTF-8')
except FileExistsError:
    print(f"\"{outputPath}\" already exists. \n"
          "Fallback to stdout")
    f = stdout
except Exception as e:
    print("ERROR:\nUnknown error occurred", e, "Fallback to stdout")
    f = stdout
finally:
    if f is stdout:
        print("-------------------- copy after this line --------------------")
    for line in outputBuffer:
        print(line, file=f)
    if f is stdout:
        print("------------------ copy before this line ------------------")
    else:
        f.close()
input("Done")
