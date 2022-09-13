import argparse
import subprocess
import json
# TODO: remove json dependency?

parser = argparse.ArgumentParser()
parser.add_argument("target",
                    nargs='*',
                    help="Names of packages to be checked. "
                    "Leave empty to find top-level packages. "
                    "Case sensitive")
parser.add_argument("--protect",
                    nargs='*',
                    help="Omit these packages when checking")
parser.add_argument("--verbose", "-v",
                    action='store_true',
                    help="Print verbose information")
args = parser.parse_args()

if args.verbose:
    print("----------")
    print("Querying pip ...")
installedPackageList = frozenset(
    pd['name']
    for pd
    in json.loads(subprocess.run(['pip', 'list', '--format', 'json'],
                                 stdout=subprocess.PIPE).stdout.decode())
)
if args.verbose:
    print("----------")
    print("Packages reported by pip:")
    for pacName in sorted(installedPackageList):
        print(pacName)

args.target = list(pacName
                   for pacName in args.target
                   if pacName in installedPackageList \
                           or print(f"{pacName} is not installed by pip"))
if len(args.target) == 0:
    exit()
if args.verbose:
    print("----------")
    print("Querying pipdeptree ...")
packageList = json.loads(subprocess.run(['pipdeptree', '--all', '--json'],
                                        stdout=subprocess.PIPE)
                         .stdout.decode())
# O(E)
depTree = dict()
for node in packageList:
    pacName = node['package']['key']
    if pacName not in installedPackageList:
        continue
    depTree[pacName] = (depTree.get(pacName, list())
                        + [d['key']
                           for d
                           in node['dependencies']
                           if d['key'] in installedPackageList])
# O(E)
affTree = dict() # reverse depTree
for pacName in depTree:
    if pacName not in installedPackageList:
        continue
    if pacName not in affTree:
        affTree[pacName] = list()
    for depName in depTree[pacName]:
        affTree[depName] = (affTree.get(depName, list()) + [pacName, ])

if args.verbose:
    print("----------")
    print("Dependency reported by pipdeptree:")
    for pacName, pacDepLst in depTree.items():
        print(pacName, pacDepLst)
    print("----------")

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
            print(f"No dependency found for {pacName}")
        else:
        # mark package as removable / maybe-removable
            removableRecord[pacName] = (True
                                        if len(affTree[pacName]) == 0
                                        else None)
    # protect pip
    if args.protect is None:
        args.protect = ["pip", ]
    else:
        args.protect.append("pip")
    for pacName in args.protect:
        if pacName not in depTree:
            print(f"{pacName} is not installed by pip. Omitted.")
        else:
            # mark package as NOT-removable
            removableRecord[pacName] = False
    targetPacList = list(removableRecord.keys())
    for pacName in targetPacList:
        updateSubDepStatus(pacName)

    if args.verbose:
        print("----------")
        print("Algo output:")
        for pacName, removableStatus in removableRecord.items():
            print(pacName, removableStatus)
        print("----------")

    removablePac = [pacName
                    for pacName in removableRecord.keys()
                    if removableRecord[pacName]]  # if is TRUE
    if len(removablePac) != 0:
        print(" ".join(sorted(removablePac)))
else:
    topLevelList = getTopLevelPac()
    if len(topLevelList) != 0:
        print(" ".join(sorted(topLevelList)))

