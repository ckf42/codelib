import string
import pathlib
from typing import Iterable, Optional, Callable


def rot13(s: str, n: int = 13) -> str:
    """
    Rot13 the given string. 
    ----
    Parameter:
    s: str. The given string.

    m: int. The offset. a |-> a + offset. Defaults to 13.
    ----
    Return:
    A string. The rotated string
    ----
    Example:
    >>> hx.rot13('abc')
    'nop'
    >>> hx.rot13('abc', n=14)
    'opq'
    """
    ls = string.ascii_lowercase
    us = string.ascii_uppercase
    return s.translate(str.maketrans(ls + us,
                                     ls[n:] + ls[:n] + us[n:] + us[:n]))


def caeserBruteForce(s: str) -> list[str]:
    """
    Enumerate all possible results of Caeser cipher
    ----
    Parameter:
    s: str. The input string.
    ----
    Return:
    A list containing all 25 possible rotation of Caeser cipher
    ----
    Example:
    >>> hx.caeserBruteForce('abcd')
    ['abcd',
     'bcde',
     ...,
     'yzab',
     'zabc']
    """
    return [rot13(s, i) for i in range(26)]


def lenIndices(it: Iterable, toReverse: bool = False) -> range:
    """
    Get the range of len of an iterable
    ----
    Parameter:
    it: iterable that has len
    ----
    Return:
    A range object for enumerating the indices of it
    ----
    Example:
    >>> [i for i in hx.lenIndices('abc')]
    [0, 1, 2]
    >>> [i for i in hx.lenIndices('abc', toReverse=True)]
    [2, 1, 0]
    """
    if toReverse:
        return range(len(it) - 1, -1, -1)
    else:
        return range(len(it))


def toCharFreq(s: str, alphaOnly: bool = True) -> dict[str, float]:
    """
    Get the character frequencies
    ----
    Parameter:
    s: str. The input string to analyze

    alphaOnly: bool. Count only the letters in the statistics. Defaults to True
    ----
    Return:
    A dictionary containing the frequencies, in the form of char: freq
    Frequencies are normalized so that they sum to 1
    ----
    Example:
    >>> hx.toCharFreq('abcde12345')
    {'a': 0.1, 'b': 0.1, 'c': 0.1, 'd': 0.1, 'e': 0.1, '1': 0.1, '2': 0.1, '3': 0.1, '4': 0.1, '5': 0.1}
    >>> hx.toCharFreq('abcde12345', alphaOnly=True)
    {'a': 0.2, 'b': 0.2, 'c': 0.2, 'd': 0.2, 'e': 0.2}
    """
    freqDict = {}
    sList = [c.lower() for c in s if (not alphaOnly or c.isalpha())]
    for c in sList:
        freqDict[c] = freqDict.get(c, 0) + 1
    totalCharCount = sum(freqDict.values())
    return {c: f / totalCharCount for c, f in freqDict.items()}


def distToEnglishText(charDistriDict: dict) -> float:
    """
    Compute the distance of character frequency to the English text frequency
    ----
    Parameter:
    charDistriDict: a dictionary that contains the frequency,
                    in the form of char: freq. Frequencies are assumed to be
                    normalized, and letters are in lower case
    ----
    Return:
    The L1 distance to the reference English text letter frequency
    ----
    Example:
    >>> hx.distToEnglishText({'a': 0.2, 'b': 0.2, 'c': 0.2, 'd': 0.2, 'e': 0.2})
    1.4267346121566844
    >>> hx.distToEnglishText({'a': 0.1, 'b': 0.1, 'c': 0.1, 'd': 0.1, 'e': 0.1})
    0.9671256095621028
    """
    engDist = {
        'e': 21912, 't': 16587, 'a': 14810, 'o': 14003, 'i': 13318,
        'n': 12666, 's': 11450, 'r': 10977, 'h': 10795, 'd': 7874,
        'l': 7253, 'u': 5246, 'c': 4943, 'm': 4761, 'f': 4200,
        'y': 3853, 'w': 3819, 'g': 3693, 'p': 3316, 'b': 2715,
        'v': 2019, 'k': 1257, 'x': 315, 'q': 205, 'j': 188,
        'z': 128
    }
    engDistSum = 182303  # sum(engDist.values())
    return sum(abs(engDist[c] / engDistSum - charDistriDict.get(c, 0))
               for c in string.ascii_lowercase)


