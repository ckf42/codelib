import decimal
if __name__ == '__main__':
    exit()


def viewList(lst, itemPerPage,
             displayMethod=print, showOrdinal=False, useIndex=False,
             headMessageStrFunc=lambda lstLen: f"{lstLen} item(s) in total"):
    if headMessageStrFunc is not None:
        print(headMessageStrFunc(len(lst)))
    if len(lst) == 0:
        return
    elif itemPerPage <= 0 or len(lst) <= itemPerPage:
        # for item in lst: displayMethod(item)
        for i in range(len(lst)):
            if showOrdinal:
                print(f'#{i+1}:    ', end='')
            if useIndex:
                displayMethod(lst[i], i)
            else:
                displayMethod(lst[i])
    else:
        import msvcrt
        n = int((len(lst) + itemPerPage - 1) / itemPerPage)
        index = 0
        command = '.'
        while index < n:
            print(f"---- Page {index+1} / {n} ----")
            for itemIndex in range(index * itemPerPage,
                                   min((index + 1) * itemPerPage, len(lst))):
                if showOrdinal:
                    print(f"#{itemIndex+1}:    ", end='')
                # displayMethod(lst[itemIndex])
                if useIndex:
                    displayMethod(lst[itemIndex], itemIndex)
                else:
                    displayMethod(lst[itemIndex])
            if index == n - 1:
                print("---- End of list, forward to quit ----")
            print(f"[F]orward{', [B]ackward' if index!=0 else ''}, "
                  "[J]ump or [Q]uit: ",
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
            if command == 'q':
                return
            elif command == 'h':
                print("Help Message")
                print("h    show this help message")
                print("f    go to next page")
                print("b    go to last page")
                print("j    jump to some page, or to some item")
                print("c    toggle ordinal number display")
                print("q    quit")
                input("Press [Enter] to quit this message")
            elif command in 'fb':
                index += (1 if command == 'f' else -1)
            elif command == 'j':
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
                index = (int((command - 1) / itemPerPage)
                         if isItem else command - 1)
            elif command == 'c':
                showOrdinal = not showOrdinal


def genStr(charList: str, minLen: int, maxLen: int) -> str:
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


def floydCycleDetect(f: callable, x0) -> (int, int):
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


class textColoring:
    colorCode = {
        'reset': 0, 'none': 0, 'black': 30, 'red': 31, 'green': 32,
        'yellow': 33, 'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37,
        'bright black': 90, 'bright red': 91, 'bright green': 92,
        'bright yellow': 93, 'bright blue': 94, 'bright magenta': 95,
        'bright cyan': 96, 'bright white': 97,
    }

    def __new__(cls, text: str, color: str = "white") -> str:
        color = color.lower().strip()
        try:
            rHex, gHex, bHex = \
                int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16)
            color = f'38;2;{rHex};{gHex};{bHex}'
        except ValueError:  # is string name
            color = cls.colorCode.get(color, 0)
        return f'\x1b[{color}m{text}\x1b[0m'


def FareyApprox(x: float,
                tol: float = 1e-8,
                maxIter: int = 1000) -> (int, int):
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
        -> decimal.Decimal:
    decimal.getcontext().prec = prec
    a = decimal.Decimal('1')
    b = decimal.Decimal('0.5').sqrt()
    t = decimal.Decimal('1') / 4
    p = decimal.Decimal('1')
    for i in range(iterTime):
        newA = (a + b) / 2
        newB = (a * b).sqrt()
        t = t - p * (a - newA) ** 2
        p = 2 * p
        a, b = newA, newB
    return (a + b) ** 2 / (4 * t)


class stringToPhoneNum:
    _internaldict = {
        **dict.fromkeys(list('abc'), '2'),
        **dict.fromkeys(list('def'), '3'),
        **dict.fromkeys(list('ghi'), '4'),
        **dict.fromkeys(list('jkl'), '5'),
        **dict.fromkeys(list('mno'), '6'),
        **dict.fromkeys(list('pqrs'), '7'),
        **dict.fromkeys(list('tuv'), '8'),
        **dict.fromkeys(list('wxyz'), '9'),
    }

    def __new__(cls, s: str) -> str:
        return ''.join([cls._internaldict.get(i, i) for i in s])


def listMatrix(val, *args) -> list:
    from numbers import Number
    valF = val
    if isinstance(val, Number):
        valF = (lambda *args: val)
    if len(args) == 1:
        return [valF(idx) for idx in range(args[0])]
    else:
        return [listMatrix(lambda *x: valF(idx, *x), *(args[1:]))
                for idx in range(args[0])]


def overwriteThenDelete(filePath: str,
                        passes: int = 3, blockSize: int = 4096,
                        randomModule: str = 'os') -> None:
    randomBitGen = None
    if randomModule == 'random':
        from random import getrandbits

        def randomBitGen(k):
            return bytes(getrandbits(8) for i in range(k))
    elif randomModule == 'secrets':
        from secrets import randbits

        def randomBitGen(k):
            return bytes(randbits(8) for i in range(k))
    else:
        from os import urandom

        def randomBitGen(k):
            return urandom(k)
    from os import fstat, remove
    with open(filePath, 'rb+') as f:
        fileSize = fstat(f.fileno()).st_size
        blockCount, remainBytes = divmod(fileSize, blockSize)
        for passNo in range(passes):
            f.seek(0)
            for i in range(blockCount):
                f.write(randomBitGen(blockSize))
            f.write(randomBitGen(remainBytes))
    remove(filePath)


def binom(n: int, r: int) -> float:
    from math import log1p, exp
    r = min(r, n - r)
    return exp(sum(log1p((n - r) / i) for i in range(1, r + 1)))


def sqrtByBinom(x: float, approxSqrtX: float = None,
                n: int = 2, iterTime: int = 1) -> float:
    if approxSqrtX is None:
        approxSqrtX = x / 2
    if iterTime != 1:
        return sqrtByBinom(x,
                           sqrtByBinom(x, approxSqrtX, n, 1),
                           n,
                           iterTime - 1)
    r = x / (approxSqrtX ** 2)
    return approxSqrtX \
        * sum(binom(n, 2 * k) * r**k for k in range(0, n // 2 + 1)) \
        / sum(binom(n, 2 * k + 1) * r**k for k in range(0, (n - 1) // 2 + 1))


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


def findThisMatchBracket(inputStr: str, startPos: int = 0,
                         bracketPair: str = '{}',
                         escapeChar: str = '\\') -> int:
    if len(bracketPair) != 2:
        raise ValueError("bracketPair is not a string of length 2")
    if inputStr[startPos] != bracketPair[0]:
        raise ValueError("character at startPos is not an opening bracket")
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
