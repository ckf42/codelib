from argparse import Namespace, ArgumentParser
from msvcrt import kbhit, getch
from re import match, Match
from time import monotonic, sleep
from typing import Optional
from winsound import Beep

def countdownLenConverter(arg: str) -> float:
    numRegex: str = r'-?\d+|-?\d*\.\d+'
    matches: Optional[Match] \
            = match('|'.join(map(lambda x: '^' + x + '$',
                                 (''.join(f'(?:({numRegex}){sym})?'
                                          for sym in 'hms'),
                                  f'({numRegex})'))),
                    arg)
    assert matches is not None, f"Unable to parse argument: {arg}"
    resSecond: float = sum((float(a) if a is not None else 0) * b
                           for (a, b) in zip(matches.groups(), (3600, 60, 1, 1),
                                             strict=True))
    return resSecond

def getArgs() -> Namespace:
    parser: ArgumentParser = ArgumentParser()
    parser.add_argument(
            'countdownLen',
            type=countdownLenConverter,
            help="length of countdown, in second or in format like 1h2m3s. "
            "Also allows float values like 1.5m and negative parts like 1h-5s. "
            "Total time must be positive")
    parser.add_argument(
            '--freq', '-f',
            action='append',
            type=int,
            help="frequency of beep, in integral Hz. "
            "Must be in range [37, 32767] or is zero (for an empty segment). "
            "May specify multiple times for series of beeps. "
            "Defaults to 2200Hz and 1800Hz")
    parser.add_argument(
            '--updateFreq', '-uf',
            type=float,
            default=5.0,
            help="Timer update frequency, in Hz. "
            "The larger, the more accurate the timer is but the more work to do. "
            "Should be meaningless to set this too high. "
            "Defaults to 5Hz")
    parser.add_argument(
            '--beepLen', '-bl',
            type=float,
            default=0.4,
            help="Length of each beep, in seconds. "
            "Also reaction time to key press. "
            "Small values may lead to skipped beep sequence. "
            "Defaults to 0.4s")
    args: Namespace = parser.parse_args()
    assert args.countdownLen > 0, "count down length must be positive"
    if args.freq is None:
        args.freq = (2200, 1800)
    for freq in args.freq:
        if freq != 0:
            assert 37 <= freq <= 32767, f"Invalid frequency: {freq}Hz"
    assert args.updateFreq > 0, "updateFreq must be positive"
    assert args.beepLen > 0, "beepLen must be positive"
    args.beepLenMs = int(args.beepLen * 1000)
    return args

def formatTime(timeInSecond: float) -> str:
    assert timeInSecond >= 0, "No negative time allowed"
    remainMinute, remainSecond = divmod(timeInSecond, 60)
    remainHour, remainMinute = divmod(remainMinute, 60)
    return f"{round(remainHour)}:{round(remainMinute):02}:{int(remainSecond):02}"

def isToQuitInWaitTime(
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
    targetTime: float = initTime + timeInSecond
    while (remainTime := targetTime - monotonic()) >= 0:
        if kbhit() and getch() in b'q ':
            return True
        sleep(sleepIntervalSecond)
        print("Remaining: " + formatTime(remainTime), end='\x1b[K\r')
    return False

def main() -> None:
    args: Namespace = getArgs()
    print("Press CTRL-C, space, or q to quit")
    try:
        if isToQuitInWaitTime(args.countdownLen, 1.0 / args.updateFreq):
            raise KeyboardInterrupt  # same as C-C
        shouldBreak: bool = False
        overdueOffset: float = monotonic()
        while not shouldBreak:
            print("Time's up. Overdue: " + formatTime(monotonic() - overdueOffset),
                  end='\x1b[K\r')
            for freq in args.freq:
                if kbhit() and getch() in b'q ':
                    shouldBreak = True
                    break
                # this part is BLOCKING
                if freq != 0:
                    Beep(freq, args.beepLenMs)
                else:
                    sleep(args.beepLen)
    except KeyboardInterrupt:
        # terminate on C-C, die gracefully
        pass
    finally:
        # print empty line to retain overdue time
        print("")

if __name__ == '__main__':
    main()

