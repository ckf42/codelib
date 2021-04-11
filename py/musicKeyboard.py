from pynput import keyboard as kb

import numpy as np
import personalPylib_audio as au

print("Initiating ...")

loopTime = 1. / 256
sampleRate = 48000
bufferSize = int(sampleRate * loopTime)

naturalDampingFactor = 10
naturalDampingCutoffCount = int(0.25 * sampleRate / bufferSize)
manualDampingIsActive = False
manualDampingFactor = 6
manualDampedFrameCount = 0

scaleOffset = 2
signalMode = 1
globalVolume = 100

ao = au.AudioOutputInterface(bufferSize=bufferSize,
                             channels=1,
                             sampleRate=sampleRate)
aos = au.AudioOutputSignal

scaler = 2**(1 / 12)
freqDict = {
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
scaleNames = ['C', 'Cs', 'D', 'Ds', 'E', 'F', 'Fs', 'G', 'Af', 'A', 'Bf', 'B']


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
            192: 'o0',
            49: 'o1',
            50: 'o2',
            51: 'o3',
            52: 'o4',
            # 53: 'o5',
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
            kb.Key.f3: 'vu',
            kb.Key.f4: 'vd',
            kb.Key.f5: 'damp',
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

    def __init__(self, scaleName, octaveOffset, mode):
        self.aosObj = getSignal(freqDict[scaleName] * 2 ** octaveOffset, mode)
        self.name = (scaleName, octaveOffset, mode)

    def __iter__(self):
        return self.aosObj._genObj

    def __next__(self):
        res = next(self.aosObj, None)  # should not be None, gen is infinite
        if res is None or not self.isInEffect:
            self.isInEffect = False
            raise StopIteration
        else:
            if self.doNaturalDamping:
                damp = damper(self.naturalDampedFrameCount * bufferSize,
                              naturalDampingFactor)
                res *= damp
                self.naturalDampedFrameCount += 1
                if self.naturalDampedFrameCount >= naturalDampingCutoffCount:
                    self.isInEffect = False
            return res

    def reset(self):
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
    global activeNotes
    global signalMode
    global manualDampingIsActive
    global globalVolume
    cmd = getCommandFromKey(key)
    if cmd is None:
        pass
    elif cmd == 'q':
        print("quitting")
        global mainLoopIsKilled
        mainLoopIsKilled = True
    elif cmd in scaleNames:
        noteTriggered = (cmd, scaleOffset, signalMode)
        if noteTriggered in activeNotes:
            activeNotes[noteTriggered].reset()
        else:
            activeNotes[noteTriggered] = MusicNote(cmd,
                                                   scaleOffset,
                                                   signalMode)
    elif cmd == 'dd':
        for note in activeNotes.values():
            if note.isInEffect and not note.doNaturalDamping:
                note.initDamping()
    elif cmd in ('o0', 'o1', 'o2', 'o3', 'o4'):
        scaleOffset = int(cmd[1])
        print(scaleOffset)
    elif cmd in ('m1', 'm2', 'm3', 'm4'):
        signalMode = int(cmd[1])
        print(signalMode)
    elif cmd == 'damp':
        manualDampingIsActive = True
    elif cmd == 'vu':
        globalVolume = min(globalVolume + 5, 100)
        print(f"vol: {globalVolume}")
    elif cmd == 'vd':
        globalVolume = max(globalVolume - 5, 0)
        print(f"vol: {globalVolume}")


def onReleaseCallback(key):
    print(key, 'released')
    global scaleOffset
    global activeNotes
    global manualDampingIsActive
    global manualDampedFrameCount
    cmd = getCommandFromKey(key)
    if cmd is None:
        pass
    elif cmd in scaleNames:
        noteTriggered = (cmd, scaleOffset, signalMode)
        if noteTriggered in activeNotes.keys():
            activeNotes[noteTriggered].initDamping()
    elif cmd == 'damp':
        manualDampingIsActive = False
        manualDampedFrameCount = 0
    elif cmd == 'su':
        scaleOffset = min(scaleOffset + 1, 4)
        print(f"offset: {scaleOffset}")
    elif cmd == 'sd':
        scaleOffset = max(scaleOffset - 1, 0)
        print(f"offset: {scaleOffset}")


reportedEmpty = False
kbListener = kb.Listener(on_press=onPressCallback,
                         on_release=onReleaseCallback,
                         suppress=True)
kbListener.start()
print("Initiated")
print("esc: quit")
print("7, /, *, -, left, up, pgup, +, end, middle, right, enter: C-B")
print("insert: clear all")
print("~, 1, 2, 3, 4: move to octave")
print("f1, f2: octave up/down")
print("f3, f4: volume up/down")
print("f5: damp all")
while not mainLoopIsKilled:
    activeNoteBuf = list(note
                         for note in activeNotes.values()
                         if note.isInEffect)
    noteNames = list(note.name for note in activeNoteBuf)
    if len(noteNames) != 0:
        print(noteNames)
        reportedEmpty = False
    elif not reportedEmpty:
        print("empty")
        reportedEmpty = True
    activeNoteBuf = list(next(gen) for gen in activeNoteBuf)
    if len(activeNoteBuf) == 0:
        activeNoteBuf = np.zeros(bufferSize)
    else:
        activeNoteBuf = sum(activeNoteBuf) / len(activeNoteBuf)
        if manualDampingIsActive:
            print("damping")
            activeNoteBuf *= damper(manualDampedFrameCount,
                                    manualDampingFactor)
            manualDampedFrameCount += bufferSize
    ao.play(activeNoteBuf * (globalVolume / 100))
kbListener.stop()
