# TODO no numpy as dependency
# TODO higher width than float32

import pyaudio as _pa
import numpy as _np
import itertools as _it
from numbers import Number as _numClass


class AudioOutputSignal:
    _genObj = None
    _aoObj = None
    _isInEffect = True

    def __init__(self, gen, aoObj=None):
        self._genObj = gen
        self._aoObj = aoObj

    def __next__(self):
        res = next(self._genObj, None)
        if res is None:
            self._isInEffect = False
            raise StopIteration
        else:
            return res

    def __iter__(self):
        self._isInEffect = False
        return self._genObj

    @property
    def isInEffect(self):
        return self._isInEffect

    @isInEffect.setter
    def isInEffect(self, newFlag):
        raise ValueError("Cannot modify the property")

    @classmethod
    def fromNpArray(cls, npArray, bufferSize=4096, aoObj=None):
        if npArray.dtype != _np.float32:
            npArray = npArray.astype(_np.float32)
        if aoObj is not None:
            bufferSize = aoObj.bufferSize
        elif bufferSize is None:
            bufferSize = len(npArray)
        arrLen = len(npArray)
        nPieces = (arrLen + bufferSize - 1) // bufferSize
        return cls((npArray[bIdx * bufferSize:min((bIdx + 1) * bufferSize,
                                                  arrLen)]
                    for bIdx in range(nPieces)),
                   aoObj=aoObj)

    @classmethod
    def fromAmpFunc(cls, ampFunc, duration=1.,
                    bufferSize=4096, sampleRate=48000, aoObj=None):
        if aoObj is not None:
            bufferSize = aoObj.bufferSize
            sampleRate = aoObj.sampleRate
        ampFunc_formatted = _np.vectorize(ampFunc)
        if duration is not None:
            totalSamples = int(duration * sampleRate)
            if bufferSize is None:
                bufferSize = totalSamples
            nPieces = (totalSamples + bufferSize - 1) // bufferSize
            return cls(
                (ampFunc_formatted(_np.arange(bIdx * bufferSize,
                                              min((bIdx + 1) * bufferSize,
                                                  totalSamples))
                                   / sampleRate)
                 for bIdx in range(nPieces)),
                aoObj=aoObj)
        else:
            if bufferSize is None:
                raise ValueError("No bufferSize provided")
            return cls((ampFunc_formatted(_np.arange(bIdx * bufferSize,
                                                     (bIdx + 1) * bufferSize)
                                          / sampleRate)
                        for bIdx in _it.count()),
                       aoObj=aoObj)

    @classmethod
    def fromFreqFunc(cls, freqFunc, duration=1., amplitude=1., initPhase=0.,
                     bufferSize=4096, sampleRate=48000, aoObj=None):
        if aoObj is not None:
            bufferSize = aoObj.bufferSize
            sampleRate = aoObj.sampleRate
        return cls.fromAmpFunc(ampFunc=lambda t: amplitude
                               * _np.sin(2 * _np.pi * t
                                         * freqFunc(t)
                                         + initPhase),
                               duration=duration,
                               bufferSize=bufferSize,
                               sampleRate=sampleRate,
                               aoObj=aoObj)

    @classmethod
    def silentSignal(cls, duration=1.,
                     bufferSize=4096, sampleRate=48000, aoObj=None):
        return cls.fromAmpFunc(ampFunc=lambda t: 0.,
                               duration=duration,
                               bufferSize=bufferSize,
                               sampleRate=sampleRate,
                               aoObj=aoObj)

    @classmethod
    def sineWave(cls, frequency, duration=1., amplitude=1., initPhase=0.,
                 bufferSize=4096, sampleRate=48000, aoObj=None):
        return cls.fromFreqFunc(freqFunc=lambda t: frequency,
                                duration=duration,
                                amplitude=amplitude,
                                initPhase=initPhase,
                                bufferSize=bufferSize,
                                sampleRate=sampleRate,
                                aoObj=aoObj)

    @classmethod
    def unitSound(cls, frequency, aoObj):
        return cls.sineWave(frequency=frequency,
                            duration=1. / frequency,
                            aoObj=aoObj)

    @classmethod
    def squareWave(cls, frequency, duration=1., amplitude=1.,
                   bufferSize=4096, sampleRate=48000, aoObj=None):
        return cls.fromAmpFunc(ampFunc=lambda t:
                               amplitude * _np.sign(
                                   _np.sin(2 * _np.pi
                                           * frequency * t)),
                               duration=duration,
                               bufferSize=bufferSize,
                               sampleRate=sampleRate,
                               aoObj=aoObj)

    @classmethod
    def sawWave(cls, frequency, duration=1., amplitude=1.,
                bufferSize=4096, sampleRate=48000, aoObj=None):
        return cls.fromAmpFunc(ampFunc=lambda t:
                               amplitude * (_np.modf(
                                   t * frequency)[0] * 2 - 1),
                               duration=duration,
                               bufferSize=bufferSize,
                               sampleRate=sampleRate,
                               aoObj=aoObj)

    @classmethod
    def triangleWave(cls, frequency, duration=1., amplitude=1.,
                     bufferSize=4096, sampleRate=48000, aoObj=None):
        return cls.fromAmpFunc(ampFunc=lambda t: amplitude
                               * (2 * _np.abs(2 * _np.modf(
                                   t * frequency)[0] - 1) - 1),
                               duration=duration,
                               bufferSize=bufferSize,
                               sampleRate=sampleRate,
                               aoObj=aoObj)

    def toNpArray(self, frameLimit=None, getLenOnly=False):
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        if getLenOnly:
            return len(self.toNpArray(frameLimit=frameLimit,
                                      getLenOnly=False))
        self._isInEffect = False
        # default frameLimit: 60 seconds
        if frameLimit is None:
            frameLimit = 60 * (48000
                               if self._aoObj is None
                               else self._aoObj.sampleRate)
        sampleRate = 48000
        if self._aoObj is not None:
            sampleRate = self._aoObj.sampleRate
        # extract np array till the end if frameLimit is negative
        if frameLimit < 0:
            return _np.hstack(tuple(self._genObj))
        else:
            return _np.hstack(tuple(
                self.keepTime(timeToKeep=frameLimit / sampleRate,
                              sampleRate=sampleRate)._genObj))

    def join(self, *sigObj):
        if len(sigObj) == 0:
            return self
        elif len(sigObj) == 1:
            sigObj = sigObj[0]
            self._isInEffect = False
            sigObj._isInEffect = False
            return self.__class__(_it.chain(self._genObj,
                                            sigObj._genObj),
                                  aoObj=self._aoObj)
        else:
            return self.join(sigObj[0]).join(*(sigObj[1:]))

    @classmethod
    def joinSignals(cls, *sigObj):
        if len(sigObj) == 0:
            return cls.silentSignal(duration=None)
        else:
            return sigObj[0].join(*sigObj[1:])

    def damping(self, dampingFactor=1, dampingMethod='exp',
                tol=None, stopBelowTol=False,
                sampleRate=48000, aoObj=None):
        self._isInEffect = False
        if aoObj is not None:
            sampleRate = aoObj.sampleRate
        if tol is None:
            tol = -1
            stopBelowTol = False
        if not callable(dampingMethod):
            dampingFuncDict = {
                'exp': lambda t: _np.exp(-dampingFactor * t),
                'linear': lambda t: _np.reciprocal(1 + dampingFactor * t),
                'quad': lambda t: _np.reciprocal(1 + (dampingFactor * t) ** 2),
                'cubic': lambda t: _np.reciprocal(1 + (dampingFactor * t) ** 3)
            }
            dampingMethod = dampingFuncDict.get(dampingMethod.lower(),
                                                dampingFuncDict['exp'])

        def _damping_gen(_gen):
            blockOffset = 0
            for amp in _gen:
                blockLen = len(amp)
                if dampingMethod(blockOffset / sampleRate) < tol:
                    if stopBelowTol:
                        return
                    yield _np.zeros(blockLen)
                else:
                    damper = dampingMethod(_np.arange(blockOffset,
                                                      blockOffset + blockLen)
                                           / sampleRate)
                    yield _np.where(damper < tol, 0, amp * damper)
                blockOffset += blockLen

        return self.__class__(_damping_gen(self._genObj),
                              aoObj=self._aoObj)

    def cutoff(self, chunkTotalVarTol=1e-3):
        self._isInEffect = False

        def _cutoff_gen(_gen):
            for chunk in _gen:
                if len(chunk) == 1 and _np.abs(chunk[0]) < chunkTotalVarTol:
                    return
                elif _np.sum(_np.abs(_np.diff(chunk))) < chunkTotalVarTol:
                    return
                else:
                    yield chunk
        return self.__class__(_cutoff_gen(self._genObj),
                              aoObj=self._aoObj)

    def ampModify(self, ampFunc):
        self._isInEffect = False
        return self.__class__(map(_np.vectorize(ampFunc),
                                  self._genObj),
                              aoObj=self._aoObj)

    def elementwiseOp(self, secondSigObj, ampFunc):
        if not isinstance(secondSigObj, AudioOutputSignal):
            raise ValueError(
                f"Not a signal class ({secondSigObj.__class__.__name__})"
            )
        self._isInEffect = False
        secondSigObj._isInEffect = False
        ampFunc = _np.vectorize(ampFunc)

        def _elementwiseOp_gen(gen0, gen1, npVectFunc):
            buf = [_np.zeros(0), _np.zeros(0)]
            gen1IsEmpty = False
            while not gen1IsEmpty:
                buf[0] = next(gen0, None)
                if buf[0] is None:
                    break
                while len(buf[0]) > len(buf[1]):
                    nextBuf = next(gen1, None)
                    if nextBuf is None:
                        gen1IsEmpty = True
                        break
                    buf[1] = _np.hstack((buf[1], nextBuf))
                if gen1IsEmpty:
                    buf[0] = buf[0][:len(buf[1])]
                yield npVectFunc(buf[0], buf[1][:len(buf[0])])
                buf[1] = buf[1][len(buf[0]):]

        return self.__class__(_elementwiseOp_gen(self._genObj,
                                                 secondSigObj._genObj,
                                                 ampFunc),
                              aoObj=self._aoObj)

    def add(self, *signalObj, average=False):
        if len(signalObj) == 0:
            return self
        elif len(signalObj) == 1:
            if isinstance(signalObj[0], _numClass):
                return self.ampModify(lambda amp:
                                      (amp + signalObj[0]) / (
                                          2 if average else 1))
            else:
                return self.elementwiseOp(signalObj[0],
                                          lambda x, y:
                                          (x + y) / (2 if average else 1))
        elif average:
            n = len(signalObj) + 1
            return self.mul(1 / n).add(*(sig.mul(1 / n)
                                         for sig in signalObj),
                                       average=False)

        else:
            return self.add(signalObj[0],
                            average=False).add(*signalObj[1:],
                                               average=False)

    def __add__(self, secondSigObj):
        return self.add(secondSigObj, average=False)

    def __radd__(self, secondSigObj):
        return self.__add__(secondSigObj)

    @classmethod
    def sum(cls, *signalObj, average=False):
        if len(signalObj) == 0:
            return cls.silentSignal(duration=None)
        else:
            return signalObj[0].add(*signalObj[1:], average=average)

    def mul(self, *signalObj):
        if len(signalObj) == 0:
            return self
        elif len(signalObj) == 1:
            if isinstance(signalObj[0], _numClass):
                return self.ampModify(lambda amp: amp * signalObj[0])
            else:
                return self.elementwiseOp(signalObj[0],
                                          lambda x, y: x * y)
        else:
            return self.mul(signalObj[0]).mul(*signalObj[1:])

    def __mul__(self, secondSigObj):
        return self.mul(secondSigObj)

    def __rmul__(self, secondSigObj):
        return self.__mul__(secondSigObj)

    @classmethod
    def prod(cls, *signalObj):
        if len(signalObj) == 0:
            return cls.fromAmpFunc(lambda x: 1, None)
        else:
            return signalObj[0].mul(*signalObj[1:])

    def enforceBufferSize(self, bufferSize=4096, frameLimit=None):
        self._isInEffect = False
        if bufferSize is None:
            arr = self.toNpArray(frameLimit=frameLimit)
            return self.__class__.fromNpArray(arr, bufferSize=len(arr))

        def _enforceBufferSize_gen(_gen):
            buf = _np.zeros(0)
            while True:
                nextBuf = next(_gen, None)
                if nextBuf is None:
                    break
                buf = _np.hstack((buf, nextBuf))
                while len(buf) >= bufferSize:
                    yield buf[:bufferSize]
                    buf = buf[bufferSize:]
            if len(buf) > 0:
                yield buf
        return self.__class__(_enforceBufferSize_gen(self._genObj),
                              aoObj=self._aoObj)

    def play(self, playerAO=None,
             keepActive=True, volume=1.,
             forceAsTwoChannel=False, forcePrecompute=False,
             smoothClip=False):
        if playerAO is None:
            playerAO = self._aoObj
        if playerAO is None:
            raise ValueError("No AudioOutputInterface object given")
        else:
            playerAO.play(self,
                          keepActive=keepActive,
                          volume=volume,
                          forceAsTwoChannel=forceAsTwoChannel,
                          forcePrecompute=forcePrecompute,
                          smoothClip=smoothClip)

    def skipTime(self, timeToSkip=0.,
                 sampleRate=48000):
        if timeToSkip <= 0:
            return self
        if self._aoObj is not None:
            sampleRate = self._aoObj.sampleRate
        framesToSkip = int(sampleRate * timeToSkip)
        self._isInEffect = False

        def _skipTime_gen(_gen):
            skippedFrames = 0
            while True:
                buf = next(_gen, None)
                if buf is None:
                    break
                if skippedFrames + len(buf) > framesToSkip:
                    yield buf[framesToSkip - skippedFrames:]
                    break
                else:
                    skippedFrames += len(buf)
            yield from _gen
        return self.__class__(_skipTime_gen(self._genObj),
                              aoObj=self._aoObj)

    def keepTime(self, timeToKeep=0.,
                 sampleRate=48000):
        self._isInEffect = False
        if timeToKeep < 0:
            return self
        if self._aoObj is not None:
            sampleRate = self._aoObj.sampleRate
        framesToKeep = int(sampleRate * timeToKeep)

        def _keepTime_gen(_gen):
            keepedFrames = 0
            while True:
                buf = next(_gen, None)
                if buf is None:
                    break
                if keepedFrames + len(buf) > framesToKeep:
                    yield buf[:framesToKeep - keepedFrames]
                    break
                else:
                    yield buf
                    keepedFrames += len(buf)
        return self.__class__(_keepTime_gen(self._genObj),
                              aoObj=self._aoObj)

    @classmethod
    def fromFourier(cls, ampList, freqList, initPhaseList=0.,
                    duration=1., ampWeightNormalize=True,
                    bufferSize=4096, sampleRate=48000, aoObj=None):
        if len(ampList) != len(freqList):
            raise ValueError("the two lists have different lengths")
        if len(ampList) == 0:
            return cls.silentSignal(duration=duration,
                                    bufferSize=bufferSize,
                                    sampleRate=sampleRate,
                                    aoObj=aoObj)
        else:
            if isinstance(initPhaseList, _numClass):
                initPhaseList = [initPhaseList] * len(ampList)
            if ampWeightNormalize:
                ampSum = _np.sum(_np.abs(ampList))
                ampList = list(amp / ampSum for amp in ampList)
            return cls.fromAmpFunc(
                ampFunc=lambda t: sum(
                    amp * _np.sin(2 * _np.pi * freq * t
                                  + initPhase)
                    for (amp, freq, initPhase)
                    in zip(ampList, freqList, initPhaseList)),
                duration=duration,
                bufferSize=bufferSize,
                sampleRate=sampleRate,
                aoObj=aoObj)

    def clip(self):
        self._isInEffect = False
        return self.__class__((amp.clip(-1., 1.)
                               for amp
                               in self._gen),
                              aoObj=self._aoObj)

    def repeat(self, repeatTimes=1, eachDuration=1., patchLenWithZero=False,
               sampleRate=48000):
        if self._aoObj is not None:
            sampleRate = self._aoObj.sampleRate
        eachBlockLen = int(eachDuration * sampleRate)
        signalArr = self.toNpArray(frameLimit=eachBlockLen)
        if patchLenWithZero and len(signalArr) < eachBlockLen:
            signalArr = _np.hstack((signalArr,
                                   _np.zeros(eachBlockLen - len(signalArr))))
        if repeatTimes is None:
            return self.__class__(_it.repeat(signalArr), aoObj=self._aoObj)
        else:
            return self.__class__(_it.repeat(signalArr, repeatTimes),
                                  aoObj=self._aoObj)

    def echo(self, delayTime=0.5, echoAmp=0.7, infEcho=False,
             sampleRate=48000):
        if self._aoObj is not None:
            sampleRate = self._aoObj.sampleRate
        delayFrame = int(sampleRate * delayTime)

        def _echo_gen(_gen):
            memBuf = _np.zeros(delayFrame)
            while True:
                nextBuf = next(_gen, None)
                if nextBuf is None:
                    nextBuf = _np.zeros(delayFrame)
                elif len(nextBuf) < delayFrame:
                    nextBuf = _np.hstack((nextBuf,
                                          _np.zeros(delayFrame - len(nextBuf))
                                          ))
                yield nextBuf + memBuf * echoAmp
                if infEcho:
                    memBuf = nextBuf + memBuf * echoAmp
                else:
                    memBuf = nextBuf

        return self.__class__(
            _echo_gen(self.enforceBufferSize(bufferSize=delayFrame)._genObj),
            aoObj=self._aoObj)


