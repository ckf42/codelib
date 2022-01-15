import string
import pathlib
from typing import Iterable


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
    Enumerate all possible results of Ceaser cipher
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
     'yzab']
    """
    return [rot13(s, i) for i in range(25)]


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

    unitLen: int. The length of a chunk. Defautls to 8

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
    A list containing the indices of chatacters in the string
    (case insensitive, starts with a = 1) in the English alphabet,
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
                 (Most significant bytr first)
                 Defaults to True

    isNum: bool. Whether the contents are integers.
           If True, will try to convereach block into hex integers.
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

