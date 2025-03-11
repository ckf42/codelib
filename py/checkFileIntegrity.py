import argparse
import hashlib
import pathlib
import typing as tp
from shutil import which
from subprocess import PIPE, run
from urllib.parse import urlparse
from webbrowser import open_new_tab

import requests as rq

from personalPylib import userConfirm

defaultHashNames: tuple[str, ...] = ('md5', 'sha1', 'sha256')
hashAlwaysCompute: frozenset[str] = frozenset(('md5',))


def isURL(s: str) -> bool:
    return all(tuple((r.scheme, r.netloc, r.path) for r in (urlparse(s),))[0])


@tp.overload
def getLinkContent(
    hashLink: str,
    asHashDigest: tp.Literal[True]) -> tuple[str | None, str]: ...


@tp.overload
def getLinkContent(
    hashLink: str,
    asHashDigest: tp.Literal[False]) -> tuple[bytes | None, str]: ...


def getHash(hashInput: str, parser: argparse.ArgumentParser, hName: str):
    sigContent: str | None = None
    try:
        # is digest
        int(hashInput, base=16)
        sigContent = hashInput.lower()
    except ValueError:
        sigContent, report = getLinkContent(
            hashInput.strip(' \'\"'),
            asHashDigest=True)
        if report == 'failed':
            parser.error(f"Failed to get content for {hName}")
        if report == 'file':
            print(f"Input for {hName} looks like a file path")
        elif report == 'url':
            print(f"Input for {hName} looks like a URL")
        print("Fetched content:")
        print(sigContent)
        print()
        return sigContent


def getLinkContent(
        hashLink: str,
        asHashDigest: bool = True) -> tuple[str | bytes | None, str]:
    # returns (sigContent, report)
    sigContent: str | bytes | None = None
    report: str = 'failed'
    if isURL(hashLink):
        report = 'url'
        sigContent = rq.get(hashLink, allow_redirects=True).content
        if asHashDigest:
            assert isinstance(sigContent, bytes)
            sigContent = sigContent.decode('utf-8')
    elif (p := pathlib.Path(hashLink).expanduser().resolve()).is_file():
        report = 'file'
        # is file
        if asHashDigest:
            with p.open('rt') as f:
                sigContent = f.read()
    return (sigContent, report)


