import numpy as np
from typing import Callable

# NOTE: when plotting in plt, the y-axis begins from the top to bottom
#       an additional np.flipud may be needed
# TODO: numba compatible

def julia(c: np.cdouble,
          xmin: float = -1.5,
          xmax: float = 1.5,
          ymin: float = -1.5,
          ymax: float = 1.5,
          xres: int = 1024,
          yres: int = 1024,
          power: float = 2.0,
          nmax: int = 50):
    r = (1 + np.sqrt(1 + 4 * np.abs(c))) / 2
    xidx, yidx = np.mgrid[0 : xres, 0 : yres]
    z = np.linspace(xmin, xmax, xres)[xidx] + 1j * np.linspace(ymin, ymax, yres)[yidx]
    n = np.zeros_like(z, dtype=np.uint32)
    xidx, yidx, z = xidx.flatten(), yidx.flatten(), z.flatten()
    for iterTime in range(1, nmax + 1):
        if len(z) == 0:
            break
        np.power(z, power, out=z)
        np.add(z, c, out=z)
        msk = np.abs(z) > r
        n[xidx[msk], yidx[msk]] = iterTime
        np.logical_not(msk, out=msk)
        xidx, yidx, z = xidx[msk], yidx[msk], z[msk]
    n[n == 0] = nmax + 1
    return n.transpose()


def mandelbrot(xmin: float = -2.,
               xmax: float = 1.,
               ymin: float = -1.,
               ymax: float = 1.,
               xres: int = 1024,
               yres: int = 1024,
               nmax: int = 50):
    xidx, yidx = np.mgrid[0 : xres, 0 : yres]
    c = np.linspace(xmin, xmax, xres)[xidx] + 1j * np.linspace(ymin, ymax, yres)[yidx]
    n = np.zeros_like(c, dtype=np.uint32)
    xidx, yidx, c = xidx.flatten(), yidx.flatten(), c.flatten()
    z = np.zeros_like(c, dtype=np.cfloat)
    for iterTime in range(1, nmax + 1):
        if len(z) == 0:
            break
        np.multiply(z, z, out=z)
        np.add(z, c, out=z)
        msk = np.abs(z) > 2
        n[xidx[msk], yidx[msk]] = iterTime
        np.logical_not(msk, out=msk)
        xidx, yidx, z, c = xidx[msk], yidx[msk], z[msk], c[msk]
    n[n == 0] = nmax + 1
    return n.transpose()


# def logisBranch(rmin: float = 2.4,
                # rmax: float = 4.0,
                # rres: int = 512,
                # tres: int = 512,
                # n: int = 300):
    # # TODO: return a bitmap instead
    # r, t = np.mgrid[rmin : rmax : rres * 1j, 0 : 1 : tres * 1j]
    # for i in range(n):
        # np.multiply(t, 1 - t, out=t)
        # np.multiply(r, t, out=t)
    # for i in range(rres):
        # plt.plot(r[i], t[i], 'b,')
    # return plt.gca()

def dynamicTimeWarp(s1: np.ndarray,
                    s2: np.ndarray,
                    windowSize: int = None,
                    dist: callable = None) -> np.ndarray:  # 90-45-90 mode
    if dist is None:
        def dist(a, b):
            return (ord(a) - ord(b)) ** 2
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
    c1, c2 = (0.01 * L) ** 2, (0.03 * L) ** 2
    return (2 * mux * muy + c1) \
        / (mux ** 2 + muy ** 2 + c1) \
        * (2 * covar + c2) \
        / (sigma2x + sigma2y + c2)


def tanPlotHelper(f: callable,
                  interval: tuple = (-np.inf, np.inf),
                  nPts: int = 1000) -> tuple:
    pts = np.linspace(np.arctan(interval[0]), np.arctan(interval[1]), nPts)
    return (pts, f(np.tan(pts)))