class AudioOutputInterface:
    _paObj = None
    _stream = None
    _sr = None
    _channel = None
    _buffSize = None

    def _init_stream(self):
        if self._stream is not None:
            self._ensureStreamClosed()
        self._stream = self._paObj.open(rate=self._sr,
                                        channels=self._channel,
                                        format=_pa.paFloat32,
                                        output=True)

    def _ensureStreamClosed(self):
        if self._stream is not None:
            if self._stream.is_active():
                self._stream.stop_stream()
            self._stream.close()

    def __del__(self):
        self._ensureStreamClosed()
        self._paObj.terminate()

    @staticmethod
    def _checkParaValid(paraName, paraVal):
        if paraName == 'sampleRate':
            if not isinstance(paraVal, int) or paraVal <= 0:
                raise ValueError("SampleRate must be positive integer")
        elif paraName == 'channels':
            if paraVal not in (1, 2):
                raise ValueError("Channel count must be 1 or 2")
        elif paraName == 'bufferSize':
            if not isinstance(paraVal, int) or paraVal <= 0:
                raise ValueError("BufferSize must be positive integer")
        else:
            raise ValueError(f"Invalid parameter name {paraName}")

    @property
    def sampleRate(self):
        return self._sr

    @sampleRate.setter
    def sampleRate(self, sampleRate):
        self._checkParaValid('sampleRate', sampleRate)
        if sampleRate != self._sr:
            self._sr = sampleRate
            self._init_stream()

    @property
    def channels(self):
        return self._channel

    @channels.setter
    def channels(self, channels):
        self._checkParaValid('channels', channels)
        if channels != self._channel:
            self._channel = channels
            self._init_stream()

    @property
    def bufferSize(self):
        return self._buffSize

    @bufferSize.setter
    def bufferSize(self, bufferSize):
        self._checkParaValid('bufferSize', bufferSize)
        self._buffSize = bufferSize

    def __init__(self,
                 sampleRate=48000,
                 channels=2,
                 bufferSize=4096):
        self._checkParaValid('sampleRate', sampleRate)
        self._sr = sampleRate
        self._checkParaValid('channels', channels)
        self._channel = channels
        self._checkParaValid('bufferSize', bufferSize)
        self._buffSize = bufferSize
        self._paObj = _pa.PyAudio()
        self._init_stream()

    def _ensureSigGen(self, obj, forcePrecompute):
        if obj.__class__.__name__ == 'generator':
            obj = AudioOutputSignal(obj)
        if isinstance(obj, AudioOutputSignal):
            if not obj._isInEffect:
                raise ValueError("Signal has no valid data")
            if forcePrecompute is None:
                forcePrecompute = True
            if isinstance(forcePrecompute, bool):
                if not forcePrecompute:
                    obj._isInEffect = False
                    return obj.enforceBufferSize(
                        bufferSize=self.bufferSize)._genObj
                else:
                    forcePrecompute = 60.
            obj = obj.toNpArray(frameLimit=forcePrecompute * self.bufferSize)
        if isinstance(obj, _np.ndarray):
            return AudioOutputSignal.fromNpArray(obj,
                                                 bufferSize=self.bufferSize
                                                 )._genObj
        else:
            raise ValueError(f"Unknown signal type {obj.__class__.__name__}")

    def play(self, signal, signalR=None,
             keepActive=True, volume=1.,
             forceAsTwoChannel=False, forcePrecompute=False,
             smoothClip=False):
        if isinstance(signal, tuple) \
                and len(signal) >= 2 \
                and self.channels == 2:
            signal, signalR = signal[0], signal[1]
        signal = self._ensureSigGen(signal, forcePrecompute)
        if self._channel == 2 and not forceAsTwoChannel:
            if signalR is None or not signalR._isInEffect:
                signal = (_np.vstack((sig, sig)).T.ravel()
                          for sig in signal)
            else:
                signalR = self._ensureSigGen(signalR, forcePrecompute)
                signal = (_np.vstack((signalPair[0][:maxLen],
                                      signalPair[1][:maxLen])).T.ravel()
                          for signalPair in zip(signal, signalR)
                          for maxLen in (len(min(signalPair, key=len)), ))
        if self._stream.is_stopped():
            self._stream.start_stream()
        for buf in signal:
            if smoothClip:
                buf = volume * (2 / (1 + _np.exp(-2 * buf)) - 1)
                # ~ 75% peak loss
            else:
                buf = buf.clip(-1., 1.) * volume
            self._stream.write(buf.astype(_np.float32,
                                          casting='same_kind',
                                          copy=False).tobytes())
        if not keepActive:
            self._stream.stop_stream()

    def playNpArray(self, npArray,
                    keepActive=True, volume=1., smoothClip=False):
        if isinstance(npArray, tuple) \
                and len(npArray) >= 2 \
                and self.channels == 2:
            if len(npArray[0]) != len(npArray[1]):
                raise ValueError("Input arrays are not of equal length")
            npArray = _np.vstack(npArray[0:2]).T.ravel()
        if not isinstance(npArray, _np.ndarray):
            raise ValueError("Input array not np ndarray")
        if smoothClip:
            npArray = (2 / (1 + _np.exp(-2 * npArray)) - 1) * volume
        else:
            npArray = npArray.clip(-1, 1) * volume
        self._stream.write(npArray.astype(_np.float32,
                                          casting='same_kind',
                                          copy=False).tobytes())
        if not keepActive:
            self._stream.stop_stream()

    def clearBuf(self, duration=0.1):
        self.play(AudioOutputSignal.silentSignal(duration=duration,
                                                 aoObj=self),
                  keepActive=False)


if __name__ == '__main__':
    ao = AudioOutputInterface()
    aos = AudioOutputSignal