def getArgs() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="This is a combination of gpgVerify.py and checkVirusTotal.py")
    parser.add_argument(
        'file',
        help="Path to the file",
        type=str)
    parser.add_argument(
        '--sys_enc',
        dest='sysenc',
        type=str,
        default='cp950',
        help="The encoding used to communicate with shell "
        "(to invoke hashsum executable and gpg)")
    hashOptionGp = parser.add_argument_group(
        "Hash Options",
        "Except MD5, only hashes specified are computed. "
        "MD5 is always computed.")
    hashOptionGp.add_argument(
        '--pysum',
        action='store_true',
        help="Only use Python hashlib module to calculate hash. "
        "If not specified, will use hasher executable whenever it exists in path "
        "and use hashlib only as fallback")
    for hName in defaultHashNames:
        hashOptionGp.add_argument(
            f'--{hName}',
            type=str,
            help=f"The {hName} hash (in hexadecimal), "
            "the file path to digest file, or a URL to it")
    hashOptionGp.add_argument(
            '--althash',
            type=str,
            help="Use other hash algorithm. Will always use Python hashlib. "
            "Format: {hashName}:{hash/path/URL}")
    gpgOptionGp = parser.add_argument_group("GPG Options")
    gpgOptionGp.add_argument(
        '--sig',
        type=str,
        help="The GPG signature file, or a URL to it")
    gpgOptionGp.add_argument(
        '--gpgpath',
        type=str,
        default='gpg',
        help="The path to gpg executable. Defaults to the first one in PATH")
    scanOptionGp = parser.add_argument_group("Windows Defender Options")
    scanOptionGp.add_argument(
        '--scan',
        action=argparse.BooleanOptionalAction,
        help="Determine if WinDefender scan should be done automatically. "
        "If not provided, will ask before scanning")
    args: argparse.Namespace = parser.parse_args()
    # args verification
    filePath: pathlib.Path = pathlib.Path(args.file.strip(' \'\"'))
    if not filePath.is_file():
        parser.error("Requested path does not point to a file")
    args.file = filePath
    args._hashInShell = dict()
    for hName in defaultHashNames:
        if getattr(args, hName) is not None or hName in hashAlwaysCompute:
            isHashUtilFound: bool = False
            if not args.pysum and which(hName + 'sum') is not None:
                isHashUtilFound = True
                args._hashInShell[hName] = True
            if not isHashUtilFound and hName not in hashlib.algorithms_available:
                parser.error(
                    f"Requested hash {hName} is not available in hashlib")
            else:
                args._hashInShell[hName] = False
        # get digest content
        if (hashUserInput := getattr(args, hName)) is not None:
            setattr(args, hName, getHash(hashUserInput.strip(), parser, hName))
    if args.althash is not None:
        args.althashName, altHashUserInput = args.althash.split(':', maxsplit=1)
        args.althashName = args.althashName.strip()
        if args.althashName in defaultHashNames:
            parser.error(f"Specify {args.althashName} hash with --{args.althashName}")
        if args.althashName not in hashlib.algorithms_available:
            parser.error(
                    f"Requested hash {args.althashName} is not available in hashlib")
        args._hashInShell[args.althashName] = False
        args.althashVal = getHash(altHashUserInput, parser, args.althashName)
    if args.sig is not None:
        if which(args.gpgpath) is None:
            parser.error("gpg not found in PATH")
        gpgLink: str = args.sig.strip().strip(' \'\"')
        gpgContent: bytes | None
        gpgContent, report = getLinkContent(gpgLink, asHashDigest=False)
        if report == 'failed':
            parser.error("Failed to get content for GPG")
        if report == 'file':
            print("Input for GPG looks like a file path")
            args._sigIsFile = True
            args.sig = pathlib.Path(gpgLink)
        elif report == 'url':
            print("Input for GPG looks like a URL")
            print("Fetched content:")
            print(gpgContent)
            print()
            args._sigIsFile = False
            args.sig = gpgContent
    return args


def displayFileSig(fileLoc: pathlib.Path, enc: str) -> None:
    print(f"file size (in byte): {fileLoc.stat().st_size:,}")
    fileSigStatus: str = run(
        ['powershell', '-Command',
         '(', 'Get-AuthenticodeSignature',
         '-FilePath', f'"{str(fileLoc.resolve())}"', ').Status'],
        stdout=PIPE,
        shell=True,
        text=True).stdout.strip()
    print("File signature status:", fileSigStatus)
    if fileSigStatus != 'NotSigned':
        print("Signature info:")
        print(run(
            ['powershell', '-Command', '(',
             'Get-AuthenticodeSignature',
             '-FilePath', f'"{str(fileLoc.resolve())}"', ').SignerCertificate',
             '|', 'Format-List'],
            stdout=PIPE,
            text=True,
            shell=True,
            encoding=enc).stdout.strip())