def blockSelfSimCal(xmin: float, xmax: float, ymin: float, ymax: float,
                    xres: int, yres: int,
                    nmax: int,
                    blockSpec: tuple[tuple[tuple[Callable], Callable]]):
    res = xres * yres
    xidx, yidx = np.mgrid[0 : xres, 0 : yres]
    n = np.zeros((xres, yres), dtype=np.uint8)
    vidx = np.vstack((xidx.flatten(), yidx.flatten()))
    v = np.vstack((np.linspace(xmin, xmax, xres)[xidx].flatten(),
                   np.linspace(ymin, ymax, yres)[yidx].flatten()))
    tags = np.empty(res, dtype=np.uint8)
    for iterTime in range(1, nmax + 1):
        if len(tags) == 0:
            break
        msk = np.empty_like(tags, dtype=np.bool8)
        tags.fill(0)
        for i in range(len(blockSpec)):
            # region i + 1
            np.logical_and.reduce(tuple(f(v[0, :], v[1, :]) for f in blockSpec[i][0]),
                                  out=msk)
            tags[msk] = i + 1
        # region no
        msk = (tags == 0)
        n[vidx[0, msk], vidx[1, msk]] = iterTime
        # shift
        # TODO: better?
        for i in range(len(blockSpec)):
            msk = (tags == i + 1)
            v[:, msk] = blockSpec[i][1](v[:, msk])
        # cleanup
        np.logical_not(tags == 0, out=msk)
        vidx, v, tags = vidx[:, msk], v[:, msk], tags[msk]
    n[n == 0] = nmax + 1
    return n.transpose()


def sierpinskiTrig(xmin: float = 0.,
                   xmax: float = 1.,
                   ymin: float = 0.,
                   ymax: float = 1.,
                   xres: int = 768,
                   yres: int = 576,
                   nmax: int = 25):
    return blockSelfSimCal(xmin, xmax, ymin, ymax, xres, yres, nmax,
            (
                ((lambda x, y: y > 0,
                  lambda x, y: y < np.sqrt(3) * x,
                  lambda x, y: y < np.sqrt(3) * (1 / 2 - x)),
                 lambda v: v * 2),
                ((lambda x, y: y > 0,
                  lambda x, y: y < np.sqrt(3) * (x - 1 / 2),
                  lambda x, y: y < np.sqrt(3) * (1 - x)),
                 lambda v: v * 2 - [[1], [0]]),
                ((lambda x, y: y > np.sqrt(3) / 4,
                  lambda x, y: y < np.sqrt(3) * x,
                  lambda x, y: y < np.sqrt(3) * (1 - x)),
                 lambda v: v * 2 - [[1 / 2], [np.sqrt(3) / 2]]),
            ))


def sierpinskiCarpet(xmin: float = 0.,
                     xmax: float = 1.,
                     ymin: float = 0.,
                     ymax: float = 1.,
                     xres: int = 768,
                     yres: int = 576,
                     nmax: int = 25):
    return blockSelfSimCal(xmin, xmax, ymin, ymax, xres, yres, nmax,
            (
                ((lambda x, y: x > 0, lambda x, y: x < 1 / 3, lambda x, y: y > 0, lambda x, y: y < 1 / 3),
                 lambda v: v * 3),
                ((lambda x, y: x > 1 / 3, lambda x, y: x < 2 / 3, lambda x, y: y > 0, lambda x, y: y < 1 / 3),
                 lambda v: v * 3 - [[1], [0]]),
                ((lambda x, y: x > 2 / 3, lambda x, y: x < 1, lambda x, y: y > 0, lambda x, y: y < 1 / 3),
                 lambda v: v * 3 - [[2], [0]]),
                ((lambda x, y: x > 0, lambda x, y: x < 1 / 3, lambda x, y: y > 1 / 3, lambda x, y: y < 2 / 3),
                 lambda v: v * 3 - [[0], [1]]),
                ((lambda x, y: x > 2 / 3, lambda x, y: x < 1, lambda x, y: y > 1 / 3, lambda x, y: y < 2 / 3),
                 lambda v: v * 3 - [[2], [1]]),
                ((lambda x, y: x > 0, lambda x, y: x < 1 / 3, lambda x, y: y > 2 / 3, lambda x, y: y < 1),
                 lambda v: v * 3 - [[0], [2]]),
                ((lambda x, y: x > 1 / 3, lambda x, y: x < 2 / 3, lambda x, y: y > 2 / 3, lambda x, y: y < 1),
                 lambda v: v * 3 - [[1], [2]]),
                ((lambda x, y: x > 2 / 3, lambda x, y: x < 1, lambda x, y: y > 2 / 3, lambda x, y: y < 1),
                 lambda v: v * 3 - [[2], [2]]),
            ))

def genUnimodularMatrix(d, minV=-3, maxV=3):
    # modified from https://nathanbrixius.wordpress.com/2013/09/13/generating-random-unimodular-matrices-with-a-column-of-ones/
    import sympy as sp
    m: sp.Matrix = sp.randMatrix(d, min=minV, max=maxV)
    u: sp.Matrix = m.upper_triangular()
    l: sp.Matrix = m.lower_triangular()
    u += sp.eye(d) - sp.diag(*u.diagonal())
    l += sp.eye(d) - sp.diag(*l.diagonal())
    return l @ u

