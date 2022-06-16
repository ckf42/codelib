# TODO no numpy as dependency
# TODO higher width than float32

import pyaudio as _pa
import numpy as _np
import itertools as _it
from numbers import Number as _numClass
from typing import Optional, Callable, Union
from collections.abc import Iterable


class AudioOutputSignal:
    """
    A class for generating audio signals
    ---
    Properties:
        isInEffect:
            Read-only
            Indicates if the signal is still valid
    ---
    Methods:
        Class methods:
            fromNpArray
            fromAmpFunc
            fromFreqFunc
            silentSignal
            sineWave
            unitSound
            squareWave
            sawWave
            triangleWave
            joinSignals
            joinSignalsSmooth
            sum
            prod
        Member methods:
            toNpArray
            join
            joinSmooth
            damping
            cutoff
            ampModify
            elementwiseOp
            add
            __add__, __radd__
            mul
            __mul__, __rmul__
            enforceBufferSize
            play
            skipTime
            keepTime
            clip
            repeat
            echo
    """
    # actual data
    _genObj = None
    # whether the signal generator can still be used
    _isInEffect = True
    # referential standard buffer size
    _bufSize = None
    # number of chunks, float('inf') if unlimited, None if not known
    _length = None

    def __init__(self,
                 gen: Iterable,
                 bufSize: Optional[int] = None,
                 length: Optional[int] = None):
        """
        Constructor for AudioOutputSignal class.
        Most of the time, this constructor should not be called directly.
        To construct a signal, you may use the class methods.
        ---
        Parameter:
            gen:
                Type: iterable
                The generator for actual signal
            bufSize:
                Type: Optional[int]
                Default: None
                The reference buffer size
            length
                Type: Optional[int]
                Default: None
                The reference length of the signal
                For signals that have infinite length, pass None
        """
        self._genObj = gen
        self._length = length

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

    def __len__(self):
        return self._length

    @property
    def isInEffect(self):
        """
        Property denoting whether the object can still be used.
        Read-only property.
        """
        return self._isInEffect

    @isInEffect.setter
    def isInEffect(self, newFlag):
        raise ValueError("This property is read-only")

    @classmethod
    def fromNpArray(cls,
                    npArray: _np.ndarray,
                    bufferSize: Optional[int] = 4096):
        """
        Constuct AudioOutputSignal from a numpy.ndarray.
        ---
        Parameter:
            npArray:
                Type: numpy.ndarray
                The data for the signal.
                npArray will be flatten to 1D and casted to float32 type.
            bufferSize:
                Type: Optional[int]
                Default: 4096
                The buffer size for the object.
                If None, the whole data will be taken as one buffer,
                    which may deteriorate the performance if npArray is too large.
        """
        npArray = npArray.reshape(-1)
        if npArray.dtype != _np.float32:
            npArray = npArray.astype(_np.float32)
        elif bufferSize is None:
            bufferSize = len(npArray)
        arrLen = len(npArray)
        nPieces = (arrLen + bufferSize - 1) // bufferSize
        return cls((npArray[bIdx * bufferSize:min((bIdx + 1) * bufferSize,
                                                  arrLen)]
                    for bIdx in range(nPieces)),
                   bufSize=bufferSize,
                   length=nPieces)

    @classmethod
    def fromAmpFunc(cls,
                    ampFunc: Callable,
                    duration: Optional[float] = 1.,
                    bufferSize: Optional[int] = 4096,
                    sampleRate: int = 48000):
        """
        Constuct AudioOutputSignal from a function that gives the amplitude.
        ---
        Parameter:
            ampFunc:
                Type: callable
                The function that gives the amplitude.
                Must take only one input (time)
                To speed up the calculation, this function will be vectoized first.
            duration:
                Type: Optional[float]
                Default: 1.0
                The duration of the signal, in seconds.
                ampFunc will be called with input values in [0, duration]
            bufferSize:
                Type: Optional[int]
                Default: 4096
                The buffer size for the object.
                If None, the whole data will be taken as one buffer,
                    which may deteriorate the performance if npArray is too large.
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal.
        """
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
                bufSize=bufferSize,
                length=nPieces)
        else:
            if bufferSize is None:
                raise ValueError("No bufferSize provided")
            return cls((ampFunc_formatted(_np.arange(bIdx * bufferSize,
                                                     (bIdx + 1) * bufferSize)
                                          / sampleRate)
                        for bIdx in _it.count()),
                       bufSize=bufferSize,
                       length=float('inf'))

    @classmethod
    def fromFreqFunc(cls,
                     freqFunc: Callable,
                     duration: Optional[float] = 1.,
                     amplitude: float = 1.,
                     initPhase: float = 0.,
                     bufferSize: Optional[int] = 4096,
                     sampleRate: int = 48000):
        """
        Constuct AudioOutputSignal from a function that gives the frequency.
        ---
        Parameter:
            freqFunc:
                Type: callable
                The function that gives the frequency.
                Must take only one input (time)
                The amplitude will be determined by sine function.
                To speed up the calculation, this function will be vectoized first.
            duration:
                Type: Optional[float]
                Default: 1.0
                The duration of the signal, in seconds.
                ampFunc will be called with input values in [0, duration]
            amplitude:
                Type: float
                Default: 1.0
                The amplitude of the output singal.
            initPhase:
                Type: float
                Default: 0.0
                The initial Phase for the sine function.
            bufferSize:
                Type: Optional[int]
                Default: 4096
                The buffer size for the object.
                If None, the whole data will be taken as one buffer,
                    which may deteriorate the performance if npArray is too large.
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal.
        """
        return cls.fromAmpFunc(ampFunc=lambda t: amplitude
                               * _np.sin(2 * _np.pi * t
                                         * freqFunc(t)
                                         + initPhase),
                               duration=duration,
                               bufferSize=bufferSize,
                               sampleRate=sampleRate)

    @classmethod
    def silentSignal(cls,
                     duration: Optional[float] = 1.,
                     bufferSize: Optional[int] = 4096,
                     sampleRate: int = 48000):
        """
        Constuct AudioOutputSignal that gives an empty signal.
        ---
        Parameter:
            duration:
                Type: Optional[float]
                Default: 1.0
                The duration of the signal, in seconds.
                ampFunc will be called with input values in [0, duration]
            bufferSize:
                Type: Optional[int]
                Default: 4096
                The buffer size for the object.
                If None, the whole data will be taken as one buffer,
                    which may deteriorate the performance if npArray is too large.
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal.
        """
        return cls.fromAmpFunc(ampFunc=lambda t: 0.,
                               duration=duration,
                               bufferSize=bufferSize,
                               sampleRate=sampleRate)

    @classmethod
    def sineWave(cls,
                 frequency: float,
                 duration: Optional[float] = 1.,
                 amplitude: float = 1.,
                 initPhase: float = 0.,
                 bufferSize: Optional[int] = 4096,
                 sampleRate: int = 48000):
        """
        Constuct AudioOutputSignal that gives a constant frequency signal.
        ---
        Parameter:
            frequency:
                Type: float
                The frequency of the output signal, in Hz.
            duration:
                Type: Optional[float]
                Default: 1.0
                The duration of the signal, in seconds.
                ampFunc will be called with input values in [0, duration]
            amplitude:
                Type: float
                Default: 1.0
                The amplitude of the output singal.
            initPhase:
                Type: float
                Default: 0.0
                The initial Phase for the sine function.
            bufferSize:
                Type: Optional[int]
                Default: 4096
                The buffer size for the object.
                If None, the whole data will be taken as one buffer,
                    which may deteriorate the performance if npArray is too large.
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal.
        """
        return cls.fromFreqFunc(freqFunc=lambda t: frequency,
                                duration=duration,
                                amplitude=amplitude,
                                initPhase=initPhase,
                                bufferSize=bufferSize,
                                sampleRate=sampleRate)

    @classmethod
    def unitSound(cls, frequency: float):
        """
        Constuct AudioOutputSignal that gives an empty signal.
        Wrapper of sineWave.
        The duration is exactly one period of the signal.
        All other parameters for sineWave are the default parameters.
        ---
        Parameter:
            frequency:
                Type: float
                The frequency of the output signal.
        """
        return cls.sineWave(frequency=frequency,
                            duration=1. / frequency)

    @classmethod
    def squareWave(cls,
                   frequency: float,
                   duration: Optional[float] = 1.,
                   amplitude: float = 1.,
                   bufferSize: Optional[int] = 4096,
                   sampleRate: int = 48000):
        """
        Constuct AudioOutputSignal that gives a square wave.
        ---
        Parameter:
            frequency:
                Type: float
                The frequency of the output signal, in Hz.
            duration:
                Type: Optional[float]
                Default: 1.0
                The duration of the signal, in seconds.
                ampFunc will be called with input values in [0, duration]
            amplitude:
                Type: float
                Default: 1.0
                The amplitude of the output singal.
            initPhase:
                Type: float
                Default: 0.0
                The initial Phase for the sine function.
            bufferSize:
                Type: Optional[int]
                Default: 4096
                The buffer size for the object.
                If None, the whole data will be taken as one buffer,
                    which may deteriorate the performance if npArray is too large.
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal.
        """
        return cls.fromAmpFunc(ampFunc=lambda t:
                               amplitude * _np.sign(
                                   _np.sin(2 * _np.pi
                                           * frequency * t)),
                               duration=duration,
                               bufferSize=bufferSize,
                               sampleRate=sampleRate)

    @classmethod
    def sawWave(cls,
                frequency: float,
                duration: Optional[float] = 1.,
                amplitude: float = 1.,
                bufferSize: Optional[int] = 4096,
                sampleRate: int = 48000):
        """
        Constuct AudioOutputSignal that gives a saw wave.
        ---
        Parameter:
            frequency:
                Type: float
                The frequency of the output signal, in Hz.
            duration:
                Type: Optional[float]
                Default: 1.0
                The duration of the signal, in seconds.
                ampFunc will be called with input values in [0, duration]
            amplitude:
                Type: float
                Default: 1.0
                The amplitude of the output singal.
            bufferSize:
                Type: Optional[int]
                Default: 4096
                The buffer size for the object.
                If None, the whole data will be taken as one buffer,
                    which may deteriorate the performance if npArray is too large.
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal.
        """
        return cls.fromAmpFunc(ampFunc=lambda t:
                               amplitude * (_np.modf(
                                   t * frequency)[0] * 2 - 1),
                               duration=duration,
                               bufferSize=bufferSize,
                               sampleRate=sampleRate)

    @classmethod
    def triangleWave(cls,
                     frequency: float,
                     duration: Optional[float] = 1.,
                     amplitude: float = 1.,
                     bufferSize: Optional[int] = 4096,
                     sampleRate: int = 48000):
        """
        Constuct AudioOutputSignal that gives a triangle wave.
        ---
        Parameter:
            frequency:
                Type: float
                The frequency of the output signal, in Hz.
            duration:
                Type: Optional[float]
                Default: 1.0
                The duration of the signal, in seconds.
                ampFunc will be called with input values in [0, duration]
            amplitude:
                Type: float
                Default: 1.0
                The amplitude of the output singal.
            bufferSize:
                Type: Optional[int]
                Default: 4096
                The buffer size for the object.
                If None, the whole data will be taken as one buffer,
                    which may deteriorate the performance if npArray is too large.
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal.
        """
        return cls.fromAmpFunc(ampFunc=lambda t: amplitude
                               * (2 * _np.abs(2 * _np.modf(
                                   t * frequency)[0] - 1) - 1),
                               duration=duration,
                               bufferSize=bufferSize,
                               sampleRate=sampleRate)

    def toNpArray(self,
                  frameLimit: int = 60 * 48000,
                  getLenOnly: bool = False):
        """
        Returns the underlying data as a numpy.ndarray.
        ---
        Parameter:
            frameLimit:
                Type: int
                Default: 60 * 48000
                The maximal number of frames outputed.
                The default corresponds to 60 seconds in 48k sample rate.
                If frameLimit is negative, the whole signal will be outputed.
            getLenOnly:
                Type: bool
                Default: False
                Returns only the length of the signal in number of frames.
        ---
        Return:
            The whole data as encoded in a 1D numpy.ndarray.
            If getLenOnly is True, returns only the length of the numpy.ndarray.
        ---
        Exception:
            If the object is invalid, a ValueError will be raised
        ---
        Side Effect:
            The object will be set invalided after calling this function.
        """
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        if getLenOnly:
            # TODO: isolate this to a separate function
            return len(self.toNpArray(frameLimit=frameLimit,
                                      getLenOnly=False))
        # extract np array till the end if frameLimit is negative
        if frameLimit < 0:
            self._isInEffect = False
            return _np.hstack(tuple(self._genObj))
        else:
            return _np.hstack(tuple(
                self.keepTime(timeToKeep=frameLimit,
                              sampleRate=1)._genObj))

    def join(self, *sigObj):
        """
        Joining multiple AudioOutputSignal objects.
        ---
        Parameters:
            *sigObj:
                Type: AudioOutputSignal
                The objects to be joined with this AudioOutputSignal object.
                All objects will be joined in order.
        ---
        Return:
            A new AudioOutputSignal object that contains all data joined in sequence.
        ---
        Exception:
            If some of the objects is invalid, a ValueError will be raised
        ---
        Side Effect:
            All AudioOutputSignal objects, including this one, will be set invalid.
            In the case where an exception is raised, all objects iterated before the
                exception is raised will be set invalid
        """
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        if len(sigObj) == 0:
            return self
        elif len(sigObj) == 1:
            # TODO: deal with different buffer size
            # currently use only the first one (self)
            sigObj = sigObj[0]
            if not sigObj.isInEffect:
                raise ValueError("No valid signal data")
            self._isInEffect = False
            sigObj._isInEffect = False
            return self.__class__(
                _it.chain(self._genObj, sigObj._genObj),
                bufSize=self._bufSize,
                length=(self._length + sigObj._length
                        if all(x is not None
                               for x in (self._length, sigObj._length))
                        else float('inf')))
        else:
            return self.join(sigObj[0]).join(*(sigObj[1:]))

    @classmethod
    def joinSignals(cls, *sigObj):
        """
        Construct a new AudioOutputSignal from all AudioOutputSignal inputted.
        Wrapper of AudioOutputSignal.join.
        ---
        Parameter:
            *sigObj:
                Type: AudioOutputSignal
                The AudioOutputSignal objects to be joined.
                All objects will be joined in order.
        ---
        Return:
            A new AudioOutputSignal object that contains all data joined in sequence.
        ---
        Exception:
            If some of the objects is invalid, a ValueError will be raised
        ---
        Side Effect:
            All AudioOutputSignal objects, including this one, will be set invalid.
            In the case where an exception is raised, all objects iterated before the
                exception is raised will be set invalid
        """
        if len(sigObj) == 0:
            return cls.silentSignal(duration=None)
        else:
            return sigObj[0].join(*sigObj[1:])

    def joinSmooth(self,
                   *sigObj,
                   mode: str = 'linear',
                   transitDuration: float = 0.1,
                   sampleRate: int = 48000):
        """
        Join AudioOutputSignal, but smoothly
        ---
        Parameter:
            *sigObj:
                Type: AudioOutputSignal
                The objects to be joined with this one
            mode:
                Type: str
                Default: 'linear'
                Keyword only
                The method used to join the signals together
                Currently only accept two options:
                    'linear': The amplitude during the transition period is linearly interpolated
                              from the adjacent buffers
                    'zero':   The amplitude during the transition period is simple zero
            transitDuration:
                Type: float
                Default: 0.1
                The length of the transition period, in seconds
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal
        ---
        Return:
            A new AudioOutputSignal object that contains all data joined in sequence.
            If no sigObj is given, will return self
        ---
        Exception:
            If some of the objects is invalid, a ValueError will be raised
        ---
        Side Effect:
            All AudioOutputSignal objects, including this one, will be set invalid.
            In the case where an exception is raised, all objects iterated before the
                exception is raised will be set invalid
        """
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        transitFrameCount = int(transitDuration * sampleRate)
        if len(sigObj) == 0:
            return self
        elif len(sigObj) == 1:
            self._isInEffect = False
            if not sigObj[0].isInEffect:
                raise ValueError("No valid signal data")
            sigObj[0]._isInEffect = False
            lastBuf = _np.zeros(0)
            while (buf := next(self._genObj, None)) is not None:
                yield buf
                lastBuf = buf
            newBuf = next(sigObj[0]._genObj, None)
            if newBuf is not None:
                interpolBuf = {
                    'linear': (
                        lambda buf1, buf2:
                        _np.linspace(buf1[-1], buf2[0],
                                     num=transitFrameCount)),
                    'zero': (lambda buf1, buf2: _np.zeros(transitFrameCount)),
                }.get(mode,
                      lambda buf1, buf2: _np.zeros(0))(lastBuf, newBuf)
                yield interpolBuf
                yield newBuf
                # yield sigObj[0]._genObj
                for buf in sigObj[0]._genObj:
                    yield buf
        else:
            return self.joinSmooth(
                sigObj[0],
                mode=mode,
                transitDuration=transitDuration,
                sampleRate=sampleRate).join(
                *(sigObj[1:]),
                mode=mode,
                transitDuration=transitDuration,
                sampleRate=sampleRate)

    @classmethod
    def joinSignalsSmooth(cls,
                          *sigObj,
                          mode: str = 'linear',
                          transitDuration: float = 1.,
                          sampleRate: int = 48000):
        """
        Join AudioOutputSignal, but smoothly
        ---
        Parameter:
            *sigObj:
                Type: AudioOutputSignal
                The objects to be joined together
            mode:
                Type: str
                Default: 'linear'
                Keyword only
                The method used to join the signals together
                Currently only accept two options:
                    'linear': The amplitude during the transition period is linearly interpolated
                              from the adjacent buffers
                    'zero':   The amplitude during the transition period is simple zero
            transitDuration:
                Type: float
                Default: 0.1
                The length of the transition period, in seconds
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal
        ---
        Return:
            A new AudioOutputSignal object that contains all data joined in sequence.
            If no sigObj is given, will return a silent signal of infinite length
        ---
        Exception:
            If some of the objects is invalid, a ValueError will be raised
        ---
        Side Effect:
            All AudioOutputSignal objects, including this one, will be set invalid.
            In the case where an exception is raised, all objects iterated before the
                exception is raised will be set invalid
        """
        if len(sigObj) == 0:
            return cls.silentSignal(duration=None)
        else:
            return sigObj[0].joinSmooth(*sigObj[1:],
                                        mode=mode,
                                        transitDuration=transitDuration,
                                        sampleRate=sampleRate)

    def damping(self,
                dampingFactor: float = 1.,
                dampingMethod: Union[str, Callable] = 'exp',
                tol: Optional[float] = None,
                stopBelowTol: bool = False,
                sampleRate: int = 48000):
        """
        Tone down the signal to zero
        ---
        Parameter:
            dampingFactor:
                Type: float
                Default: 1.0
                On default dampingMethod, the frequency factor used to damp the signal
                Ignored if dampingMethod is a callable
            dampingMethod:
                Type: Union[str, Callable]
                Default: 'exp'
                The method used to give the multiplie to damp the signal on its amplitude
                The following default damping methods can be specified with a case-insensitive string:
                    'exp': the amplitude will decrease as exp(- a t)
                    'linear': the amplitude will decrease as 1 / (1 + a t)
                    'quad': the amplitude will decrease as 1 / (1 + (a t) ** 2)
                    'cubic': the amplitude will decrease as 1 / (1 + (a t) ** 3)
                    where a is the dampingFactor
                If dampingMethod is a string not in the above list, will fall back to 'exp'
                If dampingMethod is callable, it will be used to directly
                    In this case, it is assumed to take a 1D numpy.ndarray as time
                        and returns a numpy.ndarray of the same length
            tol:
                Type: Optional[float]
                Default: None
                The minimal playable damping multiplier to be seen nonzero
                If the damping multiplier goes below this value, the output will be consider zero
                If None, tol will be set to -1 and stopBelowTol will be set to False
            stopBelowTol:
                Type: bool
                Default: False
                Determine if the signal should stop on the first time the damping multiplier goes
                    below tol
            sampleRate
                Type: int
                Default: 48000
                The sample rate of the output signal
        ---
        Return:
            An AudioOutputSignal object that records the damped signal
        ---
        Exception:
            If the object is invalid, a ValueError will be raised
        ---
        Side Effect:
            The original AudioOutputSignal object will be set invalid
        """
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        self._isInEffect = False
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
                              bufSize=self._bufSize,
                              length=self._length)

    def cutoff(self, chunkTotalVarTol: float = 1e-3):
        """
        Stop signal when the signal is too quiet
        ---
        Parameter:
            chunkTotalVarTol:
                Type: float
                Default: 1e-3
                The minimal L1 norm for the buffer to continue
        ---
        Return:
            The original signal, except the signal will be stopped
                if the L1 norm of the signal is smaller than chunkTotalVarTol
                in some buffer
        ---
        Exception:
            If the object is invalid, a ValueError will be raised
        ---
        Side Effect:
            The original AudioOutputSignal object will be set invalid
        """
        if not self.isInEffect:
            raise ValueError("No valid signal data")
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
                              bufSize=self._bufSize,
                              length=self._length)

    def ampModify(self, ampFunc: Callable):
        """
        Modify the signal by changing the amplitude
        ---
        Parameter:
            ampFunc:
                Type: Callable
                Must take only one parameter, which is the amplitude of the signal
                To speed up the computation, the function will be vectorized
        ---
        Return:
            The original signal, with the amplitude changed by ampFunc
        ---
        Exception:
            If the object is invalid, a ValueError will be raised
        ---
        Side Effect:
            The original AudioOutputSignal object will be set invalid
        """
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        self._isInEffect = False
        return self.__class__(map(_np.vectorize(ampFunc),
                                  self._genObj),
                              bufSize=self._bufSize,
                              length=self._length)

    def elementwiseOp(self, secondSigObj, ampFunc: Callable):
        """
        Mixing one signal with another
        ---
        Parameter:
            secondSigObj:
                Type: AudioOutputSignal
                The second signal object to interactive with
            ampFunc:
                Type: Callable
                The operation for the interaction
                Must take two parameters, which are the amplitudes of the two signals
                To speed up the computation, the function will be vectorized
        ---
        Return:
            The resulting AudioOutputSignal that records the mixed signal
            The resulting amplitudes will be the values of ampFunc on the two signals
            (ampFunc(amp1, amp2))
            The signal will stop when one of the signals runs out
        ---
        Exception:
            If one of the object is invalid, a ValueError will be raised
        ---
        Side Effect:
            The two AudioOutputSignal objects will be set invalid
        """
        # if not isinstance(secondSigObj, AudioOutputSignal):
            # raise ValueError(
                # f"Not a signal class ({secondSigObj.__class__.__name__})"
            # )
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        if not secondSigObj.isInEffect:
            raise ValueError("No valid signal data")
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

        return self.__class__(
            _elementwiseOp_gen(self._genObj,
                               secondSigObj._genObj,
                               ampFunc),
            bufSize=self._bufSize,
            length=(min(self._length, secondSigObj._length)
                    if all(x is not None
                           for x in (self._length, secondSigObj._length))
                    else None))

    def add(self, *signalObj, average: bool = False):
        """
        Adding signals
        ---
        Parameter:
            *signalObj:
                Type: Union[AudioOutputSignal, float]
                The signal objects to add with
                If the type is float, will be taken as a constant signal
            average:
                Type: bool
                Default: False
                Determine if the output signal amplitude should be averaged
        ---
        Return:
            The resulting AudioOutputSignal that records the added signal
            The resulting amplitudes will be the sum of amplitudes of the signals
            If average is True, the resulting amplitudes will be averaged
            If no signalObj is given, will return the original signal
        ---
        Exception:
            If some of the objects is invalid, a ValueError will be raised
        ---
        Side Effect:
            All AudioOutputSignal objects, including this one, will be set invalid,
                unless no signalObj is given
            In the case where an exception is raised, all objects iterated before the
                exception is raised will be set invalid
        """
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        if len(signalObj) == 0:
            return self
        elif len(signalObj) == 1:
            if isinstance(signalObj[0], float):
                return self.ampModify(lambda amp:
                                      (amp + signalObj[0]) / (
                                          2 if average else 1))
            else:
                if not signalObj[0].isInEffect:
                    raise ValueError("No valid signal data")
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
        """
        Adding signals
        ---
        Parameter:
            *signalObj:
                Type: Union[AudioOutputSignal, float]
                The signal objects to add with
                If the type is float, will be taken as a constant signal
            average:
                Type: bool
                Default: False
                Determine if the output signal amplitude should be averaged
        ---
        Return:
            The resulting AudioOutputSignal that records the added signal
            The resulting amplitudes will be the sum of amplitudes of the signals
            If average is True, the resulting amplitudes will be averaged
            If no signalObj is given, will return a silent signal of infinite length
        ---
        Exception:
            If some of the objects is invalid, a ValueError will be raised
        ---
        Side Effect:
            All AudioOutputSignal objects will be set invalid.
            In the case where an exception is raised, all objects iterated before the
                exception is raised will be set invalid
        """
        if len(signalObj) == 0:
            return cls.silentSignal(duration=None)
        else:
            return signalObj[0].add(*signalObj[1:], average=average)

    def mul(self, *signalObj):
        """
        Multiplying signals
        ---
        Parameter:
            *signalObj:
                Type: Union[AudioOutputSignal, float]
                The signal objects to multipled with
                If the type is float, will be taken as a constant signal
        ---
        Return:
            The resulting AudioOutputSignal that records the multiplied signal
            The resulting amplitudes will be the product of amplitudes of the signals
            If no signalObj is given, will return the original signal
        ---
        Exception:
            If some of the objects is invalid, a ValueError will be raised
        ---
        Side Effect:
            All AudioOutputSignal objects, including this one, will be set invalid,
                unless no signalObj is given
            In the case where an exception is raised, all objects iterated before the
                exception is raised will be set invalid
        """
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        if len(signalObj) == 0:
            return self
        elif len(signalObj) == 1:
            if not signalObj[0].isInEffect:
                raise ValueError("No valid signal data")
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
        """
        Multiplying signals
        ---
        Parameter:
            *signalObj:
                Type: Union[AudioOutputSignal, float]
                The signal objects to multipled with
                If the type is float, will be taken as a constant signal
        ---
        Return:
            The resulting AudioOutputSignal that records the multiplied signal
            The resulting amplitudes will be the product of amplitudes of the signals
            If no signalObj is given, will return a signal of unit amplitude and infinite length
        ---
        Exception:
            If some of the objects is invalid, a ValueError will be raised
        ---
        Side Effect:
            All AudioOutputSignal objects will be set invalid,
                unless no signalObj is given
            In the case where an exception is raised, all objects iterated before the
                exception is raised will be set invalid
        """
        if len(signalObj) == 0:
            return cls.fromAmpFunc(lambda x: 1, None)
        else:
            return signalObj[0].mul(*signalObj[1:])

    def enforceBufferSize(self,
                          bufferSize: Optional[int] = 4096,
                          frameLimit: Optional[int] = None):
        """
        Set the buffer size to some fixed number
        ---
        Parameter:
            bufferSize:
                Type: Optional[int]
                Default: 4096
                The target buffer size of the output signal
                If None, the whole data will be taken as a single buffer
                bufferSize and frameLimit cannot both be None
            frameLimit:
                Type: Optional[int]
                Default: None
                The maximal number of frames to be outputted
                If None, will return as many frames as possible
                bufferSize and frameLimit cannot both be None
        ---
        Return:
            A AudioOutputSignal object that encodes the same signal but
                with the required buffer size
        ---
        Exception:
            If both bufferSize and frameLimit are both None, will raise a ValueError
            If the signal is invalid, will raise a ValueError
        ---
        Side Effect:
            The object will be set invalid.
        """
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        if bufferSize is None:
            if frameLimit is None:
                raise ValueError("bufferSize and frameLimit cannot both be None")
            arr = self.toNpArray(frameLimit=frameLimit)
            return self.__class__.fromNpArray(arr, bufferSize=len(arr))
        self._isInEffect = False

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
                              bufSize=bufferSize,
                              length=0 if self._length is not None else None)

    def play(self,
             playerAO,
             keepActive: bool = True,
             volume: float = 1.,
             forceAsTwoChannel: bool = False,
             forcePrecompute: bool = False,
             smoothClip: bool = False):
        """
        Play the signal through the speaker
        Wrapper function for AudioOutputInterface.play
        ---
        Parameter:
            For details, please refer to help(AudioOutputInterface.play)
            playAO:
                Type: AudioOutputInterface
            keepActive:
                Type: bool
                Default: True
            volume:
                Type: float
                Default: 1.0
            forceAsTwoChannel:
                Type: bool
                Default: False
            forcePrecompute:
                Type: bool
                Default: False
            smoothClip:
                Type: bool
                Default: False
        ---
        Exception:
            If the signal is invalid, will raise a ValueError
            If playerAO is None, will raise a ValueError
        ---
        Side Effect:
            The object will be set invalid.
        """
        if playerAO is None:
            raise ValueError("No AudioOutputInterface object given")
        elif not self.isInEffect:
            raise ValueError("No valid signal data")
        else:
            playerAO.play(self,
                          keepActive=keepActive,
                          volume=volume,
                          forceAsTwoChannel=forceAsTwoChannel,
                          forcePrecompute=forcePrecompute,
                          smoothClip=smoothClip)

    def skipTime(self, timeToSkip: float = 0., sampleRate: int = 48000):
        """
        Skip some frames of the signal
        ---
        Parameter:
            timeToSkip:
                Type: float
                Default: 0.0
                The time to skip in the signal
                If a non-positive number is given, the original sigal will not be altered
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal
                Will be used to compute the number of data points to skip
        ---
        Return:
            A new AudioOutputSignal object with some data points skipped
        ---
        Exception:
            If the signal is invalid, will raise a ValueError
        ---
        Side Effect:
            The object will be set invalid unless timeToSkip is non-positive.
        """
        if timeToSkip <= 0:
            return self
        # TODO: check if it is actually rounded down
        if not self.isInEffect:
            raise ValueError("No valid signal data")
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

        return self.__class__(
            _skipTime_gen(self._genObj),
            bufSize=self._bufSize,
            length=((self._length - framesToSkip)
                    if self._length is not None
                    else None))

    def keepTime(self,
                 timeToKeep: float = 0.,
                 sampleRate: int = 48000):
        """
        Keep only some frames of the signal
        ---
        Parameter:
            timeToKeep:
                Type: float
                Default: 0.0
                The time to keep in the signal
                If a negative number is given, the original sigal will not be altered
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal
                Will be used to compute the number of data points to keep
        ---
        Return:
            A new AudioOutputSignal object with only some data points kept
        ---
        Exception:
            If the signal is invalid, will raise a ValueError
        ---
        Side Effect:
            The object will be set invalid unless timeToKeep is negative.
        """
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        if timeToKeep < 0:
            return self
        self._isInEffect = False
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
                              bufSize=self._bufSize,
                              length=framesToKeep)

    @classmethod
    def fromFourier(cls,
                    ampList: list[float],
                    freqList: list[float],
                    initPhaseList: Union[float, list[float]] = 0.,
                    duration: float = 1.,
                    ampWeightNormalize: bool = True,
                    bufferSize: int = 4096,
                    sampleRate: int = 48000):
        """
        Construct a signal from Fourier components
        Wrapper of AudioOutputSignal.fromAmpFunc
        ---
        Parameter:
            ampLst:
                Type: list[float]
                A list of float that denotes the peak amplitudes of the components
            freqList:
                Type: list[float]
                A list of float that denotes the frequencies of the components
            initPhaseList:
                Type: Union[float, list[float]]
                Default: 0.0
                A float or a list of float that denotes the initial phases of the components
                If initPhaseList is a float, the same initial phases will be used for all components
            duration:
                Type: float
                Default: 1.0
                The duration of the signal, in seconds
            ampWeightNormalize:
                Type: bool
                Default: True
                Determine if the amplitudes will be normalzed to sum 1
            bufferSize:
                Type: int
                Default: 4096
                The buffer size of the output signal
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal
        ---
        Return:
            The resulting AudioOutputSignal object that records the multiplied signal
            The resulting amplitudes will be the sum of the sine components
                (f(t) = sum(amp[i] * sin(2 * pi * freq[i] * t + initPhase[i])))
            If ampList has length 0, will return a silent signal with required length
        ---
        Exception:
            If ampList and freqList have different lengths, will raise a ValueError
            If initPhaseList is a list and has different length with previous lists,
                will raise a ValueError
        """
        if len(ampList) != len(freqList):
            raise ValueError("ampList and freqList have different lengths")
        if len(ampList) == 0:
            return cls.silentSignal(duration=duration,
                                    bufferSize=bufferSize,
                                    sampleRate=sampleRate)
        else:
            if isinstance(initPhaseList, float):
                initPhaseList = (initPhaseList, ) * len(ampList)
            if len(ampList) != len(initPhaseList):
                raise ValueError("ampList and initPhaseList have different lengths")
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
                sampleRate=sampleRate)

    def clip(self, smoothClip: bool = False):
        """
        Clipping the amplitude of a signal
        ---
        Parameter:
            smoothClip:
                Type: bool
                Default: False
                Determine if smooth clipping is used
                If True, the amplitude will be mapped as 2 / (1 + exp(-2 * amp)) - 1
                Otherwise the amplitude will be clipped in [-1, 1]
        ---
        Return:
            An AudioOutputSignal object where all the amplitudes are clipped in [-1, 1]
        ---
        Exception:
            If the signal is invalid, will raise a ValueError
        ---
        Side Effect:
            The object will be set invalid.
        """
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        self._isInEffect = False
        return self.__class__(((2 / (1 + _np.exp(-2 * amp)) - 1) if smoothClip else amp.clip(-1., 1.)
                               for amp in self._gen),
                              bufSize=self._bufSize,
                              length=self._length)

    def repeat(self,
               repeatTimes: Optional[int] = 1,
               eachDuration: float = 1.,
               patchLenWithZero: bool = False,
               sampleRate: int = 48000):
        """
        Repeat the signal multiple times
        ---
        Parameter:
            repeatTimes:
                Type: Optional[int]
                Default: 1
                The number of repetitions of the signal
                If None, the signal will repeat indefinitely
            eachDuration:
                Type: float
                Default: 1.0
                The length for each repetition
            patchLenWithZero:
                Type: bool
                Default: False
                Determine if the signal should be patched with 0 if the original signal
                    is shorter than eachDuration
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal
        ---
        Exception:
            If the signal is invalid, will raise a ValueError
        ---
        Side Effect:
            The object will be set invalid.
        """
        eachBlockLen = int(eachDuration * sampleRate)
        signalArr = self.toNpArray(frameLimit=eachBlockLen)
        if patchLenWithZero and len(signalArr) < eachBlockLen:
            signalArr = _np.hstack((signalArr,
                                   _np.zeros(eachBlockLen - len(signalArr))))
        if repeatTimes is None:
            return self.__class__(_it.repeat(signalArr),
                                  bufSize=self._bufSize,
                                  length=float('inf'))
        else:
            return self.__class__(_it.repeat(signalArr, repeatTimes),
                                  bufSize=self._bufSize,
                                  length=((self._length
                                           * repeatTimes)
                                          if self._length is not None
                                          else None))

    def echo(self,
             delayTime: float = 0.5,
             echoAmp: float = 0.7,
             infEcho: bool = False,
             sampleRate: int = 48000):
        """
        Add an echoing effect of the signal
        ---
        Parameter:
            delayTime:
                Type: float
                Default: 0.5
                The time delayed before the echo starts, in seconds
            echoAmp:
                Type: float
                Default: 0.7
                The amplitude multiplier for the echo
                Typically in [0, 1]
            infEcho:
                Type: bool
                Default: False
                Determine if the echoes should also be echoed
            sampleRate:
                Type: int
                Default: 48000
                The sample rate of the output signal
        ---
        Return:
            An AudioOutputSignal object that recores the output signal
        ---
        Exception:
            If the signal is invalid, will raise a ValueError
        ---
        Side Effect:
            The object will be set invalid.
        """
        if not self.isInEffect:
            raise ValueError("No valid signal data")
        delayFrame = int(sampleRate * delayTime)

        def _echo_gen(_gen):
            memBuf = _np.zeros(delayFrame)
            while True:
                nextBuf = next(_gen, None)
                if nextBuf is None:
                    nextBuf = _np.zeros(delayFrame)
                elif len(nextBuf) < delayFrame:
                    nextBuf = _np.hstack((nextBuf,
                                          _np.zeros(delayFrame - len(nextBuf))))
                yield nextBuf + memBuf * echoAmp
                if infEcho:
                    memBuf = nextBuf + memBuf * echoAmp
                else:
                    memBuf = nextBuf

        return self.__class__(
            _echo_gen(self.enforceBufferSize(bufferSize=delayFrame)._genObj),
            bufSize=delayFrame,
            length=self._length)


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
    def sampleRate(self, sampleRate: int):
        self._checkParaValid('sampleRate', sampleRate)
        if sampleRate != self._sr:
            self._sr = sampleRate
            self._init_stream()

    @property
    def channels(self):
        return self._channel

    @channels.setter
    def channels(self, channels: int):
        self._checkParaValid('channels', channels)
        if channels != self._channel:
            self._channel = channels
            self._init_stream()

    @property
    def bufferSize(self):
        return self._buffSize

    @bufferSize.setter
    def bufferSize(self, bufferSize: int):
        self._checkParaValid('bufferSize', bufferSize)
        self._buffSize = bufferSize

    def __init__(self,
                 sampleRate: int = 48000,
                 channels: int = 2,
                 bufferSize: int = 4096):
        self._checkParaValid('sampleRate', sampleRate)
        self._sr = sampleRate
        self._checkParaValid('channels', channels)
        self._channel = channels
        self._checkParaValid('bufferSize', bufferSize)
        self._buffSize = bufferSize
        self._paObj = _pa.PyAudio()
        self._init_stream()

    def _ensureSigGen(self, obj, forcePrecompute: Optional[bool]):
        # TODO: check if there is forcePrecompute=None use case
        if obj.__class__.__name__ == 'generator':
            obj = AudioOutputSignal(obj)
        if isinstance(obj, AudioOutputSignal):
            if not obj._isInEffect:
                raise ValueError("Signal has no valid data")
            if forcePrecompute is None:
                forcePrecompute = True
            if isinstance(forcePrecompute, bool):
                if not forcePrecompute:
                    # obj._isInEffect = False
                    # will be declared invalid in enforceBufferSize
                    return obj.enforceBufferSize(
                        bufferSize=self.bufferSize)._genObj
                else:
                    forcePrecompute = 60.
            obj = obj.toNpArray(frameLimit=forcePrecompute * self.bufferSize)
        if isinstance(obj, _np.ndarray):
            return AudioOutputSignal\
                .fromNpArray(obj,
                             bufferSize=self.bufferSize)._genObj
        else:
            raise ValueError(f"Unknown signal type {obj.__class__.__name__}")

    def play(self,
             signal,
             signalR: Optional[AudioOutputSignal] = None,
             keepActive: bool = True,
             volume: float = 1.,
             forceAsTwoChannel: bool = False,
             forcePrecompute: bool = False,
             smoothClip: bool = False):
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

    def playNpArray(self,
                    npArray,
                    keepActive: bool = True,
                    volume: float = 1.,
                    smoothClip: bool = False):
        # if isinstance(npArray, tuple) \
        #         and len(npArray) >= 2 \
        #         and self.channels == 2:
        #     if len(npArray[0]) != len(npArray[1]):
        #         raise ValueError("Input arrays are not of equal length")
        #     npArray = _np.vstack(npArray[0:2]).T.ravel()
        if self.channels != 1:
            raise ValueError("Not supported for multiple channels")
        if not isinstance(npArray, _np.ndarray):
            raise ValueError("Input array not np ndarray")
        if smoothClip:
            npArray = (2 / (1 + _np.exp(-2 * npArray)) - 1) * volume
        else:
            npArray = npArray.clip(-1, 1) * volume
        if self._stream.is_stopped():
            self._stream.start_stream()
        self._stream.write(npArray.astype(_np.float32,
                                          casting='same_kind',
                                          copy=False).tobytes())
        if not keepActive:
            self._stream.stop_stream()

    def clearBuf(self, duration: float = 0.1):
        self.play(AudioOutputSignal.silentSignal(duration=duration,
                                                 bufferSize=self._buffSize,
                                                 sampleRate=self._sr),
                  keepActive=False)


if __name__ == '__main__':
    ao = AudioOutputInterface()
    aos = AudioOutputSignal
