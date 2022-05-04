# Description

This directory contains some batch scripts.

## bookopen.bat

A simple interactive script I use to manage some books (and papers) I have on my computer. Assumes that `fzf` is installed

It requires a (local) index file for querying. This file can be built (and update) with option `/r`.

You would need to set the script configs manually and build the index first. The configs are hard-coded in the script and should be located near the beginning of the file.

To use it with a remote drive (e.g. for fetching files from remote), you would need to set up the corresponding variables first. By default, it uses `rclone` and assumes a valid `remoteIndexName`.

## runSageTeX.bat

This script is used as a part of `TeXStudio` build command to compile TeX files that uses the `sagetex` package. Assumes that `sagemath` is installed. You may need to change the `sage` path hard-coded in the script.

The corresponding build command would be something like `"path\to\runSageTeX.bat" ?am"`

## mikTexFix.bat

The MiKTeX distribution in my office computer is broken with some outdated packages cannot be updated without starting the MiKTeX console in admin mode (which requires admin privilege I do not have). Somehow I cannot install newer version of these packages in user mode with the MiKTeX console. This script tries to install those packages manually.

Running / double-clicking on this batch file should fix the issue. Haven't test on other computers though.

## pipup.bat

`pip list -o` with `fzf` to update python packages. Assumes `fzf` is installed

## condaUpdateAll.bat

Updates all conda environments

## callCondaCmd.template.bat 

Calls the given command passing all parameters.

Also checks if the given Conda Environment is activated. If not, the environment is activated before calling the command, then deactivate it after the command.

Also safe-guard deactivating the environment from `CTRL-C` aborting.

## networkDisconnectAlert.bat

Check if the network is connected and alert if not

## updateSageTex.bat

Copy `sagetex.sty` to texmf tree. Similar to `runSageTex.bat` but is used for updatting/resetting `sagetex`

