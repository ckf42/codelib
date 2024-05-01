# README

Here are some cpp code that are too small to be in their own repo.

Most are built on a Windows 10 machine with gcc on a [MSYS2](https://www.msys2.org/) environment. To build them you would need to install the corresponding toolchains. Have not checked on other OSes.

## clock

A digital 7-segment 24-hour clock that syncs with system time. That's all.

By default, the makefile builds a small executable (~500KB) that can probably run as a standalone. Have not checked yet.

Built with [FLTK](https://www.fltk.org/) 1.3.9, so install [it](https://packages.msys2.org/base/mingw-w64-fltk) first before building.

## cfrs

Another (horrible) implementation of [CFRS](https://github.com/susam/cfrs).

Usage: `cfrs $CODE`

Built with [FLTK](https://www.fltk.org/) 1.3.9

## minesweeper

Another crappy half-baked minesweeper clone. Modelled after XP minesweeper.

Note that at the moment,
* Looks horrible
* No record saving
* No config saving, so no resuming previous board config
* No Mark (`?`), no color toggling, no sound
* No Help menu
* Icons are Unicode emoji
* Opening a large blank space lags a little

Built with [FLTK](https://www.fltk.org/) 1.3.9

