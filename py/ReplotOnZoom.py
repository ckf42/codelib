from matplotlib.backend_bases import MouseEvent as _pltMouseEvent
from matplotlib.pyplot import show as _pltShow
from matplotlib.pyplot import subplots as _pltSubplots
from numpy import flipud as _npFlipud

class ReplotOnZoom:
    """
    Wrapper for matplotlib.pyplot figure with replotting on zoom by mouse.
    ---
    Method:
        __init__:
            Constructor
            For more information, see help(ReplotOnZoom.__init__)
        show:
            Show the plot window and start listening to user event.
    ---
    Example:
        >>> from ReplotOnZoom import ReplotOnZoom
        >>> ReplotOnZoom((-2.0, 1.0), (-1.0, 1.0),
        ...              mandelbrot,
        ...              {'xres': 1024, 'yres': 768, 'nmax': 250},
        ...              verbose=True).show()
    """
    _xLims = None
    _yLims = None
    _calFunc = None
    _fig = None
    _ax = None
    _paraDict = {}
    _pltPara = {}
    _eps = 1e-5
    _verbose = False


    def __init__(self,
                 xLims: tuple[float, float],
                 yLims: tuple[float, float],
                 bitmapCalculateFunc: callable,
                 paraDict: dict = {},
                 pltParaDict: dict = {},
                 eps: float = 1e-5,
                 verbose: bool = False):
        """
        Constructor for ReplotOnZoom class.
        ---
        Parameters:
            xLims:
                Type: tuple[float, float]
                The range in x-coordinate
                Assumed of form (xmin, xmax)
            yLims:
                Type: tuple[float, float]
                The range in y-coordinate
                Assumed of form (ymin, ymax)
            bitmapCalculateFunc:
                Type: callable
                Must take (at least) 4 positional parameters,
                    which are exactly the values in xLims and yLims.
                Assumed to return a 2D array-like object of type that can be plotted
                    by matplotlib.pyplot.imshow, usually numpy.ndarray.
                The return value will be flipped vertically by numpy.flipud.
                Additional parameters can be specified in paraDict.
                If the first 4 parameters are not for xLims and yLims,
                    try wrapping bitmapCalculateFunc in a wrapper function.
            paraDict:
                Type: dict
                Default: empty dict
                The additional parameters to be passed to bitmapCalculateFunc.
                All parameters will be passed as keyword parameters.
                If you have other positional parameters that cannot be passed this way,
                    try wrapping bitmapCalculateFunc in a wrapper function.
            pltParaDict:
                Type: dict
                Default: empty dict
                Parameters to be passed to matplotlib.pyplot.imshow.
                All parameters will be passed as keyword parameters.
            eps:
                Type: float
                Default: 1e-5
                The numerical tolerance for setting plot limits.
            verbose:
                Type: bool
                Default: False
                Determine if verbose messages should be shown.
        """
        self._xLims = xLims
        self._yLims = yLims
        self._calFunc = bitmapCalculateFunc
        self._fig, self._ax = _pltSubplots(1, 1)
        self._paraDict = paraDict
        self._pltPara = pltParaDict
        self._eps = eps if eps > 0 else 1e-5
        self._verbose = verbose
        self._fig.canvas.mpl_connect('button_release_event', self.__onZoomCallBack)


    def __replot(self, newXLims: tuple[float, float], newYLims: tuple[float, float]):
        self._ax.imshow(_npFlipud(self._calFunc(newXLims[0], newXLims[1], newYLims[0], newYLims[1],
                                                **self._paraDict)),
                        extent=[newXLims[0], newXLims[1], newYLims[0], newYLims[1]],
                        **self._pltPara)


    def __hasMoved(self,
                   oldLimTuple: tuple[float, float],
                   newLimTuple: tuple[float, float]):
        oldLimRange = oldLimTuple[1] - oldLimTuple[0]
        newLimRange = newLimTuple[1] - newLimTuple[0]
        return any(abs(x) > self._eps * oldLimRange
                   for x in (oldLimTuple[0] - newLimTuple[0],
                             oldLimTuple[1] - newLimTuple[1],
                             newLimRange - oldLimRange))


    def __onZoomCallBack(self, event: _pltMouseEvent):
        currentXLim = self._ax.get_xlim()
        currentYLim = self._ax.get_ylim()
        if self.__hasMoved(self._xLims, currentXLim) or self.__hasMoved(self._yLims, currentYLim):
            if self._verbose:
                print("Area changed")
                print("X:", self._xLims, "->", currentXLim)
                print("Y:", self._yLims, "->", currentYLim)
                print("Replotting ...")
            self.__replot(currentXLim, currentYLim)
            if self._verbose:
                print("Replot done")
        self._xLims = currentXLim
        self._yLims = currentYLim


    def show(self):
        """
        Start the plot.
        This method will keep running until the plot window is closed.
        """
        self.__replot(self._xLims, self._yLims)
        _pltShow()

