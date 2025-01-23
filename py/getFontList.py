import argparse
import subprocess
from shutil import which


def getArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
            description="Simple and thin wrapper around fc-list")
    parser.add_argument(
            '--path',
            action='store_true',
            help="Get the file path to the font file too")
    parser.add_argument(
            '--style',
            action='store_true',
            help="Get the style of the font too")
    parser.add_argument(
            '--lang',
            type=str,
            help="List only the font that support these languages")
    parser.add_argument(
            '--flang',
            type=str,
            help="List only the font that support these languages family, IETF tags")
    parser.add_argument(
            '--style-filter',
            dest='filter',
            type=str,
            choices=('regular', 'bold'),
            help="List only fonts with this style")
    parser.add_argument(
            '--wholeFamilyName',
            action='store_true',
            help="List the whole (multipart) family name")
    parser.add_argument(
            '--sep',
            type=str,
            default='\t',
            help="The seperator for display. Default to \\t")
    parser.add_argument(
            '--fcListPath',
            type=str,
            default='fc-list',
            help="The path to fc-list. Default to fc-list in PATH")
    args = parser.parse_args()
    if which(args.fcListPath) is None:
        parser.error(f"{args.fcListPath} not found")
    return args

if __name__ == '__main__':
    args  = getArgs()
    fcCmd = [ args.fcListPath ]
    fcFilterStr = ':'
    if args.lang is not None:
        fcFilterStr += f':lang={args.lang}'
    if args.flang is not None:
        fcFilterStr += f':familylang={args.flang}'
    if args.filter is not None:
        fcFilterStr += ':style=' + args.filter
    fcElementList = [ 'family' ]
    fcFormatStr = '%{family}' if args.wholeFamilyName else '%{family[0]}'
    if args.path:
        fcElementList.append('file')
        fcFormatStr += args.sep + '%{file}'
    if args.style:
        fcElementList.append('style')
        fcFormatStr += args.sep + '%{style[0]}'
    fcFormatStr = '"' + fcFormatStr + r'\n"'
    fcCmd.extend([ fcFilterStr ] + fcElementList + [ '--format=' + fcFormatStr ])
    for line in sorted(subprocess.run(
            fcCmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore').stdout.strip('"').split('""')):
        print(line.strip())

