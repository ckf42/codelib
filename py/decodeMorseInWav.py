"""
slightly modularized rewrite of decodeMorseInWav.old.py
not much different from the old one
mostly for debugging
"""

from argparse import ArgumentParser, Namespace
from datetime import timedelta
from itertools import groupby
from pathlib import Path
from scipy.io import wavfile
from scipy.signal import welch, stft, find_peaks
from scipy.stats import gaussian_kde
import numpy as np
from typing import Optional
import MorseCodeDict as MCD

def getArgs(argStr: Optional[str]) -> Namespace:
    parser = ArgumentParser(
            epilog="Work best on consistent intervals and without noise. "
            "Should still work if signal not too corrupted. "
            "May need to cleanup signal and test with different arguments "
            "to get accurate result")
    parser.add_argument(
            'file',
            type=str,
            help="Path to wav file. Must be in PCM or float format")
    parser.add_argument(
            '--freq', '-f',
            type=float,
            help="The (supposed) signal frequency, in Hz. "
            "If not provided, will be determined by Welch's method")
    parser.add_argument(
            '--nperseg', '-n',
            type=int,
            default=512,
            help="The number of samples in each STFT (and Welch) segment. "
            "Typically a power of 2. Usually 256, 512, or 1024. "
            "Defaults to 512")
    parser.add_argument(
            '--channel', '-c',
            type=int,
            choices=(0, 1),
            default=0,
            help="The channel number of the signal. "
            "0 for left, 1 for right. "
            "Ignored if the file is single-channel. "
            "Defaults to 0")
    parser.add_argument(
            '--onLen', '-1',
            type=float,
            nargs='*',
            help="Typical lengths of a signal, in seconds. "
            "If specified, can specify at most 2 lengths, "
            "which are the `di` (short signal) length "
            "and the `dah` (long signal) length. "
            "If not specified, will try to deduce from signal. "
            "If only 1 length is specified, "
            "will use 3 times the length as the second one")
    parser.add_argument(
            '--offLen', '-0',
            type=float,
            nargs='*',
            help="Typical lengths of a pause, in seconds. "
            "If specified, can specify at most 3 lengths, "
            "which are signal pause (short), letter pause (medium), "
            "and word pause (long). "
            "If the list is empty (only the switch is present) or 0 is included, "
            "will try to use the most common lengths in signal. "
            "If not specified, will try to deduce from signal. "
            "If less than 3 lengths are specified, "
            "will attempt to fill up the remaining lengths "
            "with the (1, 3, 7) pattern")
    parser.add_argument(
        '--lang',
        type=str,
        choices=MCD._SUPPORTED_LANG,
        default='en',
        help="The language variant of Morse code to use. Defautls to en"
    )
    parser.add_argument(
            '--verbose', '-v',
            action='count',
            default=0,
            help="Verbosity for diagnostic info. May repeat at most twice")
    args = parser.parse_args(None if argStr is None else argStr.split())
    args.file = Path(args.file).expanduser().resolve()
    if not args.file.is_file():
        parser.error(f"file {str(args.file)} is not a valid file")
    if args.freq is not None and args.freq <= 0:
        parser.error(f"frequency {args.freq} is not a positive number")
    # process lengths
    if args.onLen is not None:
        assert 1 <= len(args.onLen) <= 2
        assert len(frozenset(args.onLen)) == len(args.onLen), "onLen not unique"
        assert min(args.onLen) > 0, "onLen must be positive"
        args.onLen.sort()
        if len(args.onLen) == 1:
            args.onLen.append(args.onLen[0] * 3)
    if args.offLen is not None:
        assert len(args.offLen) <= 3
        assert len(frozenset(args.offLen)) == len(args.offLen), "offLen not unique"
        if len(args.offLen) != 0:
            assert min(args.offLen) >= 0, "offLen must be positive"
        if 0 in args.offLen:
            args.offLen.clear()
        if len(args.offLen) == 1:
            args.offLen.append(min(args.offLen) * 3)
        if len(args.offLen) == 2:
            args.offLen.append(min(args.offLen) * 7)
        args.offLen.sort()
    args.morseDict = MCD.MorseDict(lang=args.lang)
    return args

