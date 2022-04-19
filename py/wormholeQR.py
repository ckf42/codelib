import argparse
import os
import qrcode
import subprocess
import locale

parser = argparse.ArgumentParser()
parser.add_argument('path',
                    type=str,
                    help="The path of file be sent by wormhole")
parser.add_argument('--astext',
                    action='store_true',
                    help="Send text by wormhole. "
                    "If specified, path will be treated as plain text")
parser.add_argument('--wormhole',
                    type=str,
                    help="Path to wormhole",
                    default='wormhole')
args = parser.parse_args()

os.environ["PYTHONUNBUFFERED"] = "1"
p = subprocess.Popen(
    [
        args.wormhole,
        'send',
        f'--text={args.path}' if args.astext else args.path,
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    shell=True,
    bufsize=0
)

qrCodeObj = None
while p.poll() is None:
    for line in p.stdout:
        line = line.decode(locale.getpreferredencoding())
        print(line, end='')
        if qrCodeObj is None and line.startswith('wormhole receive'):
            whCode = line.split()[2]
            qrCodeObj = qrcode.QRCode()
            qrCodeObj.add_data(
                f'wormhole:relay.magic-wormhole.io:4000?code={whCode}')
            qrCodeObj.print_ascii(invert=True)