def readTextFile(filePath: str, enc: str = 'utf-8') -> list[str]:
    """
    Get the content of a file
    ----
    Parameter:
    filePath: str. The path of the file. Assume to exist and readable

    enc: str. The encoding used for the file. Defaults to UTF-8
    ----
    Return:
    A list of strings. The content of the target file read in text mode.
    Each item is a line
    """
    returnLst = []
    with pathlib.Path(filePath).expanduser().resolve(strict=True)\
            .open('rt', encoding=enc) as f:
        returnLst = f.readlines()
    return returnLst


def splitString(s: str, unitLen: int = 8, strict: bool = True) -> list[str]:
    """
    Split a string into chunks
    ----
    Parameter:
    s: str. The target string

    unitLen: int. The length of a chunk. Defaults to 8

    strict: bool. Decide whether to allow the last block being half-filled.
            If True, length of input string must be integer multiple of chunk
            length. Defaults to True
    ----
    Return:
    A list of strings as the chunks of the input string
    ----
    Example:
    >>> hx.splitString('1234567812345678')
    ['12345678', '12345678']
    >>> hx.splitString('1234567812345678', unitLen=4)
    ['1234', '5678', '1234', '5678']
    >>> hx.splitString('123456781234', strict=False)
    ['12345678', '1234']
    """
    assert unitLen > 0, "unitLen must be positive"
    if strict:
        assert len(s) % unitLen == 0,\
            f"Length of s ({len(s)}) is not a integer multiple "\
            f"of unitLen ({unitLen})"
    return [s[i:i + unitLen] for i in range(0, len(s), unitLen)]


def toHexString(s: str, enc: str = 'utf-8', withPrefix: bool = False) -> str:
    """
    Convert a string to hex numbers
    ----
    Parameter:
    s: str. The target string

    enc: str. The encoding to encode the string into. Defaults to UTF-8
    ----
    Return:
    A string representing the hex encoding of the string. Starts with '0x'
    ----
    Example:
    >>> hx.toHexString('abc')
    '616263'
    >>> hx.toHexString('abc', withPrefix=True)
    '0x616263'
    """
    return ('0x' if withPrefix else '') + s.encode(enc).hex()


def hexToASCII(s: str, isBinary: bool = False) -> str:
    """
    Convert a hex string to ASCII characters
    ----
    Parameter:
    s: str. The input string of a hex number.
       May start with '0x' is isBinary is False, or '0b' if isBinary is True

    isBinary: bool. Whether the input is hex or 01-binary.
              If True, the input string must contain only '0' and '1'.
              Defaults to False
    ----
    Return:
    A string obtained by splitting the string. 
    ----
    Example:
    >>> hx.hexToASCII('616263')
    'abc'
    >>> hx.hexToASCII('0x616263')
    'abc'
    >>> hx.hexToASCII('0b011000010110001001100011', isBinary=True)
    'abc'
    """
    if len(s) > 2 and s[:2] == ('0b' if isBinary else '0x'):
        s = s[2:]
    return ''.join([chr(int(c, 2 if isBinary else 16))
                    for c in splitString(s, 8 if isBinary else 2)])


def alphaToNum(s: str) -> list:
    """
    Convert letters into orders in English alphabet
    ----
    Parameter:
    s: string. The target string
    ----
    Return:
    A list containing the indices of characters in the string
    (case insensitive, starts with a = 0) in the English alphabet,
    or the original characters if they are not English letters
    ----
    Example:
    >>> hx.alphaToNum('abc123')
    [0, 1, 2, '1', '2', '3']
    """
    return [(ord(c) - ord('a')
             if c.islower()
            else (ord(c) - ord('A')
                  if c.isupper()
                  else c))
            for c in s]