def getFileAndPreprocess(args: Namespace) -> tuple[int, np.ndarray]:
    sampleRate: int
    data: np.ndarray
    sampleRate, data = wavfile.read(args.file)
    if data.ndim >= 2:
        data = data[:, args.channel]
    if args.verbose:
        print(f'file={str(args.file)}')
        print(f'{sampleRate=}')
    xNormalized: np.ndarray = np.subtract(
            data, np.mean(data, dtype=np.float32), dtype=np.float32)
    np.divide(xNormalized, np.max(np.abs(xNormalized)), out=xNormalized)
    if args.verbose:
        print(f'length={xNormalized.size / sampleRate:.2f}s')
    return (sampleRate, xNormalized)

def getFreq(data: np.ndarray, sampleRate: int, args: Namespace) -> float:
    if args.freq is not None:
        if args.verbose:
            print(f"freq={args.freq} (overridden)")
        return args.freq
    wfq, Pxx = welch(data, fs=sampleRate,
                     nperseg=args.nperseg, average='median')
    freq = wfq[Pxx.argmax()]
    if args.verbose:
        print(f"{freq=}")
    return freq

def digitalize(data: np.ndarray,
               freq: float,
               sampleRate: float,
               args: Namespace) -> tuple[float, float, tuple[tuple[bool, int], ...]]:
    # fq, st, Zxx = stft(data, sampleRate, nperseg=args.nperseg, scaling='psd')
    # Zxx = np.power(np.abs(Zxx), 2)
    # np.divide(Zxx, Zxx.sum(axis=0), out=Zxx)
    fq, st, Zxx = stft(data, sampleRate, nperseg=args.nperseg)
    fqp = np.abs(Zxx)[np.argmin(np.abs(fq - freq)), :]
    valGp = list((k, len(tuple(v))) for k, v in groupby(fqp >= np.mean(fqp)))
    currTime = 0.0
    if not valGp[0][0]:
        currTime = valGp[0][1]
        valGp.pop(0)
    if not valGp[-1][0]:
        valGp.pop()
    if args.verbose >= 2:
        print(f'consecutive segment count={len(valGp)}')
        print(f'unit len={st[1]:.3g}s')
    return (currTime, st[1], tuple(valGp))

def getCharLen(sigLst: tuple[tuple[bool, int], ...],
               segTime: float,
               args: Namespace) -> list[np.ndarray]:
    onVal = np.asarray(tuple(v for k, v in sigLst if k))
    offVal = np.asarray(tuple(v for k, v in sigLst if not k))
    epdfs = (gaussian_kde(offVal), gaussian_kde(onVal))
    xRanges = tuple(np.linspace(min(vList) - 3,
                                max(vList) + 3,
                                len(frozenset(vList)) * 10)
                    for vList in (offVal, onVal))
    peakProps = tuple(
            tuple(
                (peakVal, pProp)
                for peakVal in xRanges[tIdx][find_peaks(epdfs[tIdx](xRanges[tIdx]))[0]]
                if (pProp := epdfs[tIdx].integrate_box_1d(peakVal - 3, peakVal + 3)) \
                        >= 0.01 * epdfs[tIdx].integrate_box_1d(xRanges[tIdx][0],
                                                               xRanges[tIdx][-1]))
            for tIdx in (0, 1))
    durList = list(
            (np.sort(tuple(
                peakProps[tIdx][i][0]
                for i in np.argpartition(tuple(p[1] for p in peakProps[tIdx]),
                                         -min(len(peakProps[tIdx]),
                                              maxCount))[-1:-(maxCount + 1):-1]))
             if overrideLen is None
             else (np.asarray(overrideLen) / segTime))[:maxCount]
            for (tIdx, overrideLen, maxCount) in zip((0, 1),
                                                     (args.offLen, args.onLen),
                                                     (3, 2)))
    assert len(durList[1]) == 2, "Unable to determine unit signal length"
    if len(durList[0]) == 0:
        # fail to find peak, fallback with sorting
        offHist = np.histogram(offVal, bins='auto')
        offPeakIdx = np.argpartition(offHist[0], -3)[-1:-4:-1]
        durList[0] = np.sort(((offHist[1][1:] + offHist[1][:-1]) / 2)\
                [offPeakIdx[offHist[0][offPeakIdx] != 0]])
    if len(durList[0]) == 0:
        # still fail to find peak, fallback with signal length
        durList[0] = np.asarray(tuple(i * durList[1][1] for i in (1, 3, 7)))
    elif len(durList[0]) == 1:
        # fill up assuming 1-3-7 pattern comparing with durList[1]
        durList[0] = np.asarray((1, 3, 7)) * durList[0][0] \
                / (1, 3, 7)[np.abs(durList[0][0] - np.hstack(
                    (durList[1], durList[1][0] * 4 + durList[1][1]))).argmin()]
    elif len(durList[0]) == 2:
        # fill up assuming 1-3-7 pattern by itself
        insIdx = np.abs(durList[0][1] / durList[0][0] - np.asarray((7 / 3, 7, 3))).argmin()
        durList[0] = np.insert(durList[0], insIdx, durList[0][0] * (1 / 3, 3, 7)[insIdx])
    if args.verbose:
        print('characteristic lengths:')
        print('on',
              ' '.join(f'{i * segTime:.3g}s' for i in durList[1]),
              '' if args.onLen is None else '(overridden)')
        print('off',
              ' '.join(f'{i * segTime:.3g}s' for i in durList[0]),
              '' if args.offLen is None else '(overridden)')
    for i in (0, 1):
        durList[i] = np.hstack(((0,), durList[i]))
    return durList

