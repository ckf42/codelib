from argparse import Namespace, ArgumentParser
from msvcrt import kbhit, getch
from re import match, Match
from time import monotonic, sleep
from typing import Optional
from winsound import Beep

def getArgs() -> Namespace:
    def countdownLenConverter(arg: str) -> float:
        numRegex: str = r'\d+|\d*\.\d+'
        matches: Optional[Match] \
                = match('|'.join(('^' + ''.join(f'(?:({numRegex}){sym})?'
                                                for sym in "hms") + '$',
                                  f'^({numRegex})$')),
                        arg)
        assert matches is not None, f"Unable to parse argument: {arg}"
        return sum((float(a) if a is not None else 0) * b
                   for (a, b) in zip(matches.groups(), (3600, 60, 1, 1),
                                     strict=True))

    parser: ArgumentParser = ArgumentParser()
    parser.add_argument(
            'countdownLen',
            type=countdownLenConverter,
            help="length of countdown, in second or in format like 1h2m3s. "
            "Also allows float values like 1.5m")
    parser.add_argument(
            '--freq', '-f',
            action='append',
            type=int,
            help="frequency of beep, in integral Hz. "
            "May specify multiple times for series of beeps. "
            "Defaults to 2200Hz and 1800Hz")
    parser.add_argument(
            '--updateFreq',
            type=float,
            default=10.0,
            help="Timer update frequency, in Hz. "
            "The larger, the more accurate the timer is but the more work to do. "
            "Defaults to 10Hz")
    parser.add_argument(
            '--beepLen',
            type=float,
            default=0.5,
            help="Length of each beep, in seconds. "
            "Also reaction time to key press. "
            "Small values may lead to skipped beep sequence. "
            "Defaults to 0.5s")
    args: Namespace = parser.parse_args()
    if args.freq is None:
        args.freq = (2200, 1800)
    assert args.countdownLen > 0, "Only positive time is allowed"
    for freq in args.freq:
        assert freq > 0, "Only positive frequency is allowed"
    assert args.beepLen > 0, "Only positive beepLen is allowed"
    args.beepLenMs = int(args.beepLen * 1000)
    return args

def formatTime(timeInSecond: float) -> str:
    assert timeInSecond >= 0, "No negative time allowed"
    remainMinute, remainSecond = divmod(timeInSecond, 60)
    remainHour, remainMinute = divmod(remainMinute, 60)
    return f"{remainHour:.0f}:{remainMinute:02.0f}:{remainSecond:02.0f}"

def waitTime(
        timeInSecond: float,
        sleepIntervalSecond: float,
        ) -> bool:
    """
    wait till `timeInSecond` seconds elapsed
    check every `sleepIntervalSecond` seconds,
        the smaller, the more accurate but more work to do
    also display in console of the remain time
    return if is commanded to quit early
    BLOCKING
    """
    initTime: float = monotonic()
    lastPrintLen: int = 0
    targetTime: float = initTime + timeInSecond
    while (remainTime := targetTime - monotonic()) >= 0:
        if kbhit() and getch() in b'q ':
            return True
        sleep(sleepIntervalSecond)
        msg: str = "Remain time: " + formatTime(remainTime)
        lastPrintLen = len(msg)
        print(msg + " " * max(0, lastPrintLen - len(msg)), end='\r')
    return False

def main() -> None:
    args: Namespace = getArgs()
    print("Press CTRL-C, space, or q to quit")
    try:
        if waitTime(args.countdownLen, 1.0 / args.updateFreq):
            raise KeyboardInterrupt  # same as C-C
        shouldBreak: bool = False
        lastPrintLen: int = 0
        baseMsg: str = "Time's up. Overdue: "
        baseMsgLen: int = len(baseMsg)
        overdueOffset: float = monotonic()
        while not shouldBreak:
            formattedTimeStr: str = formatTime(monotonic() - overdueOffset)
            print(baseMsg,
                  formattedTimeStr,
                  " " * max(0, lastPrintLen - baseMsgLen - len(formattedTimeStr)),
                  sep='',
                  end='\r')
            for freq in args.freq:
                if kbhit() and getch() in b'q ':
                    shouldBreak = True
                    break
                Beep(freq, args.beepLenMs)  # this is BLOCKING
    except KeyboardInterrupt:
        # terminate on C-C, die gracefully
        pass
    finally:
        # print empty line to retain overdue time
        print("")

if __name__ == '__main__':
    main()