def hasher(
        fname: pathlib.Path,
        hasherName: str,
        forceModule: bool) -> str:
    if not forceModule:
        return run(
            (hasherName + 'sum', fname),
            capture_output=True).stdout.split(b' ')[0].strip(b'\\').decode()
    hasherObj = hashlib.new(hasherName)
    with fname.open('rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasherObj.update(chunk)
    return hasherObj.hexdigest().lower()


def getHashRes(
        fileLoc: pathlib.Path,
        hashesToCompute: list[str],
        hashInShellDict: dict[str, bool]) -> dict[str, str]:
    return {hName: hasher(fileLoc, hName, hashInShellDict[hName])
            for hName in hashesToCompute}


def checkHashMatch(computedDigest: str, providedDigest: str) -> bool:
    hasMatch: bool = False
    for line in providedDigest.splitlines():
        if line.strip().lower().startswith(computedDigest):
            print(f"\tMatching line:\n\t{line}")
            hasMatch = True
            break
    return hasMatch


def verifyGpgSig(
        fileLoc: pathlib.Path,
        sig: pathlib.Path | bytes,
        sigIsFile: bool,
        gpgExe: str,
        enc: str) -> None:
    commandInput: bytes | None = None
    verifyCommand = f'{gpgExe} --verify '
    if sigIsFile:
        assert isinstance(sig, pathlib.Path)
        verifyCommand += f'"{str(sig.resolve())}"'
    else:
        assert isinstance(sig, bytes)
        commandInput = sig
        verifyCommand += '-'
    verifyCommand += f' "{fileLoc.resolve()}"'
    p = run(verifyCommand,
            stdout=PIPE, stderr=PIPE,
            input=commandInput,
            encoding=enc if commandInput is None else None)
    _, serrData = p.stdout, p.stderr
    publicKeyID: list[str] = []
    lastKey: str | None = None
    for line in (serrData.decode(enc) if isinstance(serrData, bytes) else serrData).splitlines():
        print(line)
        if 'using ' in line[4:].strip(' '):
            lastKey = line.split('key ')[1]
            print(f"using key {lastKey}")
        if 'No public key' in line:
            assert lastKey is not None
            print(f"Key {lastKey} missing")
            publicKeyID.append(lastKey)
            lastKey = None
    returnCode = p.returncode
    print(f"returncode: {returnCode}")
    # check if success
    if returnCode in (0, 1):
        print(("OK", "Bad sig")[returnCode])
        return
    elif len(publicKeyID) == 0:
        print("Unknown error occurred")
        return
    # key missing
    # getting keys
    print(f"Key missing, getting key {' '.join(publicKeyID)}")
    p = run(
        f"{gpgExe} --receive-keys {' '.join(publicKeyID)}",
        stdout=PIPE, stderr=PIPE, encoding=enc)
    _, serrData = p.stdout, p.stderr
    if 'failed' in serrData:
        print("Error occurred. Please try again later. ")
        return
    print("Key received")
    # second pass
    print("Re-running verification")
    returnCode = run(
        verifyCommand,
        input=commandInput,
        encoding=enc if commandInput is not None else None).returncode
    if returnCode in (0, 1):
        print(("OK", "Bad sig")[returnCode])
    else:
        print("Unknown error. Please check signature manually")


def main() -> None:
    args: argparse.Namespace = getArgs()
    displayFileSig(args.file, args.sysenc)
    if args.sig is not None:
        verifyGpgSig(args.file, args.sig, args._sigIsFile,
                     args.gpgpath, args.sysenc)
    hashesToCompute: list[str] = [
        hName
        for hName in defaultHashNames
        if getattr(args, hName) is not None or hName in hashAlwaysCompute
    ]
    providedHashes: dict[str, str] = {
        hName: h
        for hName in defaultHashNames
        if (h := getattr(args, hName)) is not None
    }
    if args.althash is not None:
        hashesToCompute.append(args.althashName)
        providedHashes[args.althashName] = args.althashVal
    hashDict: dict[str, str] = getHashRes(
        args.file,
        hashesToCompute,
        args._hashInShell)
    for hName in hashesToCompute:
        hDigest = hashDict[hName]
        print(f"{hName} hash: {hDigest}")
        providedHash: str | None = providedHashes.get(hName, None)
        # providedHash is None if hName is in hashAlwaysCompute
        if providedHash is not None and not checkHashMatch(hDigest, providedHash):
            print(f"*** {hName} hash ({hDigest}) does not match "
                  "with the specified digest ***")
    if 'md5' in hashAlwaysCompute \
            and userConfirm(
                "Open VirusTotal in default browser? [Y/n]: ",
                defaultChar='y'):
        open_new_tab(
            f"https://www.virustotal.com/gui/search/{hashDict['md5']}")
    if which('MpCmdRun.exe', path='C:/Program Files/Windows Defender') is not None \
            and (userConfirm("Scan with MS Defender? [Y/n]: ", defaultChar='y')
                 if args.scan is None
                 else args.scan):
        run([r'%ProgramFiles%\Windows Defender\MpCmdRun.exe',
             '-Scan', '-ScanType', '3',
             '-File', args.file.resolve()],
            shell=True)


if __name__ == '__main__':
    main()
