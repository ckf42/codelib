from argparse import ArgumentParser, Namespace
from pathlib import Path
from itertools import groupby
from datetime import timedelta
import numpy as np
from scipy.signal import welch, stft, find_peaks
from scipy.io import wavfile
import MorseCodeDict as MCD

def main():
    parser = ArgumentParser(
            epilog="Work best on consistent intervals and without noise. "
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
            "If less than 2 lengths are specified, "
            "will attempt to fill up the missing lengths "
            "with the (1, 3) pattern")
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
            "will attempt to fill up the missing lengths "
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
        wfq1, Pxx1 = welch(xNormalized, sampleRate, nperseg=args.nperseg, average='mean')
        wfq2, Pxx2 = welch(xNormalized, sampleRate, nperseg=args.nperseg, average='median')
        (wfq, Pxx) = (wfq1, Pxx1) if Pxx1.max() >= Pxx2.max() else (wfq1, Pxx2)
        freq = wfq[Pxx.argmax()]
        if args.verbose:
            print(f'{freq=:.2f}')
    elif args.verbose:
        print(f'{freq=} (overridden)')
    assert freq is not None
    # convert to digital
    fq, st, Zxx = stft(xNormalized, sampleRate, nperseg=args.nperseg)
    fqp = np.abs(Zxx)[np.argmin(np.square(fq - freq)), :]
    valGp = list((k, len(tuple(v))) for k, v in groupby(fqp >= np.mean(fqp)))
    currTime = 0
    if not valGp[0][0]:
        currTime = valGp[0][1]
        valGp.pop(0)
    if not valGp[-1][0]:
        valGp.pop()
    if args.verbose >= 2:
        print(f'consecutive signal count={len(valGp)}')
        print(f'unit len={st[1]:.3g}s')
    # find signal lengths
    onHist = np.histogram(tuple(v for k, v in valGp if k), bins='auto')
    offHist = np.histogram(tuple(v for k, v in valGp if not k), bins='auto')
    offPeaks = find_peaks(offHist[0], prominence=1)
    durList = [
            (np.asarray(sorted(((offHist[1][1:] + offHist[1][:-1]) / 2)\
                    [offPeaks[0][np.argsort(offPeaks[1]['prominences'])[-3:]]]))
             if args.offLen is None
             else np.asarray(args.offLen) / st[1]),
            (np.asarray(sorted(((onHist[1][1:] + onHist[1][:-1]) / 2)\
                    [np.argpartition(onHist[0], -2)[-2:]]))
             if args.onLen is None
             else np.asarray(args.onLen) / st[1])
    ]
    assert len(durList[1]) >= 2, "Unable to determine unit signal length"
    if len(durList[0]) == 0:
        # fail to find peak, fallback with sorting
        offPeakIdx = np.argpartition(offHist[0], -3)[-1:-4:-1]
        durList[0] = ((offHist[1][1:] + offHist[1][:-1]) / 2)\
                [offPeakIdx[offHist[0][offPeakIdx] != 0]]
    if len(durList[0]) == 0:
        # still fail to find peak, fallback with signal length
        durList[0] = np.asarray(tuple(i * durList[1][1] for i in (1, 3, 7)))
    for i in (0, 1):
        durList[i] = np.hstack(((0,), durList[i]))
    if args.verbose >= 2:
        print('characteristic lengths:')
        print('on',
              ' '.join(f'{i * st[1]:.3g}s' for i in durList[1][1:]),
              '' if args.onLen is None else '(overridden)')
        print('off',
              ' '.join(f'{i * st[1]:.3g}s' for i in durList[0][1:]),
              '' if args.offLen is None else '(overridden)')
    # decoding
    sigBuff = list()
    decRes = list()
    startTime = None
    for i in range(len(valGp)):
        (sigType, sigDur) = valGp[i]
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
            m1 = timedelta(seconds=tp[0] * st[1])
            m2 = timedelta(seconds=tp[1] * st[1])
            print(str(idx).ljust(maxIdxLen),
                  f'{str(m1)[:-4] if m1.microseconds != 0 else str(m1)}',
                  '-',
                  f'{str(m2)[:-4] if m2.microseconds != 0 else str(m2)}',
                  sig.ljust(maxSigLen),
                  msg)
    print(''.join(p[-1] for p in decRes))

if __name__ == '__main__':
    main()

