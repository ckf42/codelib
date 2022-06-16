import decimal as __decimal
import typing as __typing
from math import log1p, exp
from numbers import Number as __Number

if __name__ == '__main__':
    exit()


def viewList(lst: list,
             itemPerPage: int = 20,
             displayMethod: callable = print,
             showOrdinal: bool = False,
             useIndex: bool = False,
             headMessageStrFunc: callable
             = lambda lstLen: f"{lstLen} item(s) in total"):
    if headMessageStrFunc is not None:
        print(headMessageStrFunc(len(lst)))
    if itemPerPage <= 0 or len(lst) <= itemPerPage:
        # for item in lst: displayMethod(item)
        for i in range(len(lst)):
            if showOrdinal:
                print(f'#{i+1}:    ', end='')
            if useIndex:
                displayMethod(lst[i], i)
            else:
                displayMethod(lst[i])
        return None
    import msvcrt
    n = int((len(lst) + itemPerPage - 1) / itemPerPage)
    index = 0
    command = '.'
    while index < n:
        print(f"---- Page {index+1} / {n} ----")
        for itemIndex in range(index * itemPerPage,
                               min((index + 1) * itemPerPage,
                                   len(lst))):
            if showOrdinal:
                print(f"#{itemIndex+1}:    ", end='')
            # displayMethod(lst[itemIndex])
            if useIndex:
                displayMethod(lst[itemIndex], itemIndex)
            else:
                displayMethod(lst[itemIndex])
        if index == n - 1:
            print("---- End of list, forward to quit ----")
        print("[F]orward, "
              + ("[B]ackward, " if index != 0 else "")
              + "[J]ump or [Q]uit: ",
              end='', flush=True)
        command = '.'
        while len(command) != 1 or command not in 'fbqjhc':
            try:
                command = msvcrt.getche().decode('utf8').lower()
            except Exception:
                command = '.'
            if command == 'b' and index == 0:
                command = '.'
        print('')  # newline
        if command == 'q':  # quit
            return
        elif command == 'h':  # help
            print("Help Message")
            print("h    show this help message")
            print("f    go to next page")
            print("b    go to last page")
            print("j    jump to some page, or to some item")
            print("c    toggle ordinal number display")
            print("q    quit")
            input("Press [Enter] to quit this message")
        elif command in 'fb':  # next/previous page
            index += (1 if command == 'f' else -1)
        elif command == 'j':  # jump
            print(f"Total pages: {n}, "
                  f"total items: {len(lst)}, "
                  f"current page: {index+1}")
            isItem = False
            while not isinstance(command, int):
                command = input("Enter [page number], "
                                "i[item number] "
                                "or [q] to cancel: ")
                if len(command) == 0:
                    continue
                if command.lower() == 'q':
                    isItem = False
                    command = index + 1
                    break
                if command[0] == 'i':
                    isItem = True
                    command = command[1:]
                else:
                    isItem = False
                invalidNum = False
                try:
                    command = int(command)
                    if command <= 0 \
                            or command > (len(lst) if isItem else n):
                        invalidNum = True
                except Exception:
                    invalidNum = True
                if invalidNum:
                    print("Please enter a valid number. "
                          f"Total pages: {n}, total items: {len(lst)}")
                    command = '.'
            index = ((command - 1) // itemPerPage
                     if isItem else command - 1)
        elif command == 'c':  # toggle index
            showOrdinal = not showOrdinal


def genStr(charList: str, minLen: int, maxLen: int) -> str:
    """
    Generate a string from the given alphabet
    ---
    Parameter:
        charList:
            Type: str
            The string of alphabet characters
        minLen:
            Type: int
            The minimal length of the string to be generated
        maxLen:
            Type: int
            The maximal length of the string to be generated
    ---
    Return:
        Each yield generates a string consisting of letters in charList
    """
    # O(length+0.5*length) per yield
    for outputLen in range(max(minLen, 1), maxLen + 1):
        selectCharIdx = [0] * outputLen
        while selectCharIdx[outputLen - 1] < len(charList):
            s = ''
            for i in range(outputLen - 1, -1, -1):
                s += charList[selectCharIdx[i]]
            yield s
            selectCharIdx[0] += 1
            for i in range(outputLen - 1):
                if selectCharIdx[i] >= len(charList):
                    selectCharIdx[i] = 0
                    selectCharIdx[i + 1] += 1
                else:
                    break


