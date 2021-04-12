# TODO smooth transition between states (e.g. adding more notes)

from pynput import keyboard as kb
import numpy as np
import argparse
import personalPylib_audio as au

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')
args = parser.parse_args()

print("Initiating ...")

plt = None
if args.debug:
    import matplotlib.pyplot as plt

loopTime = 1. / 20
sampleRate = 48000
bufferSize = int(sampleRate * loopTime)

naturalDampingFactor = 15
naturalDampingCutoffCount = int(0.3 * sampleRate / bufferSize)
manualDampingIsActive = False
manualDampingFactor = 3
manualDampedFrameCount = 0

scaleOffset = 3
scaleOffset_adjust = 0
signalMode = 1
globalVolume = 100
doNotesHolding = False
doRecording = None
recordedBuffer = []
recordedBufferPlayPtr = 0

ao = au.AudioOutputInterface(bufferSize=bufferSize,
                             channels=1,
                             sampleRate=sampleRate)
aos = au.AudioOutputSignal

scaler = 2**(1 / 12)
freqDict = {  # at C2-B2
    "C": round(110 * scaler ** -9, 3),
    "Cs": round(110 * scaler ** -8, 3),
    "D": round(110 * scaler ** -7, 3),
    "Ds": round(110 * scaler ** -6, 3),
    "E": round(110 * scaler ** -5, 3),
    "F": round(110 * scaler ** -4, 3),
    "Fs": round(110 * scaler ** -3, 3),
    "G": round(110 * scaler ** -2, 3),
    "Af": round(110 * scaler ** -1, 3),
    "A": round(110, 3),
    "Bf": round(110 * scaler ** 1, 3),
    "B": round(110 * scaler ** 2, 3),
}
scaleNames = freqDict.keys()


