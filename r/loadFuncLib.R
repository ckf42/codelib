# source this file to load all scripts

# get original wd
originWD = getwd()

# let user choose dir
# TODO determine location of this file automatically
codefile_dir = choose.dir(caption = "Select the dirrectory that contains this script (loadFuncLib.R)")
setwd(codefile_dir)

# safe check
if (!file.exists(file.path(codefile_dir, "loadFuncLib.R"))){
    stop(paste("loadFuncLib.R not found at selected directory", 
               "(", codefile_dir, ").", 
               "Please check if the correct one is selected. "))
}

# TODO better loading order
source("miscFuncLib.R", echo = FALSE)
source("mutualInfoLib.R", echo = FALSE)
source("charNetworkLib.R", echo = FALSE)
source("clusteringLib.R", echo = FALSE)

# reset wd after source and clean up
setwd(originWD)
rm(originWD, codefile_dir)