from PIL import ImageGrab
from cv2 import QRCodeDetector
from numpy import asarray

print("Reading clipboard image")
im = ImageGrab.grabclipboard()
if im is None:
    print("Clipboard has no image")
else:
    print("Initiating detector")
    d = QRCodeDetector()
    print("Decoding image")
    data, va, bq = d.detectAndDecode(asarray(im))
    if va is not None:
        print("QRCode data:")
        print(data)
    else:
        print("No QRCode detected")

