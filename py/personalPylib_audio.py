# if __name__ == '__main__':
#     exit()

# TODO no numpy as dependency
# TODO higher width than float32

import pyaudio as _pa
import numpy as _np
import itertools as _it


class AudioOutputSignal:
    _genObj = None
    _buffSize = None
    _aoObj = None
    isEffective = True

    def __init__(self, gen, bufferSize=None, aoObj=None):
        self._genObj = gen
        self._buffSize = bufferSize
        self._aoObj = aoObj

    @classmethod
    def fromNpArray(cls, npArray, bufferSize=4096):
        if npArray.dtype != _np.float32:
            npArray = npArray.astype(_np.float32)
        nPieces = len(npArray) // bufferSize
        arrLen = len(npArray)
        return cls((npArray[bIdx * bufferSize:min((bIdx + 1) * bufferSize,
                                                  arrLen)]
                    for bIdx in range(nPieces)),
                   bufferSize=bufferSize)

    @classmethod
    def fromAmpFunc(cls, ampFunc, duration=1.,
                    bufferSize=4096, sampleRate=48000, aoObj=None):
        if aoObj is not None:
            bufferSize = aoObj.bufferSize
            sampleRate = aoObj.sampleRate
        ampFunc_formatted = _np.vectorize(ampFunc)
        totalSamples = int(duration * sampleRate)
        nPieces, nRemain = divmod(totalSamples, bufferSize)
        return cls((ampFunc_formatted(_np.arange(bIdx * bufferSize,
                                                 min((bIdx + 1) * bufferSize,
                                                     totalSamples))
                                      / sampleRate)
                    for bIdx in range(nPieces)),
                   bufferSize=bufferSize,
                   aoObj=aoObj)

    @classmethod
    def fromFreqFunc(cls, freqFunc, duration=1., amplitude=1.,
                     bufferSize=4096, sampleRate=48000, aoObj=None):
        if aoObj is not None:
            bufferSize = aoObj.bufferSize
            sampleRate = aoObj.sampleRate
        return cls.fromAmpFunc(ampFunc=lambda t: amplitude
                               * _np.sin(2 * _np.pi * t * freqFunc(t)),
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
    def sineWave(cls, frequency, duration=1., amplitude=1.,
                 bufferSize=4096, sampleRate=48000, aoObj=None):
        return cls.fromFreqFunc(freqFunc=lambda t: frequency,
                                duration=duration,
                                amplitude=amplitude,
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

    def toNpArray(self):
        self.isEffective = False
        return _np.hstack(tuple(self._genObj))

    def join(self, secondSigObj):
        self.isEffective = False
        secondSigObj.isEffective = False
        return self.__class__(_it.chain(self._genObj, secondSigObj._genObj),
                              bufferSize=self._buffSize,
                              aoObj=self._aoObj)

    def damping(self, dampingFactor=1, dampingMethod='exp',
                tol=None, stopBelowTol=False,
                sampleRate=48000, aoObj=None):
        self.isEffective = False
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
                              bufferSize=self._buffSize,
                              aoObj=self._aoObj)

    def ampModify(self, ampFunc):
        self.isEffective = False
        return self.__class__(map(_np.vectorize(ampFunc),
                                  self._genObj),
                              bufferSize=self._buffSize,
                              aoObj=self._aoObj)

    @staticmethod
    def _elementOpOnBuffers(gen0, gen1, npVectFunc, buffSize):
        buf = [_np.zeros(0), _np.zeros(0)]
        someGenIsEmpty = False
        while not someGenIsEmpty:
            while len(buf[0]) < buffSize:
                nextBuf = next(gen0, None)
                if nextBuf is None:
                    someGenIsEmpty = True
                    break
                buf[0] = _np.hstack((buf[0], nextBuf))
            while len(buf[1]) < buffSize:
                nextBuf = next(gen1, None)
                if nextBuf is None:
                    someGenIsEmpty = True
                    break
                buf[1] = _np.hstack((buf[1], nextBuf))
            minBufLen = min(len(buf[0]), len(buf[1]))
            if minBufLen == 0:
                break
            yield npVectFunc(buf[0][:minBufLen], buf[1][:minBufLen])
            buf[0] = buf[0][minBufLen:]
            buf[1] = buf[1][minBufLen:]

    def elementwiseOp(self, secondSigObj, ampFunc):
        if secondSigObj.__class__ is not AudioOutputSignal:
            raise ValueError("Not a signal class")
        self.isEffective = False
        secondSigObj.isEffective = False
        ampFunc = _np.vectorize(ampFunc)
        return self.__class__(self._elementOpOnBuffers(self._genObj,
                                                       secondSigObj._genObj,
                                                       ampFunc,
                                                       self._buffSize),
                              bufferSize=self._buffSize,
                              aoObj=self._aoObj)

    def add(self, secondSigObj, doAverage=True):
        return self.elementwiseOp(secondSigObj,
                                  lambda x, y: (x + y) / 2
                                  if doAverage
                                  else _np.ndarray.__add__)

    def __add__(self, secondSigObj):
        return self.add(secondSigObj, doAverage=True)

    def __mul__(self, secondSigObj):
        from numbers import Number as _numClass
        if isinstance(secondSigObj, _numClass):
            return self.ampModify(lambda x: x * secondSigObj)
        return self.elementwiseOp(secondSigObj, lambda x, y: x * y)

    def __rmul__(self, secondSigObj):
        return self.__mul__(secondSigObj)

    def play(self, playerAO=None,
             keepActivate=True, ampScale=1., forceAsTwoChannel=False):
        if playerAO is None:
            playerAO = self._aoObj
        if playerAO is None:
            raise ValueError("No AudioOutputInterface object given")
        else:
            playerAO.play(self,
                          keepActivate=keepActivate,
                          ampScale=ampScale,
                          forceAsTwoChannel=forceAsTwoChannel)

    @classmethod
    def fromMandelbrotMap(cls, c, interpolFreq=440, bufferLimit=100,
                          bufferSize=4096, sampleRate=48000, aoObj=None):
        if c[0] ** 2 + c[1] ** 2 > 4:
            raise ValueError("Initial c is too far away from 0")

        def _mandelbrotIter(z):
            return (z[0] ** 2 - z[1] ** 2 + c[0], 2 * z[0] * z[1] + c[1])
        if aoObj is not None:
            bufferSize = aoObj.bufferSize
            sampleRate = aoObj.sampleRate
        totalInterpolSample = int(sampleRate / interpolFreq)

        def _mandelbrotYielder():
            bufferCounter = 0
            buf = _np.zeros(0)
            z = c
            znew = _mandelbrotIter(z)
            while znew[0] ** 2 + znew[1] ** 2 <= 4:
                buf = _np.hstack((buf,
                                  _np.vstack((_np.linspace(z[0] / 2,
                                                           znew[0] / 2,
                                                           totalInterpolSample,
                                                           endpoint=False),
                                              _np.linspace(z[1] / 2,
                                                           znew[1] / 2,
                                                           totalInterpolSample,
                                                           endpoint=False))
                                             ).T.ravel()
                                  ))
                while len(buf) >= bufferSize and bufferCounter < bufferLimit:
                    bufferCounter += 1
                    yield buf[:bufferSize]
                    buf = buf[bufferSize:]
                z = znew
                znew = _mandelbrotIter(z)
                if bufferCounter >= bufferLimit:
                    break
        return cls(_mandelbrotYielder(), bufferSize=bufferSize, aoObj=aoObj)


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

    @staticmethod
    def _ensureGen(obj):
        if obj.__class__ is AudioOutputSignal:
            return obj
        elif obj.__class__ is _np.ndarray:
            return AudioOutputSignal.fromNpArray(obj)
        else:
            raise ValueError(f"Unknown signal type {obj.__class__.__name__}")

    def play(self, signal, signalR=None,
             keepActivate=True, ampScale=1,
             forceAsTwoChannel=False):
        if isinstance(signal, tuple) and len(signal) >= 2:
            signal, signalR = signal[0], signal[1]
        signal = self._ensureGen(signal)
        if not signal.isEffective:
            raise ValueError("Signal has no valid data")
        signal.isEffective = False
        signal = signal._genObj
        if self._channel == 2 and not forceAsTwoChannel:
            if signalR is None or not signalR.isEffective:
                signal = (_np.vstack((sig, sig)).T.ravel()
                          for sig in signal)
            else:
                signalR = self._ensureGen(signalR)
                signalR.isEffective = False
                signalR = signalR._genObj
                signal = (_np.vstack((signalPair[0][:maxLen],
                                      signalPair[1][:maxLen])).T.ravel()
                          for signalPair in zip(signal, signalR)
                          for maxLen in (len(min(signalPair, key=len)), ))
        if self._stream.is_stopped():
            self._stream.start_stream()
        for buf in signal:
            buf = buf.clip(-1., 1.) * ampScale
            self._stream.write(buf.astype(_np.float32,
                                          casting='same_kind',
                                          copy=False).tobytes())
        if not keepActivate:
            self._stream.stop_stream()

    def clearBuf(self):
        self.play(AudioOutputSignal.silentSignal(duration=0.5, aoObj=self))
