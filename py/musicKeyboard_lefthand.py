from pynput import keyboard as kb

import numpy as np
import personalPylib_audio as au

print("Initiating ...")

loopTime = 1. / 256
sampleRate = 48000
bufferSize = int(sampleRate * loopTime)
naturalDampingFactor = 8
naturalDampingCutoffCount = int(0.3 * sampleRate / bufferSize)
manualDampingIsActive = False
manualDampingFactor = 5
manualDampedFrameCount = 0
doSmoothClipping = False

ao = au.AudioOutputInterface(bufferSize=bufferSize,
                             channels=1,
                             sampleRate=sampleRate)
aos = au.AudioOutputSignal
scaleDiffFactor = 2**(1 / 12)
keyToScaleName = {
    k: n
    for (k, n)
    in zip([*[kb.KeyCode(char=c)
              for c
              in ('6', 't', '5', 'r', '4', 'e', '3', 'w', '2', 'q', '1')],
            kb.Key.tab],
           ['C', 'Cs', 'D', 'Ds', 'E', 'F', 'Fs', 'G', 'Af', 'A', 'Bf', 'B'])
}
scaleKeys = keyToScaleName.keys()
freqDict = {
    "C": 440 * scaleDiffFactor ** -9,
    "Cs": 440 * scaleDiffFactor ** -8,
    "D": 440 * scaleDiffFactor ** -7,
    "Ds": 440 * scaleDiffFactor ** -6,
    "E": 440 * scaleDiffFactor ** -5,
    "F": 440 * scaleDiffFactor ** -4,
    "Fs": 440 * scaleDiffFactor ** -3,
    "G": 440 * scaleDiffFactor ** -2,
    "Af": 440 * scaleDiffFactor ** -1,
    "A": 440,
    "Bf": 440 * scaleDiffFactor ** 1,
    "B": 440 * scaleDiffFactor ** 2,
}


def damper(initFrame, dampFactor):
    return np.exp(-dampFactor / sampleRate
                  * np.arange(initFrame, initFrame + bufferSize))


def isNumpadKey(key):
    if hasattr(key, 'vk') and 0x60 <= key.vk <= 0x69:
        return str(key.vk - 0x60)
    else:
        return {
            kb.Key.insert: '0',
            kb.Key.end: '1',
            kb.Key.down: '2',
            kb.Key.page_down: '3',
            kb.Key.left: '4',
            # kb.Key.insert: '5',
            kb.Key.right: '6',
            kb.Key.home: '7',
            kb.Key.up: '8',
            kb.Key.page_up: '9',
        }.get(key, None)


def getSignal(freq):
    # return aos.sineWave(freq,
    #                     duration=None,
    #                     aoObj=ao)
    return aos.fromFourier([16, 1],
                           [freq, freq / 2],
                           ampWeightNormalize=True,
                           duration=None,
                           aoObj=ao)


class MusicNote:
    aosObj = None
    name = None
    doNaturalDamping = False
    naturalDampedFrameCount = 0
    isInEffect = True

    def __init__(self, scaleName, octaveOffset):
        self.aosObj = getSignal(freqDict[scaleName] * 2 ** octaveOffset)
        self.name = (scaleName, octaveOffset)

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


scaleOffset = 0
activeNotes = {}
mainLoopIsKilled = False


def onPressCallback(key):
    # print(key, "pressed")
    global scaleOffset
    global activeNotes
    if key == kb.Key.esc:
        print("quitting")
        global mainLoopIsKilled
        mainLoopIsKilled = True
    elif key in scaleKeys:
        noteTriggered = (keyToScaleName[key], scaleOffset)
        if noteTriggered in activeNotes:
            activeNotes[noteTriggered].reset()
        else:
            activeNotes[noteTriggered] = MusicNote(keyToScaleName[key],
                                                   scaleOffset)
    elif key == kb.KeyCode(char='+'):
        for note in activeNotes.values():
            if note.isInEffect and not note.doNaturalDamping:
                note.initDamping()
    elif key == kb.Key.enter:
        global doSmoothClipping
        doSmoothClipping = True
    numpadKey = isNumpadKey(key)
    if numpadKey in ['7', '9']:
        scaleOffset = (1 if key.vk == 0x67 else -1)
    elif numpadKey == '0':
        global manualDampingIsActive
        manualDampingIsActive = True
    else:
        pass


def onReleaseCallback(key):
    # print(key, "released")
    global scaleOffset
    if key in scaleKeys:
        global activeNotes
        noteTriggered = (keyToScaleName[key], scaleOffset)
        if noteTriggered in activeNotes.keys():
            activeNotes[noteTriggered].initDamping()
    elif key == kb.Key.enter:
        global doSmoothClipping
        doSmoothClipping = False
    numpadKey = isNumpadKey(key)
    if numpadKey in ['7', '9']:
        if scaleOffset == (1 if numpadKey == '7' else -1):
            scaleOffset = 0
    elif numpadKey == '0':
        global manualDampingIsActive
        global manualDampedFrameCount
        manualDampingIsActive = False
        manualDampedFrameCount = 0
    else:
        pass


reportedEmpty = False
kbListener = kb.Listener(on_press=onPressCallback,
                         on_release=onReleaseCallback,
                         suppress=True)
kbListener.start()
print("Initiated")
print("esc: quit")
print("6, t, 5, r, 4, e, 3, w, 2, q, 1, tab: C-B")
print("home, pgup: up/down 1 octave")
print("insert: slow damp")
print("+: clear all")
print("enter: clip")
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
    ao.play(activeNoteBuf, smoothClip=doSmoothClipping)
kbListener.stop()