def getCommandFromKey(key):
    if hasattr(key, 'vk'):
        return {
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
    else:
        return {
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
            kb.Key.f5: 'vu',
            kb.Key.f6: 'vd',
            # kb.Key.f9: 'm1',
            # kb.Key.f10: 'm2',
            # kb.Key.f11: 'm3',
            kb.Key.f12: 'rec',
        }.get(key, None)


def damper(initFrame, dampFactor):
    return np.exp(-dampFactor / sampleRate
                  * np.arange(initFrame, initFrame + bufferSize))


def getSignal(freq, mode=1):
    if mode == 1:
        return aos.sineWave(freq,
                            duration=None,
                            aoObj=ao)
    elif mode == 2:
        return aos.fromFourier([4 / 7, 2 / 7, 1 / 7],
                               [freq, freq / 4, freq * 2],
                               duration=None,
                               aoObj=ao)
    elif mode == 3:
        return aos.fromFourier([4 / 9, 2 / 9, 1 / 9, 2 / 9],
                               [freq, freq * 2, freq * 4, freq / 2],
                               duration=None,
                               aoObj=ao)
    else:
        raise ValueError("Unknown signal mode")


class MusicNote:
    aosObj = None
    name = None
    doNaturalDamping = False
    naturalDampedFrameCount = 0
    isInEffect = True
    justStarted = True

    def __init__(self, scaleName, octaveOffset, mode=1):
        self.aosObj = getSignal(freqDict[scaleName] * 2 ** (octaveOffset - 2),
                                mode=1)
        # self.name = (scaleName, octaveOffset, mode)
        self.name = (scaleName, octaveOffset)
        self.reset()

    def __iter__(self):
        return self.aosObj.__iter__()

    def __next__(self):
        res = next(self.aosObj, None)  # should not be None, gen is infinite
        if res is None or not self.isInEffect:
            self.isInEffect = False
            raise StopIteration
        else:
            if self.justStarted:
                res *= np.linspace(np.exp(-naturalDampingFactor
                                          * self.naturalDampedFrameCount
                                          * bufferSize
                                          / sampleRate),
                                   1,
                                   num=bufferSize,
                                   endpoint=True)
                self.justStarted = False
            if self.doNaturalDamping:
                damp = damper(self.naturalDampedFrameCount * bufferSize,
                              naturalDampingFactor)
                res *= damp
                self.naturalDampedFrameCount += 1
                if self.naturalDampedFrameCount >= naturalDampingCutoffCount:
                    self.isInEffect = False
            return res

    def reset(self):
        self.justStarted = (not self.isInEffect) or self.doNaturalDamping
        self.isInEffect = True
        self.doNaturalDamping = False

    def initDamping(self):
        self.doNaturalDamping = True
        self.naturalDampedFrameCount = 0


activeNotes = {}
mainLoopIsKilled = False


def onPressCallback(key):
    print(key, 'pressed')
    global scaleOffset
    global scaleOffset_adjust
    global activeNotes
    # global signalMode
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
        noteTriggered = (cmd, clippedScaleOffset)
        if noteTriggered in activeNotes:
            activeNotes[noteTriggered].reset()
        else:
            activeNotes[noteTriggered] = MusicNote(cmd,
                                                   clippedScaleOffset,
                                                   #    signalMode
                                                   )
    elif cmd == 'dd':
        for note in activeNotes.values():
            if note.isInEffect and not note.doNaturalDamping:
                note.initDamping()
    elif cmd in ('o1', 'o2', 'o3', 'o4', 'o5', 'o6'):
        scaleOffset = int(cmd[1])
        print(f"offset : {scaleOffset}")
    # elif cmd in ('m1', 'm2', 'm3'):
    #     signalMode = int(cmd[1])
    #     print(signalMode)
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
    print(key, 'released')
    global scaleOffset
    global scaleOffset_adjust
    global activeNotes
    # global signalMode
    global manualDampingIsActive
    global manualDampedFrameCount
    global doNotesHolding
    global doRecording
    global recordedBuffer
    global recordedBufferPlayPtr
    cmd = getCommandFromKey(key)
    if cmd is None:
        pass
    elif cmd in scaleNames:
        clippedScaleOffset = max(min(scaleOffset + scaleOffset_adjust, 6), 1)
        # noteTriggered = (cmd, clippedScaleOffset, signalMode)
        noteTriggered = (cmd, clippedScaleOffset)
        if noteTriggered in activeNotes.keys():
            activeNotes[noteTriggered].initDamping()
    elif cmd == 'damp':
        manualDampingIsActive = False
        manualDampedFrameCount = 0
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
            print("done playing, reset everything")
            doRecording = None
            recordedBuffer = []


debugBuf = np.zeros(0)
reportedEmpty = False
kbListener = kb.Listener(on_press=onPressCallback,
                         on_release=onReleaseCallback,
                         suppress=True)
kbListener.start()
print("Initiated")
print("esc: quit")
print("home, /, *, -, left, up, pgup, +, end, middle, right, enter: C-B")
print("insert: clear all")
print("1-6: move to octave")
print("f1, f2: temporal octave up/down")
print("f3: damp all")
print("f4: hold all")
print("f5-6: volume up/down")
print("f12: toggle recording")
while not mainLoopIsKilled:
    # to avoid activeNotes changing when processing
    activeNotesCopy = activeNotes.copy()
    activeNoteBuf = list(noteName
                         for noteName in activeNotesCopy
                         if activeNotesCopy[noteName].isInEffect)
    activeNoteCount = len(activeNoteBuf)
    if activeNoteCount == 0:
        if not reportedEmpty:
            print("empty")
            reportedEmpty = True
        if doRecording is False:
            activeNoteBuf = recordedBuffer[recordedBufferPlayPtr]
            recordedBufferPlayPtr = (recordedBufferPlayPtr + 1) \
                % len(recordedBuffer)
        else:
            activeNoteBuf = np.zeros(bufferSize)
    else:
        print(list(noteName for noteName in activeNoteBuf))
        reportedEmpty = False
        if doNotesHolding:
            print("reseting")
            for noteName in activeNoteBuf:
                activeNotesCopy[noteName].reset()
        activeNoteBuf = list(next(activeNotesCopy[noteName])
                             for noteName in activeNoteBuf)
        activeNoteBuf = sum(activeNoteBuf) / activeNoteCount
        if doRecording is False:
            activeNoteBuf = (recordedBuffer[recordedBufferPlayPtr]
                             + activeNoteBuf * activeNoteCount) \
                / (activeNoteCount + 1)
            recordedBufferPlayPtr = (recordedBufferPlayPtr + 1) \
                % len(recordedBuffer)
    if manualDampingIsActive:
        print("damping")
        activeNoteBuf *= damper(manualDampedFrameCount,
                                manualDampingFactor)
        manualDampedFrameCount += bufferSize
    ao.playNpArray(activeNoteBuf,
                   volume=globalVolume / 100,
                   keepActive=True)
    if doRecording is True:
        recordedBuffer.append(activeNoteBuf)
    if args.debug:
        debugBuf = np.hstack((debugBuf, activeNoteBuf))
kbListener.stop()
if args.debug:
    plt.plot(np.linspace(0, len(debugBuf) / sampleRate, len(debugBuf),
                         endpoint=False),
             debugBuf)
    plt.show()
