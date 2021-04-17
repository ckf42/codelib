# TODO simpler main loop
# TODO different tone
# TODO transpose in keys?
# TODO check portability?

import numpy as np
import argparse
from pynput import keyboard as kb
import pyaudio as pa
import itertools as it

# cli arguments with argparse
parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true',
                    help="Toggle debug mode")
parser.add_argument('--length', type=float, default=1 / 30,
                    help="Length of a time unit, in seconds. "
                    "The shortest length of a signal, "
                    "also the reaction time. "
                    "Default: 1/30")
parser.add_argument('--sr', type=int, default=48000,
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


print("Initiating ...")


def printDebugMsg(*msg):
    if args.debug:
        print(*msg)


def toName(name):
    if isinstance(name, str):
        return name
    returnStr = name[0] + str(name[1])
    if name[2] != 1:
        returnStr += '_' + str(name[2])
    return returnStr


# for debugging amp plot
plt = None
if args.debug:
    import matplotlib.pyplot as plt

# pyaudio parameters
unitTimeLength = args.length
sampleRate = args.sr
bufferSize = int(sampleRate * unitTimeLength)
printDebugMsg(f"bufferSize: {bufferSize}")
# damping, kill natural damping below ~5%
naturalDampingFactor = 9
naturalDampingCutoffCount = int(np.log(1 / 0.05)
                                / naturalDampingFactor
                                * sampleRate / bufferSize)
manualDampingIsActive = False
manualDampingFactor = 3
manualDampedFrameCount = 0
printDebugMsg(f"naturalDampingCutoffCount: {naturalDampingCutoffCount}")
# octave scale parameter
scaleOffset = 3
scaleOffset_adjust = 0
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
# fundamental signals
scaleNames = ["C", "Cs", "D", "Ds", "E", "F", "Fs", "G", "Af", "A", "Bf", "B"]
# freq for second octave, C2-B2
# equal temperament
basicFreq = [round(110 * 2 ** (k / 12), 4) for k in range(-9, 3)]
if args.just:  # Just intonation
    basicFreq = list(map(lambda x: round(110 / 27 * 16 * x, 4),
                         [1, 256 / 243, 9 / 8, 32 / 27,
                         81 / 64, 4 / 3, 729 / 512, 3 / 2,
                         128 / 81, 27 / 16, 16 / 9, 243 / 128]))
freqDict = {k: v for (k, v) in zip(scaleNames, basicFreq)}


def getFreq(scaleName, octaveOffset):
    return freqDict[scaleName] * 2. ** (octaveOffset - 2)


paObj = pa.PyAudio()
streamObj = paObj.open(rate=sampleRate,
                       channels=1,
                       format=pa.paFloat32,
                       output=True)


def getCommandFromKey(key):
    returnCmd = None
    if hasattr(key, 'vk'):
        returnCmd = {
            103: 'C',
            111: 'Cs',
            106: 'D',
            109: 'Ds',
            100: 'E',
            104: 'F',
            105: 'Fs',
            107: 'G',
            97: 'Af',
            101: 'A',
            12: 'A',
            102: 'Bf',
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
            kb.Key.enter: 'B',
            kb.Key.esc: 'q',
            kb.Key.home: 'C',
            kb.Key.up: 'F',
            kb.Key.page_up: 'Fs',
            kb.Key.left: 'E',
            kb.Key.right: 'Bf',
            kb.Key.end: 'Af',
            kb.Key.insert: 'dd',
            kb.Key.f1: 'su',
            kb.Key.f2: 'sd',
            kb.Key.f3: 'damp',
            kb.Key.f4: 'hold',
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
    name = None
    doNaturalDamping = False
    naturalDampedBufCount = 0
    isInEffect = True
    justStarted = True

    def __init__(self, scaleName, octaveOffset, mode=1):
        self.genObj = getSignal(getFreq(scaleName, octaveOffset),
                                mode=mode)
        # self.name = (scaleName, octaveOffset, mode)
        self.name = (scaleName, octaveOffset, mode)
        self.isInEffect = True
        self.doNaturalDamping = False
        self.justStarted = True
        self.naturalDampedBufCount = 0

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
                    print("starting", toName(self.name))
                    damp = linspace(0, 1, bufferSize) ** 2
                else:  # renew from damp
                    print("renewing", toName(self.name))
                    damp = linspace(np.exp(-naturalDampingFactor
                                           * self.naturalDampedBufCount
                                           * bufferSize / sampleRate),
                                    1, bufferSize)
                res *= damp
                self.justStarted = False
            if self.doNaturalDamping:  # TODO check if can change to elif
                printDebugMsg("natural damping",
                              toName(self.name),
                              self.naturalDampedBufCount)
                damp = damper(self.naturalDampedBufCount * bufferSize,
                              naturalDampingFactor)
                res *= damp
                self.naturalDampedBufCount += 1
                if self.naturalDampedBufCount >= naturalDampingCutoffCount:
                    self.isInEffect = False
                    self.naturalDampedBufCount = 0
                    print(toName(self.name), "dying")
                    res *= np.arange(bufferSize - 1, -1, -1) / bufferSize
            return res

    def reset(self):
        self.justStarted = (not self.isInEffect) or self.doNaturalDamping
        self.isInEffect = True
        self.doNaturalDamping = False

    def initDamping(self):
        if not self.isInEffect:
            return
        print("start natural damping", toName(self.name))
        self.doNaturalDamping = True
        self.naturalDampedBufCount = 0


activeNotes = {}
mainLoopIsKilled = False


def onPressCallback(key):
    printDebugMsg(key, 'pressed')
    global scaleOffset
    global scaleOffset_adjust
    global activeNotes
    global manualDampingIsActive
    global globalVolume
    global doNotesHolding
    cmd = getCommandFromKey(key)
    if cmd is None:
        pass
    elif cmd == 'q':
        print("quitting")
        global mainLoopIsKilled
        mainLoopIsKilled = True
    elif cmd in scaleNames:
        clippedScaleOffset = np.clip(scaleOffset + scaleOffset_adjust, 1, 6)
        noteTriggered = (cmd, clippedScaleOffset, signalMode)
        if noteTriggered in activeNotes:
            activeNotes[noteTriggered].reset()
        else:
            activeNotes[noteTriggered] \
                = MusicNote(scaleName=cmd,
                            octaveOffset=clippedScaleOffset,
                            mode=signalMode)
    elif cmd == 'dd':
        for note in activeNotes.values():
            if note.isInEffect and not note.doNaturalDamping:
                note.initDamping()
    elif cmd in ('o1', 'o2', 'o3', 'o4', 'o5', 'o6'):
        scaleOffset = int(cmd[1])
        print(f"offset : {scaleOffset}")
    elif cmd == 'damp':
        manualDampingIsActive = True
    elif cmd == 'vu':
        globalVolume = min(globalVolume + 1, 100)
        print(f"vol: {globalVolume}")
    elif cmd == 'vd':
        globalVolume = max(globalVolume - 1, 0)
        print(f"vol: {globalVolume}")
    elif cmd == 'su':
        scaleOffset_adjust = 1
        print("offset adjust: +1, "
              f"current: {np.clip(scaleOffset + scaleOffset_adjust, 1, 6)}")
    elif cmd == 'sd':
        scaleOffset_adjust = -1
        print("offset adjust: -1, "
              f"current: {np.clip(scaleOffset + scaleOffset_adjust, 1, 6)}")
    elif cmd == 'hold':
        doNotesHolding = True


def onReleaseCallback(key):
    printDebugMsg(key, 'released')
    global scaleOffset
    global scaleOffset_adjust
    global activeNotes
    global signalMode
    global manualDampingIsActive
    global doNotesHolding
    global doRecording
    global recordedBuffer
    global recordedBufferPlayPtr
    global doReleaseDampAll
    cmd = getCommandFromKey(key)
    if cmd is None:
        pass
    elif cmd in scaleNames:
        if doReleaseDampAll:
            for scale in range(1, 7):
                testNoteName = (cmd, scale, signalMode)
                if testNoteName in activeNotes \
                        and not activeNotes[testNoteName].doNaturalDamping:
                    activeNotes[testNoteName].initDamping()
        else:
            noteTriggered = (cmd,
                             max(min(scaleOffset + scaleOffset_adjust,
                                     6),
                                 1),
                             signalMode)
            if noteTriggered in activeNotes \
                    and not activeNotes[noteTriggered].doNaturalDamping:
                activeNotes[noteTriggered].initDamping()
    elif cmd == 'damp':
        manualDampingIsActive = None
    elif cmd in ('su', 'sd'):
        scaleOffset_adjust = 0
        print(f"offset adjust: 0, current: {scaleOffset}")
    elif cmd == 'hold':
        doNotesHolding = False
    elif cmd == 'rec':
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
    elif cmd == 'cut':
        doReleaseDampAll = not doReleaseDampAll
        print("release mode: "
              + ("all" if doReleaseDampAll else "current only"))
    elif cmd in ('m1', 'm2', 'm3'):
        signalMode = int(cmd[1])
        print(f"tone: {signalMode}")


def playBuffer(buffer):
    buffer *= globalVolume / 100
    streamObj.write(buffer.astype(np.float32,
                                  casting='same_kind',
                                  copy=False).tobytes())


activeNoteBuf = np.zeros(bufferSize)
debugBuf = np.zeros(0)
reportedEmpty = False
previousActiveNoteCount = 0
kbListener = kb.Listener(on_press=onPressCallback,
                         on_release=onReleaseCallback,
                         suppress=not args.nosuppress)
kbListener.start()
print("""Initiated

Instruction:
esc: quit
home, /, *, -, left, up, pgup, +, end, middle, right, enter: C-B
insert: clear all
1-6: move to octave
f1, f2: temporal octave up/down
f3: damp all
f4: hold all
[, ]: volume up/down
numlock: toggle recording
f12: toggle cut
""")

print(f"offset : {scaleOffset}")
currentTime = 0
streamObj.start_stream()
while not mainLoopIsKilled:
    if args.debug:
        print(f"timestamp: {round(currentTime, 3)}")
    # to avoid activeNotes changing when processing
    activeNotesCopy = activeNotes.copy()
    activeNoteNames = list(noteName
                           for noteName in activeNotesCopy
                           if activeNotesCopy[noteName].isInEffect)
    activeNoteBufList = list(next(activeNotesCopy[noteName])
                             for noteName in activeNoteNames)
    if doNotesHolding:
        print("holding")
        for noteName in activeNoteNames:
            activeNotesCopy[noteName].reset()  # obj by ref
    if doRecording is False:
        activeNoteNames.append("record")
        activeNoteBufList.append(recordedBuffer[recordedBufferPlayPtr])
        recordedBufferPlayPtr = (recordedBufferPlayPtr + 1) \
            % len(recordedBuffer)
    activeNoteCount = len(activeNoteNames)
    if activeNoteCount != 0:
        print("playing", *map(toName, activeNoteNames))
        reportedEmpty = False
        if 0 != previousActiveNoteCount != activeNoteCount:
            printDebugMsg("weight shifting",
                          previousActiveNoteCount,
                          "->",
                          activeNoteCount)
            # fade in/out on averaging
            # NOTE
            # currently,
            # we are using linear shift in denominator
            # for k**p fade in and if we do linear shift in weight
            # with n = activeNoteCount
            # and m = activeNoteCount  - previousActiveNoteCount,
            # stability depends whether the inequality
            # m k^p - (m+n) k^(p-1) + n >= 0
            # holds for all k in [0, 1] and for all n >= 1, all m
            # if p = 2, is fine when m <= n
            # so should be fine
            # if activeNoteCount / previousActiveNoteCount - 1 is small
            activeNoteBuf = sum(activeNoteBufList) \
                / linspace(previousActiveNoteCount,
                           activeNoteCount,
                           bufferSize)
            if args.debug and np.any(activeNoteBuf > 1):
                mainLoopIsKilled = True
        else:
            activeNoteBuf = sum(activeNoteBufList) / activeNoteCount
    else:
        activeNoteBuf = np.zeros(bufferSize)
        if not reportedEmpty:
            print("no active note")
            reportedEmpty = True
    if manualDampingIsActive is True:
        print("manual damping")
        activeNoteBuf *= damper(manualDampedFrameCount,
                                manualDampingFactor)
        manualDampedFrameCount += bufferSize
    elif manualDampingIsActive is None:
        activeNoteBuf *= linspace(np.exp(-manualDampingFactor
                                         * manualDampedFrameCount
                                         / sampleRate),
                                  1,
                                  bufferSize)
        manualDampedFrameCount = 0
        manualDampingIsActive = False
    playBuffer(activeNoteBuf)
    if doRecording is True:
        recordedBuffer.append(activeNoteBuf)
    if args.debug:
        debugBuf = np.hstack((debugBuf, activeNoteBuf))
        currentTime += bufferSize / sampleRate
        print(f"timestamp: {round(currentTime, 3)}")
        print("----------")
    previousActiveNoteCount = activeNoteCount
kbListener.stop()
if streamObj.is_active():
    streamObj.stop_stream()
streamObj.close()
paObj.terminate()
if args.debug:
    plt.plot(np.linspace(0, len(debugBuf) / sampleRate,
                         num=len(debugBuf),
                         endpoint=False),
             debugBuf)
    plt.show()
