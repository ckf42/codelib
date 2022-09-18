from PIL import ImageGrab
from cv2 import QRCodeDetector, threshold, THRESH_OTSU
from numpy import asarray

print("Reading clipboard image")
im = ImageGrab.grabclipboard()
if im is None:
    print("Clipboard has no image")
else:
    print("Preprocessing image")
    im = threshold(asarray(im.convert('L')), 0, 255, THRESH_OTSU)[1]
    print("Initiating detector")
    d = QRCodeDetector()
    print("Decoding image")
    data, qrPt, rectedQr = d.detectAndDecode(im)
    if qrPt is not None:
        if len(data) == 0:
            print("The QRCode has empty data")
        else:
            print(f"QRCode data (len {len(data)}):")
            print(data)
    else:
        print("No QRCode detected")

