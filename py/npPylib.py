if __name__ == '__main__':
    exit()

import numpy as np


def dynamicTimeWarp(s1: np.ndarray, s2: np.ndarray,
                    windowSize: int = None,
                    dist: callable = None) -> np.ndarray:  # 90-45-90 mode
    if dist is None:
        def dist(a, b):
            return (ord(a) - ord(b))**2
    if windowSize is None:
        windowSize = np.inf
    n, m = len(s1), len(s2)
    # reach [i-windowSize, i+windowSize]
    windowSize = max(windowSize, abs(n - m))
    arr = np.full((n, m), np.inf)
    arr[0, 0] = dist(s1[0], s2[0])
    for i in range(1, min(n, windowSize + 1)):
        arr[i, 0] = dist(s1[i], s2[0]) + arr[i - 1, 0]
    for j in range(1, min(m, windowSize + 1)):
        arr[0, j] = dist(s1[0], s2[j]) + arr[0, j - 1]
    for i in range(1, n):
        for j in range(max(0, i - windowSize), min(m, i + windowSize + 1)):
            arr[i, j] = dist(s1[i], s2[j]) + min(arr[i - 1, j],
                                                 arr[i - 1, j - 1],
                                                 arr[i, j - 1])
    return arr


def ssim(arr1: np.ndarray, arr2: np.ndarray,
         channelLast: bool = True, bitPerPixel: int = 8) -> float:
    if arr1.shape != arr2.shape:
        return 0
    if len(arr1.shape) == 3:
        ssimOnChannel = [0]
        if channelLast:
            ssimOnChannel = [ssim(arr1[..., i], arr2[..., i])
                             for i in range(arr1.shape[-1])]
        else:
            ssimOnChannel = [ssim(arr1[i, ...], arr2[i, ...])
                             for i in range(arr1.shape[0])]
        return np.mean(ssimOnChannel)
    mux, sigma2x = np.mean(arr1), np.var(arr1)
    muy, sigma2y = np.mean(arr2), np.var(arr2)
    covar = np.mean((arr1 - mux) * (arr2 - muy))
    L = 2**bitPerPixel - 1
    c1, c2 = (0.01 * L)**2, (0.03 * L)**2
    return (2 * mux * muy + c1) \
        / (mux**2 + muy**2 + c1) \
        * (2 * covar + c2) \
        / (sigma2x + sigma2y + c2)


def tanPlotHelper(f: callable,
                  interval: tuple = (-np.inf, np.inf),
                  nPts: int = 1000) -> tuple:
    pts = np.linspace(np.arctan(interval[0]), np.arctan(interval[1]), nPts)
    return (pts, f(np.tan(pts)))
