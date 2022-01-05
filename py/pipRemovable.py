import argparse
import subprocess
import json

parser = argparse.ArgumentParser()
parser.add_argument("target",
                    nargs='*',
                    help="Names of packages to be checked. "
                    "Leave empty to find top-level packages")
parser.add_argument("--protect",
                    nargs='*',
                    help="Omit these packages when checking")
args = parser.parse_args()

packageList = json.loads(subprocess.run(['pipdeptree',
                                         '--all',
                                         '--json'],
                                        stdout=subprocess.PIPE)
                         .stdout.decode())
# O(E)
depTree = dict()
for node in packageList:
    pacName = node['package']['key']
    depTree[pacName] = (depTree.get(pacName, list())
                        + [d['key'] for d in node['dependencies']])
# O(E)
affTree = dict()
for pacName in depTree:
    if pacName not in affTree:
        affTree[pacName] = list()
    for depName in depTree[pacName]:
        affTree[depName] = (affTree.get(depName, list()) + [pacName, ])
removableRecord = dict()


def isRemovable(targetPacName):
    if removableRecord.get(targetPacName, None) is not None:
        return removableRecord[targetPacName]
    removableStatusDecision = None
    if len(affTree[targetPacName]) == 0:
        removableStatusDecision = False
    else:
        removableStatusDecision = all([isRemovable(pacName)
                                       for pacName in affTree[targetPacName]])
    removableRecord[targetPacName] = removableStatusDecision
    return removableStatusDecision


def updateSubDepStatus(targetPacName):
    if not isRemovable(targetPacName):
        return
    for pacName in depTree[targetPacName]:
        updateSubDepStatus(pacName)


def getTopLevelPac():
    return [pacName
            for pacName in depTree.keys()
            if len(affTree[pacName]) == 0]


if len(args.target) != 0:
    for pacName in args.target:
        if pacName not in depTree:
            print(f"{pacName} is not installed")
        else:
            # mark package as removable / maybe-removable
            removableRecord[pacName] = (True
                                        if len(affTree[pacName]) == 0
                                        else None)
    if args.protect is None:
        args.protect = ["pip", ]
    else:
        args.protect.append("pip")
    for pacName in (args.protect if args.protect is not None else list()):
        if pacName not in depTree:
            print(f"{pacName} is not installed")
        else:
            # mark package as NOT-removable
            removableRecord[pacName] = False
    targetPacList = list(removableRecord.keys())
    for pacName in targetPacList:
        updateSubDepStatus(pacName)
    removablePac = [pacName
                    for pacName in removableRecord.keys()
                    if removableRecord[pacName]]  # if is TRUE
    if len(removablePac) != 0:
        print(" ".join(sorted(removablePac)))
else:
    topLevelList = getTopLevelPac()
    if len(topLevelList) != 0:
        print(" ".join(sorted(topLevelList)))
