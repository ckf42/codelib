from pynput import keyboard as kb

import numpy as np
import personalPylib_audio as au

print("Initiating ...")

loopTime = 1. / 128
sampleRate = 48000
bufferSize = int(sampleRate * loopTime)

naturalDampingFactor = 10
naturalDampingCutoffCount = int(0.25 * sampleRate / bufferSize)
manualDampingIsActive = False
manualDampingFactor = 3
manualDampedFrameCount = 0

scaleOffset = 2
signalMode = 1

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
            192: 's0',
            49: 's1',
            50: 's2',
            51: 's3',
            52: 's4',
            # 53: 's5',
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
            kb.Key.f1: 'm1',
            kb.Key.f2: 'm2',
            kb.Key.f3: 'm3',
            kb.Key.f4: 'm4',
            kb.Key.f9: 'damp',
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
        return aos.fromFourier([4 / 6, 1 / 6, 1 / 6],
                               [freq, freq * scaler ** 16, freq * scaler ** 32],
                               duration=None,
                               aoObj=ao)
    elif mode == 4:
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
    elif cmd[0] == 's':
        scaleOffset = int(cmd[1])
        print(scaleOffset)
    elif cmd[0] == 'm':
        signalMode = int(cmd[1])
        print(signalMode)
    elif cmd == 'damp':
        manualDampingIsActive = True


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


reportedEmpty = False
kbListener = kb.Listener(on_press=onPressCallback,
                         on_release=onReleaseCallback,
                         suppress=True)
kbListener.start()
print("Initiated")
print("esc: quit")
print("7, /, *, -, left, up, pgup, +, end, middle, right, enter: C-B")
print("~, 1, 2, 3, 4: move to octave")
print("insert: clear all")
print("f1-f4: different sound")
print("f9: damp all")
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
    ao.play(activeNoteBuf)
kbListener.stop()
