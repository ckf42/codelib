# TODO simpler main loop
# TODO different tone
# TODO transpose in keys?
# TODO check portability?

import numpy as np
import argparse
from pynput import keyboard as kb
import pyaudio as pa
import itertools as it

print("Initiating ...")

# cli arguments with argparse
parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true',
                    help="Toggle debug mode")
parser.add_argument('--length', type=float, default=1 / 30,
                    help="Length of a time unit, in seconds. "
                    "The shortest length of a signal, "
                    "also the reaction time. "
                    "Default: 1/30")
parser.add_argument('--samplerate', type=int, default=48000,
                    help="Sample rate, in Hz, "
                    "or size of data processed per second for each note. "
                    "Available sample rate varies on machines. "
                    "Usually 22050, 32000, 44100, 48000 are supported. "
                    "Use a higher value for better quality, "
                    "use a lower value (e.g. 22050) if output is lagging. "
                    "Default: 48000")
parser.add_argument('--nosuppress', action='store_true',
                    help="Do not suppress keyboard event. "
                    "By default, all keyboard events are captured and blocked "
                    "from sending to the system until the program ends, "
                    "including those that are not used. "
                    "Specify this option to allow event pass-through. ")
parser.add_argument('--just', action='store_true',
                    help="Use just intonation instead of equal termpermant. "
                    "By default, use equal termpermant "
                    "(with each note differ by 2^(1/12)). "
                    "Specify this option to use the just intonation. ")
args = parser.parse_args()


# pyaudio parameters
unitTimeLength = args.length
sampleRate = args.samplerate
bufferSize = int(sampleRate * unitTimeLength)
# damping, kill natural damping below ~5%
naturalDampingFactor = 9
naturalDampingCutoffCount = int(np.log(1 / 0.05)
                                / naturalDampingFactor
                                * sampleRate / bufferSize)
manualDampingIsActive = False
manualDampingFactor = 3
manualDampedFrameCount = 0
# octave scale parameter
bandOffset = 3
bandOffset_adjust = 0
noteTransposeOffset = 0
# tone parameter
signalMode = 1
# volume parameter
globalVolume = 100
# holding switch
doNotesHolding = False
# debug recording
doRecording = None
recordedBuffer = []
recordedBufferPlayPtr = 0
# release mode
doReleaseDampAll = True
# current notes
activeNotesList = {}
# main loop var
mainLoopIsKilled = False
reportedEmpty = False
previousActiveNoteCount = 0
# note range C2-B6 (12-83)
noteNames = ["C", "Cs", "D", "Ds", "E", "F", "Fs", "G", "Af", "A", "Bf", "B"]
noteCmdList = tuple(map(lambda x: 'n' + str(x), range(12)))
basicFreq = [round(110 * 2 ** (k / 12), 4) for k in range(-9, 3)]
if args.just:  # Just intonation
    basicFreq = list(map(lambda x: round(110 / 27 * 16 * x, 4),
                         [1, 256 / 243, 9 / 8, 32 / 27,
                         81 / 64, 4 / 3, 729 / 512, 3 / 2,
                         128 / 81, 27 / 16, 16 / 9, 243 / 128]))


