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


def genStr(charList, minLen, maxLen) -> str:  
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


def userConfirm(message, charYStr='y', charNStr='n', defaultChar=None,
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


def strSimRatio(s1: str, s2: str, substrWeight=.6) -> float:
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


def inputPath(displayStr, forFile=True, defaultPath=None) -> str:
    import os.path
    s = ''
    while not (os.path.isfile if forFile else os.path.isdir)(s):
        s = input(displayStr).strip('\'\" ')
        if len(s) == 0:
            s = defaultPath
    return s

def textColoring(text: str, color="white") -> str:
    color = color.lower().strip()
    try:
        int(color[0:6], 16)
        colorCode = f'38;2;{int(color[0:2], 16)};{int(color[2:4], 16)};{int(color[4:6], 16)}'
    except ValueError: # is string name
        colorCode = colorCodeDict = {
                    'reset': 0, 
                    'none': 0,
                    'black': 30,
                    'red': 31,
                    'green': 32,
                    'yellow': 33,
                    'blue': 34,
                    'magenta': 35,
                    'cyan': 36,
                    'white': 37,
                    'bright black': 90,
                    'bright red': 91,
                    'bright green': 92,
                    'bright yellow': 93,
                    'bright blue': 94,
                    'bright magenta': 95,
                    'bright cyan': 96,
                    'bright white': 97,
                }.get(color, 0)
    return f'\x1b[{colorCode}m{text}\x1b[0m'

def FareyApprox(x: float, tol=1e-8, maxIter = 1000) -> (int, int):
    isNeg = False
    if x < 0:
        isNeg = True
        x = -x
    intPart = int(x // 1)
    x = x % 1
    if x < tol:
        return ((-1) ** isNeg * intPart, 1)
    # def refinePair(intPair):
        # def gcd(a,b):
            # return a if b == 0 else gcd(b, a % b)
        # g = gcd(intPair[0], intPair[1])
        # if g != 1:
            # print(a, b, g)
        # return (intPair[0] // g, intPair[1] // g)
    lPtr = (0, 1)
    rPtr = (1, 1)
    medPtr = (1, 2)
    medVal = 1 / 2
    while abs(x - medVal) >= tol and maxIter > 0:
        if x < medVal:
            rPtr = medPtr
        else:
            lPtr = medPtr
        # medPtr = refinePair((lPtr[0] + rPtr[0], lPtr[1] + rPtr[1]))
        medPtr = (lPtr[0] + rPtr[0], lPtr[1] + rPtr[1])
        medVal = medPtr[0] / medPtr[1]
        maxIter -= 1
    return ((-1) ** isNeg * (medPtr[0] + intPart * medPtr[1]), medPtr[1])

def GaussLegendreAlgorithm(iterTime = 5, prec = 53):
    import decimal
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
    __internaldict = {
        **dict.fromkeys(list('abc'), '2'), 
        **dict.fromkeys(list('def'), '3'), 
        **dict.fromkeys(list('ghi'), '4'), 
        **dict.fromkeys(list('jkl'), '5'), 
        **dict.fromkeys(list('mno'), '6'), 
        **dict.fromkeys(list('pqrs'), '7'), 
        **dict.fromkeys(list('tuv'), '8'), 
        **dict.fromkeys(list('wxyz'), '9'), 
    }
    def __new__(cls, s):
        return ''.join([cls.__internaldict.get(i, i) for i in s])

class jyutpingTone:
    # singleton pattern: no need to have more than one obj
    __instance = None
    __internaldict = None
    __printInfo = False
    @property
    def printInfo(self):
        return self.__printInfo
    @printInfo.setter
    def printInfo(self, value):
        self.__instance.__printInfo = bool(value)
    @staticmethod
    def __get_latest_dict__():
        if jyutpingTone.__instance.printInfo:
            print("Reading dictionary ...")
        dictLoc = r'C:\Users\acer\AppData\Roaming\Rime\jyut6ping3.dict.yaml'
        data = None
        with open(dictLoc, 'r', encoding='utf-8') as f:
            content = f.read()
            data = [line for line in content.split('\n') if not line.startswith('#') and len(line) != 0]
        if jyutpingTone.__instance.printInfo:
            print("Parsing dictionary ...")
        data = [line.split('\t')[:2] for line in data[data.index('...') + 1:]]
        data = [(wd, pron[:-1], int(pron[-1]), '平' if pron[-1] in '14' else '仄') for (wd, pron) in data if len(wd) == 1]
        d = dict()
        for (wd, pron, tone, levelIndi) in data:
            d[wd] = d.get(wd, []) + [(pron, tone, levelIndi)]
        return d
    @classmethod
    def update_dict(cls):
        if cls.__instance is not None:
            ogPrintInfo = cls().printInfo
            cls().printInfo = True
            cls().__internaldict = cls.__get_latest_dict__()
            cls().printInfo = ogPrintInfo
        else:
            cls(True).printInfo = False
    @classmethod
    def list_all(cls, s):
        return [cls().__internaldict[c] if c in cls().__internaldict else c for c in s]
    @classmethod
    def convert(cls, s):
        lst = cls().list_all(s)
        for wordChoices in lst:
            print(wordChoices)
    def __new__(cls, printInfo = False):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
            cls.__instance.__internaldict = jyutpingTone.__get_latest_dict__()
        cls.__instance.__printInfo = printInfo
        return cls.__instance
