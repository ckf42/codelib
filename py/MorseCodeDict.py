from typing import Optional as _Optional

alphabet = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
    'Z': '--..'
}
number = {
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.'
}
punctuation = {
    '.': '.-.-.-', ',': '--..--', '?': '..--..', '\'': '.----.', '/': '-..-.',
    '(': '-.--.', ')': '-.--.-', ':': '---...', '=': '-...-', '+': '.-.-.',
    '-': '-....-', '"': '.-..-.', '@': '.--.-.'
}
prosign = {
    # voice procedure word
    '[OUT]': '.-.-.',
    '[WAIT]': '.-...',
    '[VERIFIED]': '...-.',
    '[INTERROGATIVE]': '..-.-',
    '[CORRECTION]': '........',
    '[BREAK]': '-...-',
    '[ATTENTION]': '-.-.-',
    '[OVER AND OUT]': '...-.-',
    '[SOS]': '...---...'
}
dictionary = {
    **alphabet,
    **number,
    **punctuation,
    **prosign
}
reverse_dict = {v: k for k, v in dictionary.items()}

def getCharCode(char: str) -> _Optional[str]:
    return dictionary.get(char.upper(), None)

def translateCode(signalStr: str) -> tuple[tuple[_Optional[str], ...], ...]:
    return tuple(tuple(getCharCode(c) for c in wd)
                 for wd in signalStr.split())

def __levenshtein(s1: str, s2: str) -> int:
    if len(s1) == 0 or len(s2) == 0:
        return len(s1) + len(s2)
    dpArr = list(i + 1 for i in range(len(s1)))
    for j in range(len(s2)):
        diagBlock = j
        for i in range(len(s1)):
            (diagBlock, dpArr[i]) = (
                    dpArr[i],
                    min(diagBlock + (1 if s1[i] != s2[j] else 0),
                        (j + 1 if i == 0 else dpArr[i - 1]) + 1,
                        dpArr[i] + 1))
    return dpArr[-1]

def closestMatches(signalStr: str, maxRes: int = 5) -> tuple[tuple[str, int], ...]:
    return tuple((code, d)
                 for d, code in sorted((__levenshtein(signalStr, sig), msg)
                                       for msg, sig in dictionary.items())[:maxRes])

