# if __name__ == '__main__':
#     exit()

# TODO no numpy as dependency
# TODO higher width than float32
# TODO make signal class

import pyaudio as _pa
import numpy as _np
import itertools as _it


class AudioOutputSignal:
    _genObj = None

    def __init__(self, gen):
        self._genObj = gen

    @classmethod
    def fromNpArray(cls, npArray, bufferSize=4096):
        if npArray.dtype != _np.float32:
            npArray = npArray.astype(_np.float32)
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
        totalSamples = int(duration * sampleRate)
        nPieces, nRemain = divmod(totalSamples, bufferSize)
        return cls((ampFunc_formatted(_np.arange(bIdx * bufferSize,
                                                 min((bIdx + 1) * bufferSize,
                                                     totalSamples))
                                      / sampleRate)
                    for bIdx in range(nPieces)))

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
        return cls.signalByAmpFunc(ampFunc=lambda t:
                                   amplitude * _np.sign(
                                       _np.sin(2 * _np.pi
                                               * frequency * t)),
                                   duration=duration,
                                   amplitude=amplitude,
                                   bufferSize=bufferSize,
                                   sampleRate=sampleRate,
                                   aoObj=aoObj)

    @classmethod
    def sawWave(cls, frequency, duration=1., amplitude=1.,
                bufferSize=4096, sampleRate=48000, aoObj=None):
        return cls.signalByAmpFunc(ampFunc=lambda t:
                                   amplitude * (_np.modf(
                                       t * frequency)[0] * 2 - 1),
                                   duration=duration,
                                   amplitude=amplitude,
                                   bufferSize=bufferSize,
                                   sampleRate=sampleRate,
                                   aoObj=aoObj)

    @classmethod
    def triangleWave(cls, frequency, duration=1., amplitude=1.,
                     bufferSize=4096, sampleRate=48000, aoObj=None):
        return cls.signalByAmpFunc(ampFunc=lambda t: amplitude
                                   * (2 * _np.abs(2 * _np.modf(
                                       t * frequency)[0] - 1) - 1),
                                   duration=duration,
                                   amplitude=amplitude,
                                   bufferSize=bufferSize,
                                   sampleRate=sampleRate,
                                   aoObj=aoObj)

    def toNpArray(self):
        return _np.hstack(tuple(self._genObj))

    def join(self, secondSigObj):
        self = self.__class__(_it.chain(self._genObj, secondSigObj._genObj))
        return self

    def damping(self, dampingFactor=1, dampingMethod='exp',
                tol=None, stopBelowTol=False,
                sampleRate=48000, aoObj=None):
        if aoObj is not None:
            sampleRate = aoObj.sampleRate
        if tol is None:
            tol = 0
        dampingFunc = {
            'exp': lambda t: _np.exp(-dampingFactor * t),
            'quad': lambda t: _np.reciprocal(1 + dampingFactor * t)
        }.get(dampingMethod, lambda t: _np.exp(-dampingFactor * t))

        def _dampedAmp():
            blockOffset = 0
            for amp in self._genObj:
                blockLen = len(amp)
                if dampingFunc(blockOffset / sampleRate) < tol:
                    if stopBelowTol:
                        return
                    yield _np.zeros((blockLen, ))
                else:
                    damper = dampingFunc(_np.arange(blockOffset,
                                                    blockOffset + blockLen)
                                         / sampleRate)
                    yield _np.where(damper < tol, 0, amp * damper)
                blockOffset += blockLen
        self = self.__class__(_dampedAmp())
        return self

    def ampModify(self, ampFunc):
        ampFunc = _np.vectorize(ampFunc)
        self = self.__class__((ampFunc(amp) for amp in self._genObj))
        return self


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

    def _ensureGen(nparr_or_sig):
        if nparr_or_sig.__class__ is _np.ndarray:
            return AudioOutputSignal.fromNpArray(nparr_or_sig)
        elif nparr_or_sig.__class__ is AudioOutputSignal:
            return nparr_or_sig
        else:
            raise ValueError("Unknown signal type")

    def play(self, signal, signalR=None, keepActivate=True):
        signal = self._ensureGen(signal)
        if self._channel == 2:
            if signalR is None:
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
            self._stream.write(buf.clip(-1., 1.).astype(_np.float32,
                                                        casting='same_kind',
                                                        copy=False).tobytes())
        if not keepActivate:
            self._stream.stop_stream()
