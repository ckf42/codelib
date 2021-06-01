import re

filePath = r"C:\Users\akfchan\Desktop\sync-work\kepkaPaperNote.tex"

fileContent = []
citedKeys = set()
usedBib = []

with open(filePath, 'rt') as f:
    for line in f:
        fileContent.append(line)
        if line.lstrip().startswith(r'\\addbibresource{'):
            usedBib.append(
                re.match(r'\\addbibresource\{(.+?\.bib)\}', line).group(1))
        for match in re.findall(r'\\[a-zA-Z]*cite[a-zA-Z]*(?:\[.*?\])*?\{([a-zA-Z0-9, ]+)\}', line):
            citedKeys.update(match.split(', '))
