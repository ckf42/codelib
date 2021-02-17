# source this file to load all scripts

tempVar_loadFuncLib = list()

# get original wd
tempVar_loadFuncLib$originWD = getwd()

# let user choose dir
# TODO determine location of this file automatically
tempVar_loadFuncLib$codefile_dir = NULL
if (exists("funcLibDir")){
    tempVar_loadFuncLib$codefile_dir = dirname(get("funcLibDir"))
} else {
    tempVar_loadFuncLib$codefile_dir = choose.dir(caption = "Select the dirrectory that contains this script (loadFuncLib.R)")
}
setwd(tempVar_loadFuncLib$codefile_dir)

# safe check
if (!file.exists(file.path(tempVar_loadFuncLib$codefile_dir, "loadFuncLib.R"))){
    stop(paste("loadFuncLib.R not found at selected directory", 
               "(", tempVar_loadFuncLib$codefile_dir, ").", 
               "Please check if the correct one is selected. "))
}

# TODO better loading order. dependency? 
source("miscFuncLib.R", echo = FALSE)
source("mutualInfoLib.R", echo = FALSE)
source("charNetworkLib.R", echo = FALSE)
source("clusteringLib.R", echo = FALSE)

# reset wd after source and clean up
setwd(tempVar_loadFuncLib$originWD)
rm(tempVar_loadFuncLib)