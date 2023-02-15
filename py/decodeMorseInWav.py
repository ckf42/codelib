from argparse import ArgumentParser
from pathlib import Path
from itertools import groupby
from datetime import timedelta
import numpy as np
from scipy.signal import welch, stft, find_peaks
from scipy.io import wavfile
from scipy.stats import gaussian_kde
import MorseCodeDict as MCD

def getCliArg():
    parser = ArgumentParser(
            epilog="Work best on consistent intervals and without noise. "
            "Should still work if signal not too corrupted. "
            "May need to cleanup signal and test with different arguments "
            "to get accurate result")
    parser.add_argument(
            'file', type=str,
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
            '--verbose', '-v',
            action='count',
            default=0,
            help="Verbosity for diagnostic info. May repeat at most twice")
    args = parser.parse_args()
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
    return args

def main():
    args = getCliArg()
    # get data
    filepath = Path(args.file)
    assert filepath.is_file(), "Not a valid file"
    sampleRate, data = wavfile.read(filepath)
    if data.ndim >= 2:
        data = data[:, args.channel]
    if args.verbose:
        print(f'filepath={str(filepath.resolve())}')
        print(f'{sampleRate=}')
    # normalized
    xNormalized = np.subtract(data,
                              np.mean(data, dtype=np.float32),
                              dtype=np.float32)
    np.divide(xNormalized, np.max(np.abs(xNormalized)), out=xNormalized)
    if args.verbose:
        print(f'length={xNormalized.size / sampleRate:.2f}s')
    # find signal freq
    freq = args.freq
    if freq is None:
        wfq1, Pxx1 = welch(xNormalized, sampleRate,
                           nperseg=args.nperseg, average='mean')
        wfq2, Pxx2 = welch(xNormalized, sampleRate,
                           nperseg=args.nperseg, average='median')
        freq = wfq1[Pxx1.argmax()] if Pxx1.max() >= Pxx2.max() else wfq2[Pxx2.argmax()]
        if args.verbose:
            print(f'{freq=:.2f}')
    elif args.verbose:
        assert freq > 0
        print(f'{freq=} (overridden)')
    assert freq is not None
    # convert to digital
    fq, st, Zxx = stft(xNormalized, sampleRate, nperseg=args.nperseg)
    fqp = np.abs(Zxx)[np.argmin(np.abs(fq - freq)), :]
    valGp = list((k, len(tuple(v))) for k, v in groupby(fqp >= np.mean(fqp)))
    currTime = 0
    if not valGp[0][0]:
        currTime = valGp[0][1]
        valGp.pop(0)
    if not valGp[-1][0]:
        valGp.pop()
    if args.verbose >= 2:
        print(f'consecutive segment count={len(valGp)}')
        print(f'unit len={st[1]:.3g}s')
    # find signal lengths
    onVal = np.asarray(tuple(v for k, v in valGp if k))
    offVal = np.asarray(tuple(v for k, v in valGp if not k))
    epdfs = (gaussian_kde(offVal), gaussian_kde(onVal))
    xRanges = tuple(np.linspace(min(vList) - 3, max(vList) + 3, len(frozenset(vList)) * 10)
                    for vList in (offVal, onVal))
    peakProps = tuple(
            tuple((peakVal, pProp)
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
             else (np.asarray(overrideLen) / st[1]))[:maxCount]
            for (tIdx, overrideLen, maxCount) in zip((0, 1), (args.offLen, args.onLen), (3, 2)))
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
              ' '.join(f'{i * st[1]:.3g}s' for i in durList[1]),
              '' if args.onLen is None else '(overridden)')
        print('off',
              ' '.join(f'{i * st[1]:.3g}s' for i in durList[0]),
              '' if args.offLen is None else '(overridden)')
    for i in (0, 1):
        durList[i] = np.hstack(((0,), durList[i]))
    # decoding
    sigBuff = list()
    decRes = list()
    startTime = None
    for i, (sigType, sigDur) in enumerate(valGp):
        currTime += sigDur
        durIdx = int(np.abs(durList[1 if sigType else 0] - sigDur).argmin())
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
            sym = MCD.reverse_dict.get(sig, '{' + sig + '}')
            assert startTime is not None
            decRes.append((i - 1, (startTime, currTime - sigDur), sig, sym))
            startTime = None
            if durIdx == 3:
                # long pause, space
                decRes.append((i, (currTime - sigDur, currTime), 'PAUSE', ' '))
    if len(sigBuff) != 0:
        sig = ''.join(sigBuff)
        sym = MCD.reverse_dict.get(sig, '{' + sig + '}')
        assert startTime is not None
        decRes.append((len(valGp) - 1, (startTime, currTime), sig, sym))
    if args.verbose >= 2:
        maxSigLen = max(len(p[2]) for p in decRes)
        maxIdxLen = len(str(len(valGp)))
        print('Decoded signal:')
        for idx, tp, sig, msg in decRes:
            t0 = timedelta(seconds=tp[0] * st[1])
            t1 = timedelta(seconds=tp[1] * st[1])
            print(str(idx).ljust(maxIdxLen),
                  f'{str(t0)[:-4] if t0.microseconds != 0 else str(t0)}',
                  '-',
                  f'{str(t1)[:-4] if t1.microseconds != 0 else str(t1)}',
                  sig.ljust(maxSigLen),
                  msg)
    print(''.join(p[-1] for p in decRes))

if __name__ == '__main__':
    main()

