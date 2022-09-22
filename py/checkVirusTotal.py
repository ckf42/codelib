import webbrowser
import hashlib
import argparse
import subprocess
import pathlib
from shutil import which
from personalPylib import inputPath, userConfirm

parser = argparse.ArgumentParser()
parser.add_argument('file', nargs='?', default=None, help="Path to the file", type=str)
parser.add_argument('--noextrahash', action='store_true', help="Calculate only MD5 hash for Virustotal")
parser.add_argument('--pysum',
                    action='store_true',
                    help="Force using Python hashlib module to calculate hash "
                    "instead of checking for hasher in PATH first")
args = parser.parse_args()

if args.file is None:
    fileLoc = inputPath("Please enter the path to the file:\n").strip('\'\" ')
else:
    fileLoc = args.file.strip('\'\" ')
fileLoc = pathlib.Path(fileLoc)
if not fileLoc.is_file():
    print("Requested path does not point to a file")
    exit(1)

hashNameTuple = ('md5', 'sha1', 'sha256')
if args.noextrahash:
    hashNameTuple = ('md5', )


def hasher(fname, hasherName, forceModule=False):
    if not forceModule and which(hasherName + 'sum') is not None:
        return subprocess.run([hasherName + 'sum', fname], capture_output=True).stdout.split(b' ')[0].strip(b'\\').decode()
    try:
        hasherObj = hashlib.new(hasherName)
    except ValueError:
        raise ValueError(f'Hash algorithm {hasherName} is not supported. \n'
                         'Press Enter to quit. ')
    except Exception:
        input('Unknown error occurred. \nPress Enter to quit. ')
        quit()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasherObj.update(chunk)
    return hasherObj.hexdigest()


print(f"file size (in byte): {fileLoc.stat().st_size}")

hashDict = dict()
for hName in hashNameTuple:
    hashDict[hName] = hasher(fileLoc, hName, args.pysum)
    if not args.noextrahash:
        print(f"{hName} hash is {hashDict[hName]}")

if userConfirm("Open VirusTotal in default browser? [Y/n]: ", defaultChar='y'):
    webbrowser.open_new_tab(f"https://www.virustotal.com/gui/search/{hashDict['md5']}")
if which('MpCmdRun.exe', path='C:\\Program Files\\Windows Defender') is not None \
        and userConfirm("Scan with MS Defender? [Y/n]: ", defaultChar='y'):
    subprocess.run([r'%ProgramFiles%\Windows Defender\MpCmdRun.exe',
                    '-Scan', '-ScanType', '3',
                    '-File', fileLoc.resolve()],
                   shell=True)