def userConfirm(message: str,
                charYStr='y', charNStr='n',
                defaultChar=None,
                caseInsensitive=True) -> bool:
    s = ''
    if caseInsensitive:
        charYStr = charYStr.lower()
        charNStr = charNStr.lower()
        if defaultChar is not None:
            defaultChar = defaultChar.lower()
    while len(s) != 1 or s not in charYStr + charNStr:
        s = input(message)
        if caseInsensitive:
            s = s.lower()
        if defaultChar is not None and s == '':
            s = defaultChar
    return s in charYStr


def floydCycleDetect(f: __typing.Callable, x0) -> (int, int):
    """
    Find the length of the loop
    ---
    Parameter:
        f:
            Type: callable
            The callable to check for
            Must takes only one parameter
        x0:
            Type: Any
            The initial seed to look at
            Will be supplied to f
    ---
    Return:
        A tuple of 2 intgers (c, d) where
            c is the the number of iterations to enter the loop
            d is the length of the loop
    """
    tortoise = f(x0)
    hare = f(tortoise)
    while hare != tortoise:
        hare = f(f(hare))
        tortoise = f(tortoise)
    c = 1
    hare = f(hare)
    while hare != tortoise:
        c += 1
        hare = f(hare)
    d = 0
    tortoise = x0
    while hare != tortoise:
        d += 1
        hare = f(hare)
        tortoise = f(tortoise)
    return (c, d)


def strSimRatio(s1: str, s2: str, substrWeight: float = .6) -> float:
    l1, l2 = len(s1), len(s2)
    if l1 == 0 or l2 == 0:
        invLevRatio, substrRatio = 0, 1
    else:
        dp = [list(range(l2 + 1)), [0] * (l2 + 1)]
        ref = 0
        for i in range(l1):
            dp[1 - ref][0] = i + 1
            for j in range(l2):
                dp[1 - ref][j + 1] = (dp[ref][j]
                                      if s1[i] == s2[j]
                                      else 1 + min(dp[1 - ref][j],
                                                   dp[ref][j],
                                                   dp[ref][j + 1]))
            ref = 1 - ref
        invLevRatio = dp[ref][l2]
        dp = [[0] * (l1 + 1), [0] * (l1 + 1)]
        ref = 0
        for j in range(1, l2 + 1):
            dp[1 - ref][0] = 0
            for i in range(1, l1 + 1):
                dp[1 - ref][i] = (1 + dp[ref][i - 1]
                                  if s1[i - 1] == s2[j - 1]
                                  else max(dp[ref][i], dp[1 - ref][i - 1]))
            ref = 1 - ref
        substrRatio = dp[ref][l1]
        invLevRatio = 1 - invLevRatio / max(l1, l2)
        substrRatio = substrRatio / min(l1, l2)
    return substrWeight * substrRatio * (2 - substrRatio) \
        + (1 - substrWeight) * invLevRatio * invLevRatio


def inputPath(displayStr: str,
              forFile: bool = True,
              defaultPath: str = None) -> str:
    import os.path
    s = ''
    while not (os.path.isfile if forFile else os.path.isdir)(s):
        s = input(displayStr).strip('\'\" ')
        if len(s) == 0:
            s = defaultPath
    return s


def textColoring(text: str, color: str = "white") -> str:
    """
    Put ANSI color in string
    ---
    Parameter:
        text:
            Type: str
            The strings to be colored
        color:
            Type: str
            The target string
            Can be a 6-digit hex number as color code, or one of the following strings:
                'reset', 'none', 'black', 'red', 'green',
                'yellow', 'blue', 'magenta', 'cyan', 'white',
                'bright black', 'bright red', 'bright green',
                'bright yellow', 'bright blue', 'bright magenta',
                'bright cyan', 'bright white'
    ---
    Return:
        The same string, with ANSI color code surrounded
    """
    colorCode = {
        'reset': 0, 'none': 0, 'black': 30, 'red': 31, 'green': 32,
        'yellow': 33, 'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37,
        'bright black': 90, 'bright red': 91, 'bright green': 92,
        'bright yellow': 93, 'bright blue': 94, 'bright magenta': 95,
        'bright cyan': 96, 'bright white': 97,
    }
    color = color.lower().strip()
    try:
        rHex, gHex, bHex = \
            int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16)
        color = f'38;2;{rHex};{gHex};{bHex}'
    except ValueError:  # is string name
        color = colorCode.get(color, 0)
    return f'\x1b[{color}m{text}\x1b[0m'


