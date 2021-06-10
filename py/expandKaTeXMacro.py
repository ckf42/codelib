import argparse
import re
import pathlib as path
from personalPylib import findMatchBrackets as findMatchBrackets

filePath = r"D:\Acer\Documents\sync-work\progress.md"
jsonPath = r"D:\Acer\Documents\sync-work\umm_KaTeX_compatible.json"

fileContent = None
with open(filePath, 'rt') as f:
    fileContent = f.read()
bracketIdx = {
    match[1]: match[2]
    for match in findMatchBrackets(fileContent, '{}')
}

macroDict = dict()
with open(jsonPath, 'rt') as f:
    for line in f:
        if line.startswith('    \"'):
            matchObj = re.match(r'\s+"(\\\\.+?)":\s*"(.+?)",?\s*$',
                                line).groups()
            matchObj = (matchObj[0], matchObj[1].replace(r'\\', '\\'))
            paraCount = max(int(i)
                            for i in [0, ] + re.findall(r'#(\d+)',
                                                        matchObj[1]))
            macroDict[matchObj[0]] = (matchObj[1], paraCount)

# how to keep track of location to modify?
for key, cmdInfo in macroDict.items():
    if cmdInfo[1] == 0:
        fileContent = fileContent.replace(key, cmdInfo[0])
    else:
        keyLen = len(key) - 1
        keyIdx = tuple(match.start()
                       for match in re.finditer(key + '\\W', fileContent))
        for cmdIdx in keyIdx:
            paraDict = dict()
            paraOpenBracketIdx = cmdIdx + keyLen
            paraCloseBracketIdx = 0
            for paraIdx in range(1, cmdInfo[1] + 1):
                paraCloseBracketIdx = bracketIdx[paraOpenBracketIdx] + 1
                paraDict[paraIdx] \
                    = fileContent[paraOpenBracketIdx:paraCloseBracketIdx]
                paraOpenBracketIdx = paraCloseBracketIdx
            replacedCmd = cmdInfo[0]
            for paraIdx in range(cmdInfo[1], 0, -1):
                replacedCmd.replace(f'#{paraIdx}',
                                    paraDict[paraIdx])
            fileContent = fileContent[:cmdIdx] \
                + replacedCmd \
                + fileContent[paraCloseBracketIdx:]
