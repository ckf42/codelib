if __name__ == '__main__':
    exit()

# TODO no numpy as dependency
# TODO higher width than float32
# TODO make signal class

import pyaudio as _pa
import numpy as _np


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

    def _arrToGenerator(self, npArr):
        if npArr.dtype != _np.float32:
            npArr = npArr.astype(_np.float32)
        nPieces = len(npArr) // self._buffSize
        for bIdx in range(nPieces):
            yield npArr[range(bIdx * self._buffSize,
                              (bIdx + 1) * self._buffSize)]
        yield npArr[nPieces * self._buffSize:]

    @staticmethod
    def sigGenToArr(gen):
        return _np.hstack(tuple(gen))

    def _ensureGen(self, npArr_or_gen):
        if isinstance(npArr_or_gen, _np.ndarray):
            return self._arrToGenerator(npArr_or_gen)
        else:
            return npArr_or_gen

    def getArrayDuration(self, npArr):
        return len(npArr) / (self._sr * self._channel)

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

    def signalByAmpFunc(self, ampFunc, duration=1., wholeChunk=False):
        ampFunc_formatted = _np.vectorize(ampFunc)
        if wholeChunk:
            yield ampFunc_formatted(_np.arange(int(duration * self._sr))
                                    / self._sr)
        else:
            nPieces, nRemain = divmod(int(duration * self._sr),
                                      self._buffSize)
            for bIdx in range(nPieces):
                yield ampFunc_formatted((bIdx * self._buffSize
                                         + _np.arange(self._buffSize))
                                        / self._sr)
            yield ampFunc_formatted((nPieces * self._buffSize
                                     + _np.arange(nRemain))
                                    / self._sr)

    def signalByFreqFunc(self,
                         freqFunc,
                         duration=1.,
                         amplitude=1.,
                         wholeChunk=False):
        yield from self.signalByAmpFunc(
            ampFunc=lambda t: amplitude * _np.sin(
                2 * _np.pi * t * freqFunc(t)),
            duration=duration,
            wholeChunk=wholeChunk)

    def silentSignal(self, duration=1., wholeChunk=False):
        yield from self.signalByAmpFunc(ampFunc=lambda t: 0.,
                                        duration=duration,
                                        wholeChunk=wholeChunk)

    def sineWave(self, frequency, duration=1., amplitude=1., wholeChunk=False):
        yield from self.signalByFreqFunc(freqFunc=lambda t: frequency,
                                         duration=duration,
                                         amplitude=amplitude,
                                         wholeChunk=wholeChunk)

    def squareWave(self,
                   frequency,
                   duration=1.,
                   amplitude=1.,
                   wholeChunk=False):
        yield from self.signalByAmpFunc(ampFunc=lambda t:
                                        amplitude * _np.sign(
                                            _np.sin(2 * _np.pi
                                                    * frequency * t)),
                                        duration=duration,
                                        wholeChunk=wholeChunk)

    def sawWave(self,
                frequency,
                duration=1.,
                amplitude=1.,
                wholeChunk=False):
        yield from self.signalByAmpFunc(ampFunc=lambda t:
                                        amplitude * (_np.modf(
                                            t * frequency)[0] * 2 - 1),
                                        duration=duration,
                                        wholeChunk=wholeChunk)

    def triangleWave(self,
                     frequency,
                     duration=1.,
                     amplitude=1.,
                     wholeChunk=False):
        yield from self.signalByAmpFunc(ampFunc=lambda t: amplitude
                                        * (2 * _np.abs(2 * _np.modf(
                                            t * frequency)[0] - 1) - 1),
                                        duration=duration,
                                        wholeChunk=wholeChunk)

    def damping(self, sigGen, dampingFactor=1, tol=1e-6):
        blockOffset = 0
        for amp in self._ensureGen(sigGen):
            blockLen = len(amp)
            yield _np.zeros((blockLen, )) \
                if _np.exp(-dampingFactor * blockOffset) < tol \
                else amp * _np.exp(-dampingFactor
                                   * (_np.arange(blockOffset,
                                                 blockOffset + blockLen))
                                   / self._sr)
            blockOffset += blockLen