def FareyApprox(x: float,
                tol: float = 1e-8,
                maxIter: int = 1000) -> (int, int):
    """
    Farey Approximatin of float number
    ---
    Parameter:
        x:
            Type: float
            The input
        tol:
            Type: float
            Default: 1e-8
            The numerical tolerance
        maxIter:
            Type: int
            Default: 1000
            The maximal iterations to run this algorithm
    ---
    Return:
        A tuple of 2 integers (n, d) such that n / d approximates x
        d is guaranteed positive
    """
    isNeg = False
    if x < 0:
        isNeg = True
        x = -x
    intPart = int(x // 1)
    x = x % 1
    if x < tol:
        return ((-1) ** isNeg * intPart, 1)
    lPtr = (0, 1)
    rPtr = (1, 1)
    medPtr = (1, 2)
    medVal = 1 / 2
    while abs(x - medVal) >= tol and maxIter > 0:
        if x < medVal:
            rPtr = medPtr
        else:
            lPtr = medPtr
        medPtr = (lPtr[0] + rPtr[0], lPtr[1] + rPtr[1])
        medVal = medPtr[0] / medPtr[1]
        maxIter -= 1
    return ((-1) ** isNeg * (medPtr[0] + intPart * medPtr[1]), medPtr[1])


def GaussLegendreAlgorithm(iterTime: int = 5, prec: int = 53) \
        -> __decimal.Decimal:
    __decimal.getcontext().prec = prec
    a = __decimal.Decimal('1')
    b = __decimal.Decimal('0.5').sqrt()
    t = __decimal.Decimal('1') / 4
    p = __decimal.Decimal('1')
    for i in range(iterTime):
        newA = (a + b) / 2
        newB = (a * b).sqrt()
        t = t - p * (a - newA) ** 2
        p = 2 * p
        a, b = newA, newB
    return (a + b) ** 2 / (4 * t)


def ArithmeticGeometricMean(a: float,
                            b: float,
                            tol: float = 1e-8,
                            maxIter: int = 25) -> float:
    """
    Compute the arithmetic-geometric mean of two numbers
    ---
    Parameters:
        a:
            Type: float
            Assumed positive
        b:
            Type: float
            Assumed positive
        tol:
            Type: float
            Default: 1e-8
            The stopping numerical tolerance
        maxIter:
            Type: int
            Default: 25
            The maximal number of iterations
    ---
    Return:
        The arithmetic-geometric mean of a and b as a float
    """
    a = __decimal.Decimal(a)
    b = __decimal.Decimal(b)
    while maxIter > 0:
        a, b = (a + b) / 2, (a * b).sqrt()
        if abs(b / a - 1) < tol:
            break
        maxIter -= 1
    return float(a)


def stringToPhoneNum(s: str, asMultiTap: bool = False) -> str:
    """
    Translate a string to the corresponding number sequence on phone input
    ---
    Parameter:
        s:
            Type: str
            The input string
        asMultiTap:
            Type: bool
            Default: False
            Determine if Multi-tap typing should be used instead of T9
    ---
    Return:
        A string where the lower-case order are translated to number as in phone input
        If a character is not a lower-case letter, it is be kept in the string
    """
    keyLists = ('abc', 'def', 'ghi', 'jkl', 'mno', 'pqrs', 'tuv', 'wxyz')
    # TODO: better construct method?
    keyDict = {}
    for idx, tok in enumerate(keyLists):
        keyDict.update(
            zip(tok,
                (str(idx + 2) * k
                 for k in (range(1, len(tok) + 1)
                           if asMultiTap
                           else (1, ) * len(tok))))
        )
    return ''.join([keyDict.get(i, i) for i in s])


def multitapToString(s: str):
    """
    Convert a multitap digit sequence into letters
    ---
    Parameter:
        s:
            Type: str
            The input string
    ---
    Return:
        A string where all digits in input s are translated into
            the corresponding letters via multitap
        Characters in s that are not in 2-9 are kept
    ---
    Exceptions:
        If the string cannot be decoded, a ValueError will be thrown.
    """
    translateDict = {
        2: 'abc', 3: 'def',
        4: 'ghi', 5: 'jkl', 6: 'mno',
        7: 'pqrs', 8: 'tuv', 9: 'wxyz'
    }
    outputStr = ""
    idx = 0
    while idx < len(s):
        if s[idx] in "23456789":
            offset = 0
            while idx + offset < len(s) and s[idx + offset] == s[idx]:
                offset += 1
            targetStr = translateDict[s[idx]]
            if offset >= len(targetStr):
                raise ValueError(f"Cannot decode position {idx} to {idx + offset}")
            else:
                outputStr += targetStr[offset - 1]
        else:
            outputStr += s[idx]
    return outputStr


def listMatrix(val: __typing.Union[float, __typing.Callable], *args: int) -> list:
    """
    Construct a matrix encoded as a nested list in vanilla python
    ---
    Parameter:
        val:
            Type: Union[Callable, float]
            The value used to fill the matrix
        *args:
            Type: int
            The dimensions of the matrix
    ---
    Return:
        A nested matrix of depth len(args),
            where the (k+1)th coordinate is of size args[k]
    """
    valF = val
    if isinstance(val, __Number):
        valF = (lambda *args: val)
    if len(args) == 1:
        return [valF(idx) for idx in range(args[0])]
    else:
        return [listMatrix(lambda *x: valF(idx, *x), *(args[1:]))
                for idx in range(args[0])]


def binom(n: int, r: int) -> float:
    """
    Approximate value for binomial coefficients
    ---
    Parameter:
        n:
            Type: int
        r:
            Type: int
    ---
    Return:
        The estimated binomial coefficient C(n, r)
        May not return an integer
    """
    r = min(r, n - r)
    return exp(sum(log1p((n - r) / i) for i in range(1, r + 1)))


def sqrtNewton(x: float, tol: float = 1e-17, maxIter: int = 25) -> float:
    """
    An algorithm to compute the square root of a float, by Newton's algorithm
    ---
    Parameter:
        x:
            Type: float
            The input value
        tol:
            Type: float
            Default: 1e-17
            The numerical tolerance
        maxIter:
            Type: int
            Default: 25
            The number of iterations to run the algorithm
    ---
    Return:
        The estimated value of the square root of x
    ---
    Exceptions:
        If x < 0, a ValueError will be thrown.
    """
    if x < 0:
        raise ValueError("Cannot take square root of a negative number.")
    elif x == 0:
        return 0
    else:
        r = x / 4
        tol = tol * tol
        while maxIter > 0 and abs(r * r / x - 1) > tol:
            r = (r + x / r) / 2
            maxIter -= 1
        return r


def sqrtByBinom(x: float,
                approxSqrtX: __typing.Optional[float] = None,
                n: int = 2,
                iterTime: int = 1) -> float:
    """
    An algorithm to compute the square root of a float, by an algorithm from 4Chan /sci/
    The origin of the algorithm is unknown.
    ---
    Parameter:
        x:
            Type: float
            The input value
        approxSqrtX:
            Type: Optional[float]
            Default: None
            The initial seed for the algorithm
            If None, will be set to x / 2
        n:
            Type: int
            Default: 2
            The order of the binomial set used
        iterTime:
            Type: int
            Default: 1
            The number of iterations to run the algorithm
    ---
    Return:
        The estimated value of the square root of x
    """
    if approxSqrtX is None:
        approxSqrtX = x / 2
    if iterTime != 1:
        return sqrtByBinom(x,
                           sqrtByBinom(x, approxSqrtX, n, 1),
                           n,
                           iterTime - 1)
    r = x / (approxSqrtX ** 2)
    return approxSqrtX \
        * sum(binom(n, 2 * k) * (r ** k) for k in range(0, n // 2 + 1)) \
        / sum(binom(n, 2 * k + 1) * (r ** k) for k in range(0, (n - 1) // 2 + 1))


def findAllMatchBrackets(inputStr: str,
                         acceptBrackets: str = "()[]{}",
                         escapeChar: str = '\\') -> list:
    if len(acceptBrackets) % 2 != 0:
        raise ValueError("acceptBrackets is not a string of even length")
    bracketStack = list()
    outputRes = list()
    openBracket = acceptBrackets[::2]
    closeBracket = acceptBrackets[1::2]
    matchingOpen = dict(zip(closeBracket, openBracket))
    charIdx = 0
    inputLen = len(inputStr)
    isEscaped = False
    while charIdx < inputLen:
        thisChar = inputStr[charIdx]
        if thisChar == escapeChar:
            isEscaped = not isEscaped
        else:
            if not isEscaped:
                if thisChar in openBracket:
                    bracketStack.append((thisChar, charIdx))
                elif thisChar in closeBracket:
                    if len(bracketStack) == 0 \
                            or bracketStack[-1][0] != matchingOpen[thisChar]:
                        raise ValueError(f"Unmatched {thisChar} "
                                         f"at index {charIdx}")
                    else:
                        outputRes.append(bracketStack[-1] + (charIdx, ))
                        bracketStack.pop()
            isEscaped = False
        charIdx += 1
    if len(bracketStack) != 0:
        thisChar, charIdx = bracketStack[-1]
        raise ValueError(f"Unmatched {thisChar} at index {charIdx}")
    return outputRes


def findThisMatchBracket(inputStr: str,
                         startPos: int = 0,
                         bracketPair: str = '{}',
                         escapeChar: str = '\\') -> int:
    """
    Find the matching bracket
    ---
    Parameter:
        inputStr:
            Type: str
            The string to be checked
        startPos:
            Type: int
            Default: 0
            The position to start finding
            Assumed to be position of the opening bracket
        bracketPair:
            Type: str
            Default: '{}'
            The bracket pair to be checked, encoded a string of length 2
            Required that the character of inputtStr at startPos is
                the first character of this string
            Will look for the second character of this string
        escapeChar:
            Type: str
            Default: '\\' (a single backslash)
            Assumed to be length 1.
            The character used to escape the bracket characters.
            Bracket characters preceeded by this character will be ignored.
            If the character itself is preceeded by an escapeChar,
                the next character will not be escaped. (Same as \ and \\)
    ---
    Return:
        An int that represents the position in inputStr that matches
            the open bracket at startPos with the correct depth
    ---
    Exceptions:
        If the character at startPos is escaped, a ValueError will be thrown.
        If there is no closing bracket that matche the opening bracket at startPos,
            a ValueError will be thrown.
    """
    if len(bracketPair) != 2:
        raise ValueError("bracketPair is not a string of length 2")
    if inputStr[startPos] != bracketPair[0]:
        raise ValueError("character at startPos "
                         f"({startPos}) is not an opening bracket. \n"
                         "Context: "
                         + inputStr[max(0, startPos - 10):
                                    min(len(inputStr), startPos + 10)])
    isEscaped = False
    charIdx = startPos - 1
    while charIdx >= 0 and inputStr[charIdx] == escapeChar:
        isEscaped = not isEscaped
        charIdx -= 1
    if isEscaped:
        raise ValueError("bracket at startPos is escaped")
    charIdx = startPos
    inputLen = len(inputStr)
    bracketCounter = 0
    while charIdx < inputLen:
        thisChar = inputStr[charIdx]
        if thisChar == escapeChar:
            isEscaped = not escapeChar
        else:
            if not isEscaped:
                if thisChar == bracketPair[0]:
                    bracketCounter += 1
                elif thisChar == bracketPair[1]:
                    bracketCounter -= 1
                    if bracketCounter == 0:
                        return charIdx
            isEscaped = False
        charIdx += 1
    raise ValueError("No matching close bracket")


def vecNorm(vec: tuple[float], p: float = 2):
    """
    Return the p-norm of a vector
    ---
    Parameter:
        vec:
            Type: tuple[float]
            The vector in question
        p:
            Type: float
            Default: 2
            The index of the norm
    ---
    Return:
        A float represnting the p-norm
    """
    return sum(abs(coor) ** p for coor in vec) ** (1 / p)


def intLatticePointInSphere(
        dim: int,
        r: float,
        excludeNeg: bool = False,
        excludeZero: bool = False) -> __typing.Iterator[tuple[int]]:
    """
    Generates integer coordinates in some sphere
    ---
    Parameter:
        dim:
            Type: int
            The dimension of the coordinate generated
        r:
            Type: float
            The radius of the sphere
        excludeNeg:
            Type: bool
            Default: False
            Determine if points with negative coordinates should be included.
        excludeZero:
            Type: bool
            Default: False
            Determine if points with coordinates 0 should be included.
    ---
    Return:
        Return r-tuples of integers that are included in a sphere of radius r.
        If excludeNeg or excludeZero is True, the corresponding tuples will be omitted.
    """
    if dim == 0:
        if r >= 0:
            yield tuple()
    elif r == 0:
        if not excludeZero:
            yield (0, ) * dim
    elif r > 0:
        enumLim = int(r)
        if not excludeNeg:
            for firstCoor in range(-enumLim, 0):
                for pt in intLatticePointInSphere(
                        dim - 1,
                        (r * r - firstCoor * firstCoor) ** (1 / 2),
                        excludeNeg=False,
                        excludeZero=excludeZero):
                    yield (firstCoor, ) + pt
        if not excludeZero:
            for pt in intLatticePointInSphere(
                    dim - 1,
                    r,
                    excludeNeg=excludeNeg,
                    excludeZero=False):
                yield (0, ) + pt
        for firstCoor in range(1, enumLim + 1):
            for pt in intLatticePointInSphere(
                    dim - 1,
                    (r * r - firstCoor * firstCoor) ** (1 / 2),
                    excludeNeg=excludeNeg,
                    excludeZero=excludeZero):
                yield (firstCoor, ) + pt

