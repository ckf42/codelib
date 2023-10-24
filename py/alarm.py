from argparse import ArgumentParser, Namespace
from msvcrt import getch, kbhit
from platform import system as systemName
from re import Match, match
from time import monotonic, sleep
from typing import Optional

hasWinsound: bool = False
try:
    from winsound import Beep
    hasWinsound = True
except ImportError:
    pass

def beep(freq: int, lenMs: int, p, usePA) -> None:
    if hasWinsound and not usePA:
        Beep(freq, lenMs)
    else:
        import pyaudio as pa
        import array
        from math import sin, pi
        assert p is not None
        data = array.array('f',
                           (sin(2 * pi * i * freq / 44100)
                            for i in range(int(lenMs * 44.1)))).tobytes()
        stream = p.open(format=pa.paFloat32,
                        channels=1,
                        rate=44100,
                        output=True)
        stream.write(data)
        stream.stop_stream()
        stream.close()


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
    parser.add_argument(
            '--blocky', '-b',
            action='store_true',
            help="Show remain time with 7-row blocky display")
    parser.add_argument(
            '--pa',
            action='store_true',
            help="Use PyAudio instead of winsound if possible. "
            "winsound is always used unless this is set. "
            "On where winsound is not available, PyAudio is always used. "
            "The audio cutoff is more audible for PyAudio")
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
    # handle ansi
    if systemName() == 'Windows':
        try:
            from colorama import just_fix_windows_console as jfwc
            jfwc()
        except (ModuleNotFoundError, ImportError):  # old colorama does not have jfwc
            # https://stackoverflow.com/a/64222858
            # apparently it is a bug https://bugs.python.org/issue30075
            from os import system
            system('')
    return args

def formatTime(timeInSecond: float, omitHourIfOk: bool = True) -> str:
    assert timeInSecond >= 0, "No negative time allowed"
    remainMinute, remainSecond = divmod(timeInSecond, 60)
    remainHour, remainMinute = divmod(remainMinute, 60)
    return ("" if omitHourIfOk and remainHour == 0 else f"{round(remainHour)}:") \
            + f"{round(remainMinute):02}:{int(remainSecond):02}"

blockyCharDict: dict[str, str] = {
    '0': '011111001000100111110',
    '1': '000000000000000111110',
    '2': '010111001010100111010',
    '3': '010101001010100111110',
    '4': '011100000010000111110',
    '5': '011101001010100101110',
    '6': '011111001010100101110',
    '7': '010000001000000111110',
    '8': '011111001010100111110',
    '9': '011101001010100111110',
    ':': '0010100',
}
blockyCharDict = {
    k: ' ' * 7 + ''.join('\u2588' if c == '1' else ' ' for c in v)
    for k, v in blockyCharDict.items()
}

def isToQuitInWaitTime(
        timeInSecond: float,
        sleepIntervalSecond: float,
        blocky: bool = False
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
    if blocky:
        print("Remaining:\x1b[K" + "\n" * 7)
    while (remainTime := targetTime - monotonic()) >= 0:
        if kbhit() and getch() in b'q ':
            return True
        if not blocky:
            print("Remaining: " + formatTime(remainTime), end="\x1b[K\r")
        else:
            outBuff: str = ''.join(blockyCharDict[c] for c in formatTime(remainTime))
            colCount: int = len(outBuff) // 7
            print('\x1b[7F', end='')
            for r in range(7):
                for c in range(colCount):
                    print(outBuff[r + 7 * c], end='')
                print('\x1b[K')
        sleep(sleepIntervalSecond)
    if blocky:
        # clear blocky display after countdown
        print('\x1b[1F\x1b[K' * 8, end='')
    return False

def main() -> None:
    args: Namespace = getArgs()
    p = None
    if not hasWinsound or args.pa:
        import pyaudio as pa
        import array
        from math import sin, pi
        p = pa.PyAudio()
    print("Press CTRL-C, space, or q to quit")
    try:
        if isToQuitInWaitTime(args.countdownLen,
                              1.0 / args.updateFreq,
                              blocky=args.blocky):
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
                    beep(freq, args.beepLenMs, p, args.pa)
                else:
                    sleep(args.beepLen)
    except KeyboardInterrupt:
        # terminate on C-C, die gracefully
        pass
    finally:
        # print empty line to retain overdue time
        # this gives an extra line for --blocky as the display already have one
        print("")
    if p is not None:
        p.terminate()

if __name__ == '__main__':
    main()

