# source this file to load all scripts
# this script reads the following variables:
#
#         loadFuncLibPath: string. the path to this script.
#                          if not exist, will ask to choose the parent directory
#
#         selectedLibs: vector of strings. the names of the lib to be loaded
#                       the names should be one (or more) of: "misc", "mutualInfo", "charNet", "cluster", "DMP", "info"
#                       if not exist or is NA, default to c("misc", "mutualInfo", "charNet", "cluster", "info")
#
# this script writes the following variables (besides the ones in the loaded libraries):
#
#         loadedFuncLibNames: vector of strings. The name of lib filenames loaded
#                             may be used to avoid re-loading
#                             after executing this script, this variable will be created
#                             (may be NULL)
#
tempVar_loadFuncLib = list()

# get original wd
tempVar_loadFuncLib$originWD = getwd()

# let user choose dir
# TODO determine location of this file automatically
tempVar_loadFuncLib$codefile_dir = NULL
if (exists("loadFuncLibPath")) {
    tempVar_loadFuncLib$codefile_dir = dirname(get("loadFuncLibPath"))
} else {
    if (!is.null(sys.frames())) {
        tempVar_loadFuncLib$codefile_dir = dirname(sys.frame(1)$ofile)
    } else {
        tempVar_loadFuncLib$codefile_dir = choose.dir(caption = "Select the dirrectory that contains this script (loadFuncLib.R)")
    }
}
setwd(tempVar_loadFuncLib$codefile_dir)

# safe check
if (!file.exists(file.path(tempVar_loadFuncLib$codefile_dir, "loadFuncLib.R"))) {
    stop(
        paste(
            "loadFuncLib.R not found at selected directory",
            "(",
            tempVar_loadFuncLib$codefile_dir,
            ").",
            "Please check if the correct one is selected. "
        )
    )
}

tempVar_loadFuncLib$definedLibName = c(
    misc = "miscFuncLib.R",
    info = "infoTheoryLib.R",
    mutualInfo = "mutualInfoLib.R",
    charNet = "charNetworkLib.R",
    cluster = "clusteringLib.R",
    DMP = "DMPLib.R"
)

if (!exists("loadedFuncLibNames")){
    loadedFuncLibNames = NULL
}
tempVar_loadFuncLib$libsToLoad = tempVar_loadFuncLib$definedLibName[names(tempVar_loadFuncLib$definedLibName) != "DMP"]
if (exists('selectedLibs') && !is.na(get('selectedLibs'))) {
    tempVar_loadFuncLib$libsToLoad = na.exclude(tempVar_loadFuncLib$definedLibName[unique(selectedLibs)])
}

# TODO better loading order. dependency?
for (tempVar_loadFuncLib_LibName in tempVar_loadFuncLib$libsToLoad) {
    if (tempVar_loadFuncLib_LibName %in% loadedFuncLibNames){
        print(paste(tempVar_loadFuncLib_LibName, "already loaded"))
        next()
    }
    print(paste("loading", tempVar_loadFuncLib_LibName))
    source(tempVar_loadFuncLib_LibName, echo = FALSE)
    loadedFuncLibNames = c(loadedFuncLibNames, tempVar_loadFuncLib_LibName)
}

# reset wd after source and clean up
setwd(tempVar_loadFuncLib$originWD)
rm(tempVar_loadFuncLib, tempVar_loadFuncLib_LibName)
