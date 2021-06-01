import re
import argparse
import pathlib as path
import subprocess
from sys import stdout as stdout

parser = argparse.ArgumentParser()
parser.add_argument('--tex', type=str, help="Path to target tex file")
parser.add_argument('--sty', type=str,
                    help="Path to reference sty file. "
                    "By default determined by kpsewhich")
parser.add_argument('--out', type=str,
                    help="Path to output cmd tex file. "
                    "Default to umm.tex in tex path")
args = parser.parse_args()

texPath = path.Path((args.tex
                     if args.tex is not None
                     else input("Enter path to target .tex file:\n")
                     ).strip('\'\" '))
if not texPath.is_file() or texPath.suffix != '.tex':
    input("tex is not a valid path")
    exit()
styPath = path.Path(args.sty.strip('\'\" ')
                    if args.sty is not None
                    else subprocess.run('kpsewhich usefulmathmacro.sty',
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
if outputPath.is_file():
    print(f"\"{str(outputPath)}\" already exists. "
          "Will write to stdout instead")
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

print("Parsing sty file")
outputBuffer = [
    r'\usepackage{amsmath}',
    r'\usepackage{amssymb}',
    r'\usepackage{amsthm}',
    r'\usepackage{xparse}',
]
doCollecting = False
with styPath.open('rt', encoding='UTF-8') as f:
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
    if printToStdOut:
        f = stdout
    else:
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
        print("-------------------- copy after this line --------------------")
    for line in outputBuffer:
        print(line, file=f)
    if f is stdout:
        print("------------------ copy before this line ------------------")
    else:
        f.close()
        print(f"File written at {str(outputPath)}")
input("Done")
