# TODO no numpy as dependency
# TODO higher width than float32

import pyaudio as _pa
import numpy as _np
import itertools as _it
from numbers import Number as _numClass


class AudioOutputSignal:
    _genObj = None
    _aoObj = None
    isInEffect = True

    def __init__(self, gen, aoObj=None):
        self._genObj = gen
        self._aoObj = aoObj

    @classmethod
    def fromNpArray(cls, npArray, bufferSize=4096):
        if npArray.dtype != _np.float32:
            npArray = npArray.astype(_np.float32)
        if bufferSize is None:
            bufferSize = len(npArray)
        nPieces = len(npArray) // bufferSize
        arrLen = len(npArray)
        return cls((npArray[bIdx * bufferSize:min((bIdx + 1) * bufferSize,
                                                  arrLen)]
                    for bIdx in range(nPieces)))

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
            nPieces, nRemain = divmod(totalSamples, bufferSize)
            return cls((ampFunc_formatted(
                _np.arange(bIdx * bufferSize,
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

    def toNpArray(self, frameLimit=4096):
        return _np.hstack(tuple(self.keepTime(timeToKeep=1.,
                                              sampleRate=frameLimit,
                                              aoObj=None)._genObj))

    def join(self, *sigObj):
        if len(sigObj) == 0:
            return self
        elif len(sigObj) == 1:
            sigObj = sigObj[0]
            self.isInEffect = False
            sigObj.isInEffect = False
            return self.__class__(_it.chain(self._genObj, sigObj._genObj),
                                  aoObj=self._aoObj)
        else:
            return self.join(sigObj[0]).join(*(sigObj[1:]))

    def damping(self, dampingFactor=1, dampingMethod='exp',
                tol=None, stopBelowTol=False,
                sampleRate=48000, aoObj=None):
        self.isInEffect = False
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

        def _dampedAmp(_gen):
            blockOffset = 0
            for amp in _gen:
                blockLen = len(amp)
                if dampingMethod(blockOffset / sampleRate) < tol:
                    if stopBelowTol:
                        return
                    yield _np.zeros((blockLen, ))
                else:
                    damper = dampingMethod(_np.arange(blockOffset,
                                                      blockOffset + blockLen)
                                           / sampleRate)
                    yield _np.where(damper < tol, 0, amp * damper)
                blockOffset += blockLen

        return self.__class__(_dampedAmp(self._genObj),
                              aoObj=self._aoObj)

    def ampModify(self, ampFunc):
        self.isInEffect = False
        return self.__class__(map(_np.vectorize(ampFunc),
                                  self._genObj),
                              aoObj=self._aoObj)

    @staticmethod
    def _elementOpOnBuffers(gen0, gen1, npVectFunc):
        buf = [_np.zeros(0), _np.zeros(0)]
        gen1IsEmpty = False
        while not gen1IsEmpty:
            buf[0] = next(gen0, None)
            if buf[0] is None:
                break
            while len(buf[1]) < len(buf[0]):
                nextBuf = next(gen1, None)
                if nextBuf is None:
                    gen1IsEmpty = True
                    break
                buf[1] = _np.hstack((buf[1], nextBuf))
            if gen1IsEmpty:
                break
            yield npVectFunc(buf[0], buf[1][:len(buf[0])])
            buf[1] = buf[1][len(buf[0]):]
        if gen1IsEmpty:
            bufLen = min(len(buf[0]), len(buf[1]))
            yield npVectFunc(buf[0][:bufLen], buf[1][:bufLen])

    def elementwiseOp(self, secondSigObj, ampFunc):
        if secondSigObj.__class__ is not AudioOutputSignal:
            raise ValueError("Not a signal class")
        self.isInEffect = False
        secondSigObj.isInEffect = False
        ampFunc = _np.vectorize(ampFunc)
        return self.__class__(self._elementOpOnBuffers(self._genObj,
                                                       secondSigObj._genObj,
                                                       ampFunc),
                              aoObj=self._aoObj)

    def add(self, *signalObj, doAverage=True):
        if len(signalObj) == 0:
            return self
        else:
            n = len(signalObj) + 1
            return self.elementwiseOp(signalObj[0].add(*signalObj[1:],
                                                       doAverage=False),
                                      lambda x, y: (x + y) / (n
                                                              if doAverage
                                                              else 1))

    def __add__(self, secondSigObj):
        if isinstance(secondSigObj, _numClass):
            return self.ampModify(lambda x: x + secondSigObj)
        else:
            return self.add(secondSigObj, doAverage=False)

    def __radd__(self, secondSigObj):
        return self.__add__(secondSigObj)

    @classmethod
    def sum(cls, *signalObj, doAverage=False):
        if len(signalObj) == 0:
            return cls.silentSignal(duration=None)
        else:
            return signalObj[0].add(*signalObj[1:], doAverage=doAverage)

    def mul(self, *signalObj):
        if len(signalObj) == 0:
            return self
        else:
            return self.elementwiseOp(signalObj[0].mul(*signalObj[1:]),
                                      lambda x, y: x * y)

    def __mul__(self, secondSigObj):
        if isinstance(secondSigObj, _numClass):
            return self.ampModify(lambda x: x * secondSigObj)
        return self.mul(secondSigObj)

    def __rmul__(self, secondSigObj):
        return self.__mul__(secondSigObj)

    @classmethod
    def prod(cls, *signalObj):
        if len(signalObj) == 0:
            return cls.fromAmpFunc(lambda x: 1, None)
        else:
            return signalObj[0].mul(*signalObj[1:])

    def enforceBufferSize(self, bufferSize=4096):
        self.isInEffect = False
        if bufferSize is None:
            arr = self.toNpArray()
            return self.__class__.fromNpArray(arr, bufferSize=len(arr))

        def _enforceBufSize(_gen):
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
        return self.__class__(_enforceBufSize(self._genObj),
                              aoObj=self._aoObj)

    def play(self, playerAO=None,
             keepActivate=True, volume=1., forceAsTwoChannel=False):
        if playerAO is None:
            playerAO = self._aoObj
        if playerAO is None:
            raise ValueError("No AudioOutputInterface object given")
        else:
            playerAO.play(self,
                          keepActivate=keepActivate,
                          volume=volume,
                          forceAsTwoChannel=forceAsTwoChannel)

    def skipTime(self, timeToSkip=0.,
                 sampleRate=48000, aoObj=None):
        if timeToSkip <= 0:
            return self
        if aoObj is not None:
            sampleRate = aoObj.sampleRate
        framesToSkip = int(sampleRate * timeToSkip)
        self.isInEffect = False

        def _skip(_gen):
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
        return self.__class__(_skip(self._genObj), aoObj=self._aoObj)

    def keepTime(self, timeToKeep=0.,
                 sampleRate=48000, aoObj=None):
        self.isInEffect = False
        if timeToKeep < 0:
            return self
        if aoObj is not None:
            sampleRate = aoObj.sampleRate
        framesToKeep = int(sampleRate * timeToKeep)

        def _keep(_gen):
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
        return self.__class__(_keep(self._genObj), aoObj=self._aoObj)

    @classmethod
    def fromFourier(cls, ampList, freqList, initPhaseList=0.,
                    duration=1., doL1Normalize=True,
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
                initPhaseList = tuple(initPhaseList
                                      for _ in range(len(ampList)))
            if doL1Normalize:
                ampSum = _np.sum(_np.abs(ampList))
                ampList = list(amp / ampSum for amp in ampList)
            return cls.sum(*(cls.sineWave(frequency=freq,
                                          duration=duration,
                                          amplitude=amp,
                                          initPhase=initPhase,
                                          bufferSize=bufferSize,
                                          sampleRate=sampleRate,
                                          aoObj=aoObj)
                             for (freq, amp, initPhase)
                             in zip(freqList, ampList, initPhaseList)),
                           doAverage=False)

    def clip(self):
        self.isInEffect = False
        return self.__class__((amp.clip(-1., 1.)
                               for amp
                               in self._gen),
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

    def _ensureGen(self, obj):
        if obj.__class__ is AudioOutputSignal:
            if not obj.isInEffect:
                raise ValueError("Signal has no valid data")
            obj.isInEffect = False
            return obj._genObj
        elif obj.__class__ is _np.ndarray:
            return AudioOutputSignal.fromNpArray(obj,
                                                 bufferSize=self.bufferSize
                                                 )._genObj
        elif obj.__class__.__name__ == 'generator':
            return obj
        else:
            raise ValueError(f"Unknown signal type {obj.__class__.__name__}")

    def play(self, signal, signalR=None,
             keepActivate=True, volume=1,
             forceAsTwoChannel=False):
        if isinstance(signal, tuple) and len(signal) >= 2:
            signal, signalR = signal[0], signal[1]
        signal = self._ensureGen(signal)
        if self._channel == 2 and not forceAsTwoChannel:
            if signalR is None or not signalR.isInEffect:
                signal = (_np.vstack((sig, sig)).T.ravel()
                          for sig in signal)
            else:
                signalR = self._ensureGen(signalR)
                signal = (_np.vstack((signalPair[0][:maxLen],
                                      signalPair[1][:maxLen])).T.ravel()
                          for signalPair in zip(signal, signalR)
                          for maxLen in (len(min(signalPair, key=len)), ))
        if self._stream.is_stopped():
            self._stream.start_stream()
        for buf in signal:
            buf = buf.clip(-1., 1.) * volume
            self._stream.write(buf.astype(_np.float32,
                                          casting='same_kind',
                                          copy=False).tobytes())
        if not keepActivate:
            self._stream.stop_stream()

    def clearBuf(self, duration=0.1):
        self.play(AudioOutputSignal.silentSignal(duration=duration,
                                                 aoObj=self),
                  keepActivate=False)


if __name__ == '__main__':
    ao = AudioOutputInterface()
    aos = AudioOutputSignal
