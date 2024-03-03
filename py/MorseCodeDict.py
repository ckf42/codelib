import typing as _tp

# numbers. Seem to be common across different languages
_number_dict = {
        '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
        '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
}

_dictionaries = {
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

_SUPPORTED_LANG = tuple(_dictionaries.keys())

class MorseDict:
    def __init__(self, lang: str = 'en'):
        assert lang in _SUPPORTED_LANG, f"Lang {lang} not supported"
        self.dict: dict[str, str] = _dictionaries[lang]
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

    def getCharCode(self, char: str) -> str | None:
        # query the code for char
        return self.dict.get(char.upper(), None)

    def translateToCode(self, charStr: str) -> tuple[tuple[str | None, ...], ...]:
        """Translate a string to morse code.

        Parameters
        ----------
        charStr: str
            A string containing the message

        Returns
        -------
        tuple[tuple[str | None, ...], ...]
            A tuple of word signals,
                in which each word signal is a tuple of letter signals string
                    representing the code for the letter
            If the letter is not recognized, the signal string is None instead
            The format is to make convertion to audio signal easier
                as letter sep and word sep have different lengths
        """
        return tuple(tuple(self.getCharCode(c) for c in wd)
                     for wd in charStr.split())

    def translateFromCode(self, signals: _tp.Iterable[str]) -> str:
        """Translate morse code signal to characters.

        Parameters
        ----------
        signals: Iterable[str]
            Iterable of signals.
            Assumed each str inside is a continuous piece
            (so representing a single letter or a prosign)
            Inputs like '.../---/...' should be splitted first

        Returns
        -------
        str
            A string form by concatenating all translated unit of given signal
            If a signal is not recognized, it is kept with square bracket surrounded
        """
        return ''.join(self.reverse_dict.get(seg, '[' + seg + ']')
                       for seg in signals)

    def closestMatches(
            self,
            signalStr: str,
            maxRes: int = 5) -> tuple[tuple[str, int], ...]:
        return tuple(
                (code, d)
                for d, code in sorted(
                    (self.__levenshtein(signalStr, sig), msg)
                    for msg, sig in self.dict.items())[:maxRes])

def _cli_():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
            'input',
            type=str,
            nargs=argparse.REMAINDER,
            help="The input string to process")
    parser.add_argument(
            '--decode', '-d',
            action='store_true',
            help="Decoding instead of encoding input")
    parser.add_argument(
            '--lang', '-l',
            type=str,
            choices=_SUPPORTED_LANG,
            default='en',
            help="The lang to use. Defaults to en")
    parser.add_argument(
            '--sep',
            type=str,
            default='/',
            help="The seperator for signal. Defaults to /")
    args, remainder = parser.parse_known_args()  # in case input starts with double dashes
    args.input = ' '.join(remainder + args.input)
    md = MorseDict(args.lang)
    if args.decode:
        print(md.translateFromCode(args.input.split(args.sep)))
    else:
        print(args.sep.join(args.sep.join(wordSig)
                            for wordSig in md.translateToCode(args.input)))

if __name__ == '__main__':
    _cli_()