def getFreq(noteIdx):
    return basicFreq[noteIdx % 12] * 2. ** (noteIdx // 12 - 2)


def getCommandFromKey(key):
    returnCmd = None
    if hasattr(key, 'vk'):
        returnCmd = {
            103: 'n0',  # 'C',
            111: 'n1',  # 'Cs',
            106: 'n2',  # 'D',
            109: 'n3',  # 'Ds',
            100: 'n4',  # 'E',
            104: 'n5',  # 'F',
            105: 'n6',  # 'Fs',
            107: 'n7',  # 'G',
            97: 'n8',  # 'Af',
            101: 'n9',  # 'A',
            12: 'n9',  # 'A',
            102: 'n10',  # 'Bf',
            96: 'dd',
            # 192: 'o0',
            49: 'o1',
            50: 'o2',
            51: 'o3',
            52: 'o4',
            53: 'o5',
            54: 'o6',
        }.get(key.vk, None)
    if returnCmd is None and hasattr(key, 'char'):
        returnCmd = {
            '[': 'vu',
            ']': 'vd',
        }.get(key.char, None)
    if returnCmd is None:
        returnCmd = {
            kb.Key.enter: 'n11',  # 'B',
            kb.Key.esc: 'q',
            kb.Key.home: 'n0',  # 'C',
            kb.Key.up: 'n5',  # 'F',
            kb.Key.page_up: 'n6',  # 'Fs',
            kb.Key.left: 'n4',  # 'E',
            kb.Key.right: 'n10',  # 'Bf',
            kb.Key.end: 'n8',  # 'Af',
            kb.Key.insert: 'dd',
            kb.Key.f1: 'su',
            kb.Key.f2: 'sd',
            kb.Key.f3: 'tu',
            kb.Key.f4: 'td',
            kb.Key.f5: 'damp',
            kb.Key.f6: 'hold',
            kb.Key.num_lock: 'rec',
            kb.Key.f9: 'm1',
            kb.Key.f10: 'm2',
            kb.Key.f11: 'm3',
            kb.Key.f12: 'cut',
        }.get(key, None)
    return returnCmd


def linspace(s, e, num):  # seems faster than np.linspace
    return np.arange(num) / num * (e - s) + s


def damper(initFrame, dampFactor, outputSize=bufferSize):
    return np.exp(-dampFactor / sampleRate
                  * np.arange(initFrame, initFrame + outputSize))


def getSignal(freq, mode=1):
    ampList = None
    freqList = None
    if mode == 1:
        return (np.sin(2 * np.pi * freq / sampleRate
                       * np.arange(bIdx * bufferSize,
                                   (bIdx + 1) * bufferSize))
                for bIdx in it.count())
    elif mode == 2:
        ampList = [4, 2, 1]
        freqList = [freq, freq * 1.5, freq * 3]
    elif mode == 3:
        ampList = [4, 2, 1, 2]
        freqList = [freq, freq * 2, freq * 4, freq / 2]
    else:
        raise ValueError("Unknown signal mode")
    ampList = [i / np.sum(np.abs(ampList)) for i in ampList]
    return (sum(amp * np.sin(2 * np.pi * freqEle / sampleRate
                             * np.arange(bIdx * bufferSize,
                                         (bIdx + 1) * bufferSize))
                for (amp, freqEle) in zip(ampList, freqList))
            for bIdx in it.count())


class MusicNote:
    genObj = None
    noteIdx = 12
    name = None
    mode = 1
    doNaturalDamping = False
    naturalDampedBufCount = 0
    isInEffect = True
    justStarted = True

    def __init__(self, noteIdx, mode=1):
        self.genObj = getSignal(getFreq(noteIdx),
                                mode=mode)
        self.mode = mode
        self.noteIdx = noteIdx
        self.isInEffect = True
        self.doNaturalDamping = False
        self.justStarted = True
        self.naturalDampedBufCount = 0
        self.name = noteNames[self.noteIdx % 12] + str(self.noteIdx // 12)
        if self.mode != 1:
            self.name += '_' + str(self.mode)

    def __iter__(self):
        return self.genObj

    def __next__(self):
        res = next(self.genObj, None)  # should not be None, gen is infinite
        if res is None or not self.isInEffect:
            self.isInEffect = False
            raise StopIteration
        else:
            if self.justStarted:
                damp = None
                if self.naturalDampedBufCount == 0:  # is new sound
                    damp = linspace(0, 1, bufferSize) ** 2
                else:  # renew from damp
                    damp = linspace(np.exp(-naturalDampingFactor
                                           * self.naturalDampedBufCount
                                           * bufferSize / sampleRate),
                                    1, bufferSize)
                res *= damp
                self.justStarted = False
            if self.doNaturalDamping:  # TODO check if can change to elif
                damp = damper(self.naturalDampedBufCount * bufferSize,
                              naturalDampingFactor)
                res *= damp
                self.naturalDampedBufCount += 1
                if self.naturalDampedBufCount >= naturalDampingCutoffCount:
                    self.isInEffect = False
                    self.naturalDampedBufCount = 0
                    res *= np.arange(bufferSize - 1, -1, -1) / bufferSize
            return res

    def reset(self):
        self.justStarted = (not self.isInEffect) or self.doNaturalDamping
        self.isInEffect = True
        self.doNaturalDamping = False

    def initDamping(self):
        if self.isInEffect:
            self.doNaturalDamping = True
            self.naturalDampedBufCount = 0


def getNoteIdx(triggeredNoteIdx, bOffset=None):
    if bOffset is None:
        bOffset = bandOffset + bandOffset_adjust
    return np.clip(np.clip(bOffset, 1, 6) * 12
                   + triggeredNoteIdx + noteTransposeOffset,
                   12, 83)


def triggerNote(triggeredNoteIdx):
    global activeNotesList
    clippedNoteIdx = getNoteIdx(triggeredNoteIdx)
    noteTriggered = (clippedNoteIdx, signalMode)
    if noteTriggered in activeNotesList:
        activeNotesList[noteTriggered].reset()
    else:
        activeNotesList[noteTriggered] = MusicNote(noteIdx=clippedNoteIdx,
                                                   mode=signalMode)


def releaseNote(triggeredNoteIdx):
    global activeNotesList
    if doReleaseDampAll:
        for band in range(1, 7):
            testNoteIdx = (getNoteIdx(triggeredNoteIdx, band), signalMode)
            if testNoteIdx in activeNotesList \
                    and not activeNotesList[testNoteIdx].doNaturalDamping:
                activeNotesList[testNoteIdx].initDamping()
    else:
        noteTriggered = (getNoteIdx(triggeredNoteIdx), signalMode)
        if noteTriggered in activeNotesList \
                and not activeNotesList[noteTriggered].doNaturalDamping:
            activeNotesList[noteTriggered].initDamping()


def toggleRecording():
    global doRecording
    global recordedBuffer
    global recordedBufferPlayPtr
    if doRecording is None:
        print("start recording")
        doRecording = True
        recordedBuffer = []
    elif doRecording:
        print("done recording, start playing")
        doRecording = False
        recordedBufferPlayPtr = 0
    else:
        print("stop playing, cleaning record")
        doRecording = None
        recordedBuffer = []


def onPressCallback(key):
    global bandOffset
    global bandOffset_adjust
    global manualDampingIsActive
    global globalVolume
    global doNotesHolding
    global noteTransposeOffset
    cmd = getCommandFromKey(key)
    if cmd is None:
        pass
    elif cmd == 'q':
        print("quitting")
        global mainLoopIsKilled
        mainLoopIsKilled = True
    elif cmd in noteCmdList:
        triggerNote(int(cmd[1:]))
    elif cmd == 'dd':
        for note in activeNotesList.values():
            if note.isInEffect and not note.doNaturalDamping:
                note.initDamping()
    elif cmd in ('o1', 'o2', 'o3', 'o4', 'o5', 'o6'):
        bandOffset = int(cmd[1])
        print(f"offset : {bandOffset}")
    elif cmd in ('su', 'sd'):
        bandOffset_adjust = (1 if cmd == 'su' else -1)
        print("offset adjust: "
              + ("+1" if bandOffset_adjust == 1 else "-1")
              + f", current: {np.clip(bandOffset + bandOffset_adjust, 1, 6)}")
    elif cmd in ('tu', 'td'):
        noteTransposeOffset = 4 * (1 if cmd == 'tu' else -1)
    elif cmd in ('vu', 'vd'):
        globalVolume = np.clip(globalVolume + (1 if cmd == 'vu' else -1),
                               0, 100)
        print(f"vol: {globalVolume}")
    elif cmd == 'damp':
        manualDampingIsActive = True
    elif cmd == 'hold':
        doNotesHolding = True


def onReleaseCallback(key):
    global bandOffset
    global bandOffset_adjust
    global signalMode
    global manualDampingIsActive
    global doNotesHolding
    global doReleaseDampAll
    global noteTransposeOffset
    cmd = getCommandFromKey(key)
    if cmd is None:
        pass
    elif cmd in noteNames:
        releaseNote(int(cmd[1:]))
    elif cmd == 'damp':
        manualDampingIsActive = None
    elif cmd in ('su', 'sd'):
        bandOffset_adjust = 0
        print(f"offset adjust: 0, current: {bandOffset}")
    elif cmd == 'hold':
        doNotesHolding = False
    elif cmd == 'rec':
        toggleRecording()
    elif cmd == 'cut':
        doReleaseDampAll = not doReleaseDampAll
        print("release mode: "
              + ("all" if doReleaseDampAll else "current only"))
    elif cmd in ('m1', 'm2', 'm3'):
        signalMode = int(cmd[1])
        print(f"tone: {signalMode}")
    elif cmd in ('tu', 'td'):
        noteTransposeOffset = 0
        print("No transpose")


def getCurrentActiveNoteBuffers():
    activeNotesListCopy = activeNotesList.copy()
    activeNotesItems = tuple(v
                             for v in activeNotesListCopy.values()
                             if v.isInEffect)
    lenActiveNoteItems = len(activeNotesItems)
    if lenActiveNoteItems == 0:
        return (0, np.zeros(bufferSize), list())
    else:
        return (lenActiveNoteItems,
                sum(next(note) for note in activeNotesItems),
                list(note.name for note in activeNotesItems))


def playBuffer(buffer):
    buffer *= globalVolume / 100
    streamObj.write(buffer.astype(np.float32,
                                  casting='same_kind',
                                  copy=False).tobytes())


paObj = pa.PyAudio()
streamObj = paObj.open(rate=sampleRate,
                       channels=1,
                       format=pa.paFloat32,
                       output=True)
kbListener = kb.Listener(on_press=onPressCallback,
                         on_release=onReleaseCallback,
                         suppress=not args.nosuppress)
streamObj.start_stream()
kbListener.start()
while not mainLoopIsKilled:
    currentBufTuple = getCurrentActiveNoteBuffers()
    denominator = None
    pass
    previousActiveNoteCount = currentBufTuple[0]
kbListener.stop()
streamObj.stop_stream()
streamObj.close()
paObj.terminate()
