import argparse
import subprocess
import json

parser = argparse.ArgumentParser()
parser.add_argument('target',
                    nargs='*',
                    help="Names of packages to be checked. "
                    "Leave empty to find top-level packages")
args = parser.parse_args()

packageList = json.loads(subprocess.run(['pipdeptree',
                                         '--all',
                                         '--json'],
                                        stdout=subprocess.PIPE)
                         .stdout.decode())

depTree = dict()
for node in packageList:
    pacName = node['package']['key']
    depTree[pacName] = (depTree.get(pacName, list())
                        + [d['key'] for d in node['dependencies']])
affTree = dict()
for pacName in depTree:
    if pacName not in affTree:
        affTree[pacName] = list()
    for depName in depTree[pacName]:
        affTree[depName] = (affTree.get(depName, list()) + [pacName, ])


def findHighestInDepChain(targetPacName):
    if len(affTree[targetPacName]) == 0:
        return set([targetPacName, ])
    else:
        returnSet = set()
        for pacName in affTree[targetPacName]:
            returnSet.update(findHighestInDepChain(pacName))
        return returnSet


def getSubDep(targetPacName):
    depSet = set()
    depSet.add(targetPacName)
    for pacName in depTree[targetPacName]:
        depSet.update(getSubDep(pacName))
    return depSet


# better algo?
def queryRemovable(targetPacName):
    removableList = set()
    for pacName in getSubDep(targetPacName):
        highestList = list(findHighestInDepChain(pacName))
        if len(highestList) == 1 and highestList[0] == targetPacName:
            removableList.add(pacName)
    return removableList


def getTopLevelPac():
    return [pacName
            for pacName in depTree.keys()
            if len(affTree[pacName]) == 0]


if len(args.target) != 0:
    removablePac = set()
    for pacName in args.target:
        if pacName not in depTree:
            print(f"{pacName} is not installed")
        else:
            removablePac.update(queryRemovable(pacName))
    if len(removablePac) != 0:
        print(" ".join(sorted(removablePac)))
else:
    topLevelList = getTopLevelPac()
    if len(topLevelList) != 0:
        print(" ".join(sorted(topLevelList)))