def hexByteStringToArr(hexByteStr: str,
                       unitByteLen: int = 4,
                       isBigEndian: bool = True,
                       isNum: bool = True):
    """
    Convert hex byte blocks back to an array
    ----
    Parameter:
    hexByteStr: str. Space-separated string.
                Each space-separated block is considered a byte

    unitByteLen: int. The length of a byte in terms of blocks. Defaults to 4

    inBigEndian: bool. Whether the string is recorded in big endian
                 (Most significant byte first)
                 Defaults to True

    isNum: bool. Whether the contents are integers.
           If True, will try to convert each block into hex integers.
           If False, the blocks are returned as hex string.
           Defaults to False
    ----
    Return:
    A list of integers or string, depending on isNum. 
    ----
    Example:
    >>> hx.hexByteStringToArr('61 62 63 64')
    [1633837924]
    >>> hx.hexByteStringToArr('61 62 63 64', unitByteLen=2)
    [24930, 25444]
    >>> hx.hexByteStringToArr('61 62 63 64', unitByteLen=2, isBigEndian=False)
    [25185, 25699]
    >>> hx.hexByteStringToArr('61 62 63 64', unitByteLen=2, isNum=False)
    ['6162', '6364']
    """
    assert unitByteLen > 0
    arr = hexByteStr.split()
    assert len(arr) % unitByteLen == 0
    arr = [arr[i: i + unitByteLen] for i in range(0, len(arr), unitByteLen)]
    if not isBigEndian:
        arr = [seg[::-1] for seg in arr]
    arr = [''.join(seg) for seg in arr]
    if isNum:
        return [int(seg, 16) for seg in arr]
    else:
        return arr

def combineFromEach(listOfIter: list[Iterable],
                    postMap: Optional[callable] = None):
    """
    Picks elements from a list and applies optional map
    ----
    Parameter:
    listOfIter: list of iterable. Should contain the objects to be combined
    
    postMap: None or callable. The map to be applied on each combination.
             Defaults to None (identity map)
    ----
    Return:
    A list of results of the post map of all combinations of elements
    in the list 
    ----
    Example:
    >>> combineFromEach([[1, 2], [3, 4], [5]])
    [[1, 3, 5], [1, 4, 5], [2, 3, 5], [2, 4, 5]]
    >>> combineFromEach([[1, 2], [3, 4], [5]], sum)
    [9, 10, 10, 11]
    """
    if postMap is not None:
        return [postMap(i) for i in combineFromEach(listOfIter)]
    elif len(listOfIter) == 1:
        return [[i] for i in listOfIter[0]]
    else:
        return [[firstItem] + tailComb
                for firstItem in listOfIter[0] 
                for tailComb in combineFromEach(listOfIter[1:])]

def vigenere_map(s: str,
                 keyStr: str,
                 doEncrypt: bool = True) -> str:
    """
    Maps the string under the Vigenere cipher
    ----
    Parameter:
    s: str. The string to be mapped. Non-alphabetic characters are ignored.
    
    keyStr: str. The key string. Assumed to contains only alphabetic characters
    
    doEncrypt: bool. If True, s is encrypted with keyStr, decrypted if False
               Defaults to True
    ----
    Return:
    The result of the Vigenere map as a str
    ----
    Example:
    >>> vigenere_map("this is a test string", "key")
    [[1, 3, 5], [1, 4, 5], [2, 3, 5], [2, 4, 5]]
    >>> vigenere_map("dlgc mq k xccx qdvgxk", "key", doEncrypt=False)
    [9, 10, 10, 11]
    """
    kptr = 0
    klen = len(keyStr)
    pStr = ''
    for c in s:
        if c.isalpha():
            pStr += rot13(c, (1 if doEncrypt else -1) * alphaToNum(keyStr[kptr])[0])
            kptr = (kptr + 1) % klen
        else:
            pStr += c
    return pStr

