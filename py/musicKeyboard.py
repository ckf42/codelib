# TODO different temperament
# TODO different tone
# TODO transpose in keys?
# TODO no dependency on personalPylib_audio? may need naked portaudio
# TODO check portability?

from pynput import keyboard as kb
import numpy as np
import argparse
import personalPylib_audio as au

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
args = parser.parse_args()


print("Initiating ...")


def printDebugMsg(*msg):
    if args.debug:
        print(*msg)


def toName(name):
    if isinstance(name, str):
        return name
    return name[0] + str(name[1]) + '_' + str(name[2])


plt = None
if args.debug:
    import matplotlib.pyplot as plt

# unitTimeLength = 1. / 30
unitTimeLength = args.length
# sampleRate = 48000
sampleRate = args.sr
bufferSize = int(sampleRate * unitTimeLength)
printDebugMsg(f"bufferSize: {bufferSize}")

naturalDampingFactor = 9
# kill below ~5%
naturalDampingCutoffCount = int(np.log(1 / 0.05)
                                / naturalDampingFactor
                                * sampleRate / bufferSize)
manualDampingIsActive = False
manualDampingFactor = 3
manualDampedFrameCount = 0

printDebugMsg(f"naturalDampingCutoffCount: {naturalDampingCutoffCount}")

scaleOffset = 3
scaleOffset_adjust = 0
signalMode = 1
globalVolume = 100
doNotesHolding = False
doRecording = None
recordedBuffer = []
recordedBufferPlayPtr = 0
doReleaseDampAll = True

ao = au.AudioOutputInterface(bufferSize=bufferSize,
                             channels=1,
                             sampleRate=sampleRate)
aos = au.AudioOutputSignal

scaler = 2 ** (1 / 12)
freqDict = {  # at C2-B2, equal temperament
    "C": 110 * scaler ** -9,
    "Cs": 110 * scaler ** -8,
    "D": 110 * scaler ** -7,
    "Ds": 110 * scaler ** -6,
    "E": 110 * scaler ** -5,
    "F": 110 * scaler ** -4,
    "Fs": 110 * scaler ** -3,
    "G": 110 * scaler ** -2,
    "Af": 110 * scaler ** -1,
    "A": 110,
    "Bf": 110 * scaler ** 1,
    "B": 110 * scaler ** 2,
}
freqDict = {k: round(v, 4) for (k, v) in freqDict.items()}
scaleNames = freqDict.keys()


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
            # kb.Key.f9: 'm1',
            # kb.Key.f10: 'm2',
            # kb.Key.f11: 'm3',
            kb.Key.num_lock: 'rec',
            kb.Key.f12: 'cut',
            kb.Key.f9: 'm1',
            kb.Key.f10: 'm2',
            kb.Key.f11: 'm3',
        }.get(key, None)
    return returnCmd


def damper(initFrame, dampFactor, outputSize=bufferSize):
    return np.exp(-dampFactor / sampleRate
                  * np.arange(initFrame, initFrame + outputSize))


def getSignal(freq, mode=1):
    if mode == 1:
        return aos.sineWave(freq,
                            duration=None,
                            aoObj=ao)
    elif mode == 2:
        return aos.fromFourier([4, 2, 1],
                               [freq, freq * 1.5, freq * 3],
                               ampWeightNormalize=True,
                               duration=None,
                               aoObj=ao)
    elif mode == 3:
        return aos.fromFourier([4, 2, 1, 2],
                               [freq, freq * 2, freq * 4, freq / 2],
                               ampWeightNormalize=True,
                               duration=None,
                               aoObj=ao)
    else:
        raise ValueError("Unknown signal mode")


class MusicNote:
    aosObj = None
    name = None
    doNaturalDamping = False
    naturalDampedBufCount = 0
    isInEffect = True
    justStarted = True

    def __init__(self, scaleName, octaveOffset, mode=1):
        self.aosObj = getSignal(freqDict[scaleName] * 2 ** (octaveOffset - 2),
                                mode=mode)
        # self.name = (scaleName, octaveOffset, mode)
        self.name = (scaleName, octaveOffset, mode)
        self.isInEffect = True
        self.doNaturalDamping = False
        self.justStarted = True
        self.naturalDampedBufCount = 0

    def __iter__(self):
        return self.aosObj.__iter__()

    def __next__(self):
        res = next(self.aosObj, None)  # should not be None, gen is infinite
        if res is None or not self.isInEffect:
            self.isInEffect = False
            raise StopIteration
        else:
            if self.justStarted:
                damp = None
                if self.naturalDampedBufCount == 0:  # is new sound
                    print("starting", toName(self.name))
                    damp = np.linspace(0, 1,
                                       num=bufferSize, endpoint=False) ** 2
                else:  # renew from damp
                    print("renewing", toName(self.name))
                    damp = np.linspace(np.exp(-naturalDampingFactor
                                              * self.naturalDampedBufCount
                                              * bufferSize / sampleRate),
                                       1,
                                       num=bufferSize,
                                       endpoint=False)
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
                    res *= np.linspace(1, 0, num=bufferSize, endpoint=False)
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
        clippedScaleOffset = max(min(scaleOffset + scaleOffset_adjust, 6), 1)
        # noteTriggered = (cmd, clippedScaleOffset, signalMode)
        noteTriggered = (cmd, clippedScaleOffset, signalMode)
        if noteTriggered in activeNotes:
            activeNotes[noteTriggered].reset()
        else:
            activeNotes[noteTriggered] = MusicNote(cmd,
                                                   clippedScaleOffset,
                                                   signalMode)
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
        globalVolume = min(globalVolume + 5, 100)
        print(f"vol: {globalVolume}")
    elif cmd == 'vd':
        globalVolume = max(globalVolume - 5, 0)
        print(f"vol: {globalVolume}")
    elif cmd == 'su':
        scaleOffset_adjust = 1
        print("offset adjust: +1, "
              f"current: {max(min(scaleOffset + scaleOffset_adjust, 6), 1)}")
    elif cmd == 'sd':
        scaleOffset_adjust = -1
        print("offset adjust: -1, "
              f"current: {max(min(scaleOffset + scaleOffset_adjust, 6), 1)}")
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


activeNoteBuf = np.zeros(bufferSize)
debugBuf = np.zeros(0)
reportedEmpty = False
previousActiveNoteCount = 0
kbListener = kb.Listener(on_press=onPressCallback,
                         on_release=onReleaseCallback,
                         suppress=True)
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
                / np.linspace(previousActiveNoteCount,
                              activeNoteCount,
                              num=bufferSize, endpoint=False)
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
        activeNoteBuf *= np.linspace(
            np.exp(-manualDampingFactor * manualDampedFrameCount / sampleRate),
            1,
            num=bufferSize, endpoint=False)
        manualDampedFrameCount = 0
        manualDampingIsActive = False
    ao.playNpArray(activeNoteBuf,
                   volume=globalVolume / 100,
                   keepActive=True)
    if doRecording is True:
        recordedBuffer.append(activeNoteBuf)
    if args.debug:
        debugBuf = np.hstack((debugBuf, activeNoteBuf))
        currentTime += bufferSize / sampleRate
        print(f"timestamp: {round(currentTime, 3)}")
        print("----------")
    previousActiveNoteCount = activeNoteCount
kbListener.stop()
if args.debug:
    plt.plot(np.linspace(0, len(debugBuf) / sampleRate, len(debugBuf),
                         endpoint=False),
             debugBuf)
    plt.show()