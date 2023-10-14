from typing import Optional as _Optional

# numbers. Seem to be common across different languages
_number_dict = {
        '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
        '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
}

dictionary = {
    'en': {
        # alphabet
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
        'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
        'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
        'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
        'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
        'Z': '--..',
        # number
        **_number_dict,
        # punctuation 
        '.': '.-.-.-', ',': '--..--', '?': '..--..', '\'': '.----.', '/': '-..-.',
        '(': '-.--.', ')': '-.--.-', ':': '---...', '=': '-...-', '+': '.-.-.',
        '-': '-....-', '"': '.-..-.', '@': '.--.-.',
        # prosign, voice procedure word
        '[OUT]': '.-.-.',
        '[WAIT]': '.-...',
        '[VERIFIED]': '...-.',
        '[INTERROGATIVE]': '..-.-',
        '[CORRECTION]': '........',
        '[BREAK]': '-...-',
        '[ATTENTION]': '-.-.-',
        '[OVER AND OUT]': '...-.-',
        '[SOS]': '...---...',
    },
    'jp': {
        # kana
        '゛': '..',
        '゜': '..--.',
        'あ': '--.--', 'い': '.-', 'う': '..-', 'え': '-.---', 'お': '.-...',
        'か': '.-..', 'き': '-.-..', 'く': '...-', 'け': '-.--', 'こ': '----',
        'さ': '-.-.-', 'し': '--.-.', 'す': '---.-', 'せ': '.---.', 'そ': '---.',
        'た': '-.', 'ち': '..-.', 'つ': '.--.', 'て': '.-.--', 'と': '..-..',
        'な': '.-.', 'に': '-.-.', 'ぬ': '....', 'ね': '--.-', 'の': '..--',
        'は': '-...', 'ひ': '--..-', 'ふ': '--..', 'へ': '.', 'ほ': '-..',
        'ま': '-..-', 'み': '..-.-', 'む': '-', 'め': '-...-', 'も': '-..-.',
        'や': '.--', 'ゆ': '-..--', 'よ': '--',
        'ら': '...', 'り': '--.', 'る': '-.--.', 'れ': '---', 'ろ': '.-.-',
        'わ': '-.-', 'ゐ': '.-..-', 'ゑ': '.--..', 'を': '.---',
        'ん': '.-.-.',
        # symbols
        'ー': '.--.-', '、': '.-.-.-', '」': '.-.-..',
        '（': '-.--.-', '）': '.-..-.',
        # number
        **_number_dict,
        # prosign
        '[本文]': '-..---', '[訂正・終了]': '...-.',
    }
}

SUPPORTED_LANG = tuple(dictionary.keys())

class MorseDict:
    def __init__(self, lang: str = 'en'):
        assert lang in SUPPORTED_LANG, f"Lang {lang} not supported"
        self.dict: dict[str, str] = dictionary[lang]
        self.reverse_dict: dict[str, str] = {v: k for k, v in self.dict.items()}

    @staticmethod
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

    def getCharCode(self, char: str) -> _Optional[str]:
        return self.dict.get(char.upper(), None)

    def translateCode(self, signalStr: str) -> tuple[tuple[_Optional[str], ...], ...]:
        return tuple(tuple(self.getCharCode(c) for c in wd)
                     for wd in signalStr.split())


    def closestMatches(self,
                       signalStr: str, maxRes: int = 5) -> tuple[tuple[str, int], ...]:
        return tuple(
                (code, d)
                for d, code in sorted(
                    (self.__levenshtein(signalStr, sig), msg)
                    for msg, sig in self.dict.items())[:maxRes])