def vigenere_crack(
    cipherStr: str,
    minKeyLen: int = 3,
    maxKeyLen: int = 10,
    takeTopCount: int = 5,
    groundTruth: str = '',
    freqDistFunc: Callable[dict, float] = distToEnglishText
    ) -> list[tuple[str, str, float]]:
    """
    Tries to crack the Vigenere cipher with frequency attack
    ----
    Parameter:
    cipherStr: str. The cipher text. Non-alphabetic characters are ignored
    
    minKeyLen: int. The minimal key length to be tested.
               Defaults to 3
    
    maxKeyLen: int. The maximal key length to be tested.
               Required to be at least 4 times of the length of cipherStr 
               (ignoring non-alphabetic characters)
               Defaults to 10

    takeTopCount: int. The number of choice to consider for each letter in the key
                  Defaults to 5
    
    groundTruth: str. Known parts of the string.Non-alphabetic characters 
                 are ignored
                 Will be truncated or padded with spaces if length does 
                 not match
                 Defaults to empty string (no known ground truth)
    
    freqDistFunc: callable. The function to get the character distribution distance.
                  Should take a dict and return a float representing the distance 
                  to reference character distribution
                  Defaults to distToEnglishText
    ----
    Return:
    A list of tuples that contains 3 elements:
        the possible key: str
        the possible plaintext from the key above: str
        the distance to the standard character distribution: float
    The list is sorted by the distance in increasing order
    ----
    Example:
    >>> vigenere_crack(vigenere_map("this is a test string", "key"), 3, 3)
    [
        ('kec', 'thes io a tast otreng', 0.6299157414401557),
        ('zeo', 'ehsd ic l todt cersyg', 0.6835626918468961),
        ('zec', 'ehed io l tadt oereyg', 0.7046858962341623),
        <truncated>
        ('key', 'this is a test string', 0.9175545173500743),
        <truncated>
    # (125 items in total)
    >>> vigenere_crack(vigenere_map("this is a test string", "key"), 3, 3, groundTruth="t is")
    [
        ('kiy', 'tdis es a pesp stninc', 0.8774170732565146),
        ('kty', 'tsis ts a eese stcinr', 0.8987442044611574),
        ('key', 'this is a test string', 0.9175545173500743),
        ('kxy', 'tois ps a aesa styinn', 0.9309291480150536),
        ('kry', 'tuis vs a gesg steint', 0.9554991028188043)
    ]
    """
    if len(groundTruth) > len(cipherStr):
        groundTruth = groundTruth[:len(cipherStr)]
    elif len(groundTruth) < len(cipherStr):
        groundTruth += ' ' * (len(cipherStr) - len(groundTruth))
    pureCipherIdx = [idx 
                     for (idx, c) in enumerate(cipherStr) 
                     if c.isalpha()]
    cipherLen = len(pureCipherIdx)
    if maxKeyLen > cipherLen // 4:
        raise ValueError(f'Cipher is too short ({cipherLen}) '
                         f'for maximal key length ({maxKeyLen}).')
    resultList = []
    for proposedKeyLen in range(minKeyLen, maxKeyLen + 1):
        strBuckets = [
            ''.join([cipherStr[pureCipherIdx[c]]
                     for c in range(charOffset, 
                                    cipherLen, 
                                    proposedKeyLen)])
            for charOffset in range(0, proposedKeyLen)
        ]
        gtBuckets = [
            ''.join([groundTruth[pureCipherIdx[c]]
                     for c in range(charOffset, 
                                    cipherLen, 
                                    proposedKeyLen)])
            for charOffset in range(0, proposedKeyLen)
        ]
        freqBuckets = [
            [
                (26 - idx, freqDistFunc(toCharFreq(guessText)))
                for (idx, guessText) in enumerate(caeserBruteForce(cipherFrag))
                if all([
                    not g.isalpha() or c.lower() == g.lower()
                    for (c, g) in zip(guessText, gtFrag)
                ])
            ]
            for (cipherFrag, gtFrag) in zip(strBuckets, gtBuckets)
        ]
        freqOrder = [
            [
                fb[idx]
                for idx in sorted(lenIndices(fb), 
                                  key=lambda x: fb[x][1])[:takeTopCount]
            ]
            for fb in freqBuckets
        ]
        possibleKeys = combineFromEach([
            [
                chr(fb[idx][0] + ord('a'))
                for (idx, val) in enumerate(fb)
                if val in fo
            ]
            for (fb, fo) in zip(freqBuckets, freqOrder)
        ], lambda x: ''.join(x))
        resultList.extend([
            (
                k, 
                (p := vigenere_map(cipherStr, k, False)),
                freqDistFunc(toCharFreq(p))
            )
            for k in possibleKeys
        ])
    return sorted(resultList, key=lambda x: x[2])
        
    