def decodeSignal(signalLst: tuple[tuple[bool, int], ...],
                 charLen: tuple[np.ndarray, np.ndarray],
                 segTime: float,
                 initTime: float,
                 args: Namespace) -> str:
    sigBuff = list()
    decRes = list()
    startTime = None
    currTime = initTime
    for i, (sigType, sigDur) in enumerate(signalLst):
        currTime += sigDur
        durIdx = int(np.abs(charLen[1 if sigType else 0] - sigDur).argmin())
        if durIdx == 0 or (not sigType and durIdx == 1):
            # too short, probably noise; or short pause, sep for sig
            continue
        if startTime is None:
            startTime = currTime - sigDur
        if sigType:
            sigBuff.append('.' if durIdx == 1 else '-')
        elif len(sigBuff) != 0:
            sig = ''.join(sigBuff)
            sigBuff.clear()
            sym = args.morseDict.reverse_dict.get(sig, '{' + sig + '}')
            assert startTime is not None
            decRes.append((i - 1, (startTime, currTime - sigDur), sig, sym))
            startTime = None
            if durIdx == 3:
                # long pause, space
                decRes.append((i, (currTime - sigDur, currTime), 'PAUSE', ' '))
    if len(sigBuff) != 0:
        sig = ''.join(sigBuff)
        sym = args.morseDict.reverse_dict.get(sig, '{' + sig + '}')
        assert startTime is not None
        decRes.append((len(signalLst) - 1, (startTime, currTime), sig, sym))
    if args.verbose >= 2:
        maxSigLen = max(len(p[2]) for p in decRes)
        maxIdxLen = len(str(len(signalLst)))
        print('Decoded signal:')
        for idx, tp, sig, msg in decRes:
            t0 = timedelta(seconds=tp[0] * segTime)
            t1 = timedelta(seconds=tp[1] * segTime)
            print(str(idx).ljust(maxIdxLen),
                  str(t0)[:-4] if t0.microseconds != 0 else str(t0),
                  '-',
                  str(t1)[:-4] if t1.microseconds != 0 else str(t1),
                  sig.ljust(maxSigLen),
                  msg)
    return ''.join(p[-1] for p in decRes)

def main():
    args: Namespace = getArgs(None)
    sampleRate: int
    data: np.ndarray
    sampleRate, data = getFileAndPreprocess(args)
    freq: float = getFreq(data, sampleRate, args)
    startTime: float
    segTime: float
    signalLst: tuple[tuple[bool, int], ...]
    startTime, segTime, signalLst = digitalize(data, freq, sampleRate, args)
    charLen: tuple[np.ndarray, np.ndarray] = tuple(getCharLen(signalLst, segTime, args))
    print(decodeSignal(signalLst, charLen, segTime, startTime, args))

if __name__ == '__main__':
    main()
