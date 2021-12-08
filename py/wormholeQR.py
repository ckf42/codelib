import argparse
import os
import qrcode
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('path',
                    type=str,
                    help="The path of the file to be sent by wormhole")
args = parser.parse_args()

os.environ["PYTHONUNBUFFERED"] = "1"
p = subprocess.Popen(
    ['python', '-m', 'wormhole', 'send', args.path],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    shell=True,
    bufsize=0)

qrCodeObj = None
while p.poll() is None:
    for line in p.stdout:
        line = line.decode()
        print(line, end='')
        if qrCodeObj is None and line.startswith('wormhole receive'):
            whCode = line.split()[2]
            qrCodeObj = qrcode.QRCode()
            qrCodeObj.add_data(
                f'wormhole:relay.magic-wormhole.io:4000?code={whCode}')
            qrCodeObj.print_ascii(invert=True)
