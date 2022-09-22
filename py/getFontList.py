import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--path',
                    action='store_true',
                    help="Get the file path to the font file too")
parser.add_argument('--style',
                    action='store_true',
                    help="Get the style of the font too")
parser.add_argument('--lang',
                    type=str,
                    help="List only the font that support these languages")
styleGp = parser.add_mutually_exclusive_group()
styleGp.add_argument('--regularOnly',
                     action='store_true',
                     help="List only fonts with regular style")
styleGp.add_argument('--boldOnly',
                     action='store_true',
                     help="List only fonts with bold style")
parser.add_argument('--wholeFamilyName',
                    action='store_true',
                    help="List the whole (multipart) family name")
parser.add_argument('--sep',
                    type=str,
                    default='\t',
                    help="The seperator for display. Default to \\t")
parser.add_argument('--fcListPath',
                    type=str,
                    default='fc-list',
                    help="The path to fc-list. Default to fc-list in path")
args = parser.parse_args()

fcCmd = [ args.fcListPath ]
fcFilterStr = ':'
if args.lang is not None:
    fcFilterStr += f':familylang={args.lang}'
if args.regularOnly or args.boldOnly:
    fcFilterStr += ':style=' + ('regular' if args.regularOnly else 'bold')
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
for line in sorted(subprocess.run(fcCmd,
                                  capture_output=True,
                                  text=True,
                                  encoding='utf-8',
                                  errors='ignore').stdout.strip('"').split('""')):
    print(line.strip())

