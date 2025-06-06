# Description

Some python scripts.

Most scripts accept commandline arguments. For the details on these arguments, consult the `--help` argument

## alarm.py

Commandline tool for a simple countdown alarm clock. Uses `winsound` and so is Windows only

## ansiescape.py

A simple library for some helper functions that give ANSI escape sequences, mostly so that I do not need to keep looking back at references.

## bblToBib.py

Transform the `bbl` file (usually generated by `biblatex`) or a `tex` file that use such file into a `bib` file that can be used for e.g. `bibtex`

## cfr

(Horrible) implementation of [`CFR[]`](https://github.com/susam/cfr) displayed with [`pygame`](https://www.pygame.org/).

Assumed `pygame` is installed.

## checkFileIntegrity.py

Compute some hashes, check file signature, and verify gpg. Optionally search the MD5 hash on VirusTotal, and scan with Windows Defender

## decodeClipboardQRCode.py

Scan image in clipboard and decode the QR code within, if any. Requires `opencv-python`, `pillow`, and `numpy`

## decodeMorseInWav.py

Decode the Morse code in a `wav` file and translate it to text. Still has some issues handling spacing swings

Requires `numpy`, `scipy`, and uses `MorseCodeDict.py`

## djvu2rga

A direct python port of [the djvu adapter](https://github.com/phiresky/ripgrep-all/discussions/166#discussioncomment-6435402) for [ripgrep-all](https://github.com/phiresky/ripgrep-all). Does not do any check on file type, permission, etc.

Assumes `djvused` from [DjVuLibre](https://djvu.sourceforge.net/) (or other conforming tool) exists in the PATH. Probably can go with [python-djvulibre](https://pypi.org/project/python-djvulibre/) binding to make it standalone, but have not figured out how to build it on a Windows machine.

Written as a package so you can install it with pipx. Should also work without installing if you make rga call python directly, but I am not bothered enough to check.

## expandMdMathMacro.py

Read a `Markdown` file that uses math macros (stored as `json` format) and transform to plain math `KaTeX` math commands. Also allow transforming math commands with image links, or transform the file into a `HTML` file that can be rendered with `MathML` or GitHub-previewable `IPython` notebook.

Requires `pandoc` in path for file format transforming.

## extractBib.py

Extract entries in a `bib` file that are cited in the given `TeX` file and put them to `stdout` or put them in a separate file.

Requires `bibtexparser~=1.0`

## extractUMM.py

Extract commands from my `usefulmathmacro` macros that are used in a given `TeX` file and output them to `stdout` or embed the commands back in the file.

## fetchDocMetadata.py

Fetch the metadata of a document identifier and display its metadata in `stdout`. Cut-down version of the same functionality in `shdl`. Useful for debugging `shdl`

Currently only support `doi`, `arxiv`, and `jstor`.

## getExchangeRate.py

Get the exchange rate from one currency to another. Does not guarantee data accuracy.

Available backends are 
* [European Central Bank](https://sdw-wsrest.ecb.europa.eu/help/)
* [currency-api](https://github.com/fawazahmed0/currency-api)
* [Exchange Rate API](https://www.exchangerate-api.com)

## getFontList.py

A simple script wrapping around `fc-list`

## getLinksInHTML.py

Parse the given page and extract all links. Useful for discovering links in CTF.

## hxscript.py

Some simple python script I have written for practising CTF.

## MorseCodeDict.py

Not a cli utility but a simple module that contains dict on converting simple Morse code and some helper functions

## musicKeyboard.py

A mini project I did. Use your keyboard to play some musics. Dropped because of NKRO.

Uses code from `personalPylib_audio.py`. 

## personalPylib_np.py

Same as `personalPylib.py` but relies on `numpy`

## paperNameNormalizer.py

Same as `fetchDocMetadata.py` but for getting the `autoname`. Also for debugging `shdl`

## personalPylib_audio.py

A simple python I use to generate some sounds. Uses `numpy`

## personalPylib.py

Some python scripts I have written. May be used in other scripts.

## previewLatex.py

A function that renders `SageMath` expression (that can be `latex()`ed) into image and display it in the terminal ~~in [iTerm2 image sequence](https://iterm2.com/documentation-images.html)~~

~~Requires the [`imgcat` package](https://pypi.org/project/imgcat/).~~
Now also uses [wezterm `imgcat`](https://wezfurlong.org/wezterm/cli/imgcat.html) to show image.

The template latex content is edited from TeXStudio preview latex file. Compiling requires `amsmath`, `amssymb`, `amsfonts`, `preview`, `varwidth` packages

~~Should work on all terminal emulators that support the iTerm2 image protocol, but currently on Windows only work with the default `mintty` terminal. Not sure why~~

**NOTE** target Python version 3.7.10 (with SageMath 9.3).

## previewLatex_sp.py

Same as `previewLatex.py` but
* uses [wezterm `imgcat`](https://wezfurlong.org/wezterm/cli/imgcat.html) to show image instead of `imgcat` package
* uses `sympy.latex` to `latex()` expression and does not assume to be in a `SageMath` environment

If `sympy` is installed and `wezterm` is used, you may put this in ipython `startup` directory in the profile.

## previewInTerm.py

Similar to `previewLatex.py` but takes a `SageMath` `Graphics` object and show the image in wezterm.

## pipRemovable.py

A python script to check the dependencies of packages. Depends on `pip` and `pipdeptree >= 0.5.0` (ironically). 

**WARNING** the functionality depends on `pipdeptree`. If `pipdeptree` does not detect dependencies correctly (e.g. as optional), this script also gives incorrect answers. Check the dependencies yourself before actually uninstalling packages.

## ReplotOnZoom.py

A simple class that replots the bitmap on zooming and panning

## wormholeQR.py

Read the `wormhole send` code and generate a QR code that can be read by `wormhole-william`. Use for transferring files from computer to cellphone with `wormhole(-william)`

