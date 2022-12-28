import re
import unicodedata as ud


# extract from shdl

def transformToAuthorStr(authorList: tuple[tuple[str, ...], ...]) -> str:
    # authorList assumed (given name, family name)
    return ', '.join(''.join((gNamePart
                              if len(gNamePart) <= 1 or not gNamePart.isalpha()
                              else (gNamePart[0] + '.'))
                             for gNamePart
                             in re.split(r'\b', authorNameTuple[0]))
                     + ' '
                     + authorNameTuple[1]
                     for authorNameTuple in authorList)


# list modified from https://gist.github.com/sebleier/554280
stopwordLst = (
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an',
    'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before',
    'being', 'below', 'between', 'both', 'but', 'by', 'can', 'did', 'do',
    'does', 'doing', 'don', 'down', 'during', 'each', 'few', 'for', 'from',
    'further', 'had', 'has', 'have', 'having', 'here', 'how', 'if', 'in',
    'into', 'is', 'just', 'more', 'most', 'no', 'nor', 'not', 'now', 'of',
    'off', 'on', 'once', 'only', 'or', 'other', 'out', 'over', 'own', 's',
    'same', 'should', 'so', 'some', 'such', 't', 'than', 'that', 'the', 'then',
    'there', 'these', 'this', 'those', 'through', 'to', 'too', 'under',
    'until', 'up', 'very', 'was', 'were', 'what', 'when', 'where', 'which',
    'while', 'who', 'whom', 'why', 'will', 'with',
)


# TODO better method?
def transformToTitle(s: str) -> str:
    wordList = re.split(r'( |-)\b', s)
    if len(wordList) <= 1:
        return s
    else:
        return (wordList[0]
                if wordList[0].isupper()
                else wordList[0].capitalize()) \
            + ''.join(
            map(lambda w: w.lower()
                if w.lower() in stopwordLst
                else (w if w.isupper() else w.capitalize()),
                wordList[1:])
        )


def sanitizeFilename(s: str) -> str:
    return ' '.join(ud.normalize(
        'NFKD',
        s
        .translate(str.maketrans({k: ' ' for k in '/<>:\"\\|?*'}))
        .translate(str.maketrans({
            '’': '\''
        }))  # unicode non Sm category replacement
    ).encode('ASCII', 'ignore').decode().split(None))


authorStr = input("Enter author list, separated by comma: \n")
titleStr = input("Enter title: \n")
abbAuthorStr = transformToAuthorStr(tuple(aName.split(" ")
                                          for aName in authorStr.split(', ')))
unsanitizedFilename = f"[{abbAuthorStr}]{transformToTitle(titleStr)}"
print(sanitizeFilename(unsanitizedFilename))
