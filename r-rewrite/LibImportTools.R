# this lib provides somes functions on managing the codelib libraries
# please go to the definitions for more detail
#
# several hidden variables (name starting with a dot) are also defined here

# global var to be written by lib scripts, used to resolve dependency
.LibImportTools.Global.Dependency = NULL

# global var, list what lib are imported
.LibImportTools.Global.ImportedLibs = get0(".LibImportTools.Global.ImportedLibs")

# const var recording what lib can be imported
.LibImportTools.Const.KnownLibs = c(
    "Graph.Clustering",
    "Graph",
    "InfoTheory",
    # "LibImportTools", # not include itself
    "MiscUtility"
)

# directory of this file
# TODO need a better way of finding where this file is
.LibImportTools.Const.LibDir = getwd()

#' @description internal routine used to import a library file
#'
#' @param lib.name char. name of the library file, without extension
#'
#' @param verbose.print.func function. the function used to print verbose message
#'                           default: an empty function
#'
#' @return no return
#'
.LibImportTools.importLibFile = function(lib.name, verbose.print.func = function(x) NULL){
    targetFilePath = file.path(.LibImportTools.Const.LibDir,
                               paste0(lib.name, '.R'))
    verbose.print.func(paste("sourcing file", targetFilePath))
    source(targetFilePath, echo = FALSE, local = FALSE)
}


#'
#' @description import requested libraries
#'
#' @param requested.lib char vector. the names of the libraries to be imported
#'                      currently known libraries (ref to .LibImportTools.Const.KnownLibs):
#'                          "Graph.Clustering", "Graph", "InfoTheory", "MiscUtility"
#'                      default: all libraries known
#'
#' @param with.force.reimport boolean.
#'                            determine if libraries should be reimported on request
#'                            default: FALSE
#'
#' @param with.no.dependency boolean.
#'                           determine if import only the requested libraries and not their dependencies
#'                           default: FALSE
#'
#' @param with.legacy.names boolean. determine if legacy alias should be added
#'                          only use for compatibility
#'                          default: FALSE
#'
#' @param with.verbose boolean. determine if verbose information should be printed
#'                     default: FALSE
#'
#' @return nothing (an invisible NULL)
#'
LibImportTools.import = function(requested.lib = c(
                                     "Graph.Clustering",
                                     "Graph",
                                     "InfoTheory",
                                     "LegacyInterface",
                                     "MiscUtility"
                                 ),
                                 with.force.reimport = FALSE,
                                 with.no.dependency = FALSE,
                                 with.legacy.names = FALSE,
                                 with.verbose = FALSE) {
    verbosePrint = function(x) NULL
    if (with.verbose) {
        verbosePrint = print
    }
    requested.lib = Filter(
        function(x) x %in% .LibImportTools.Const.KnownLibs,
        requested.lib
    )
    if (!with.force.reimport) {
        requested.lib = Filter(
            function(x) !(x %in% .LibImportTools.Global.ImportedLibs),
            requested.lib
        )
    }
    if (length(requested.lib) == 0) {
        verbosePrint("No library needs to be imported")
        return(invisible(NULL))
    }
    .LibImportTools.Global.Dependency <<- NULL
    currentImported = NULL
    for (libName in requested.lib) {
        verbosePrint(paste("Importing", libName))
        # targetLibFilePath = paste0(libName, '.R')
        # verbosePrint(paste("openning file", targetLibFilePath))
        # source(targetLibFilePath, echo = FALSE, local = FALSE)
        .LibImportTools.importLibFile(libName, verbosePrint)
        currentImported = append(currentImported, libName)
    }
    .LibImportTools.Global.Dependency <<- Filter(
        function(x) !(x %in% requested.lib),
        unique(.LibImportTools.Global.Dependency)
    )
    needToImport = Filter(
        function(x) !(x %in% .LibImportTools.Global.ImportedLibs),
        .LibImportTools.Global.Dependency
    )
    verbosePrint(paste(length(needToImport), "dependencies"))
    if (!with.no.dependency && length(needToImport) != 0) {
        verbosePrint("Importing dependencies")
        for (libName in needToImport) {
            verbosePrint(paste("Importing", libName))
            # source(paste0(libName, '.R'), echo = FALSE, local = FALSE)
            .LibImportTools.importLibFile(libName, verbosePrint)
            currentImported = append(currentImported, libName)
        }
    }
    if (with.legacy.names){
        verbosePrint("Adding legacy names")
        # source("LibImportTools.LegacyInterface.R", echo = FALSE, local = FALSE)
        .LibImportTools.importLibFile("LibImportTools.LegacyInterface", verbosePrint)
    }
    verbosePrint(paste(length(currentImported), "libraries imported"))
    .LibImportTools.Global.ImportedLibs <<- unique(append(.LibImportTools.Global.ImportedLibs,
                                                          currentImported))
    return(invisible(NULL))
}

# alias
codelibImport = LibImportTools.import

#'
#' @description get what lib are imported
#'
#' @return (a copy of) the char vector which records all imported libraries
#'
#' @note (read-only) wrapper for hidden var .LibImportTools.Global.ImportedLibs
#'
LibImportTools.getImportedLib = function(){
    return(.LibImportTools.Global.ImportedLibs)
}

#'
#' @description get what lib can be imported
#'
#' @return (a copy of) the char vector which records all known libraries
#'
#' @note (read-only) wrapper for hidden var .LibImportTools.Const.KnownLibs
#'
LibImportTools.getKnownLib = function(){
    return(.LibImportTools.Const.KnownLibs)
}

# auto import when sourcing
# a bit hacky
if (exists(".LibImportTools.SourceArgs")) {
    do.call(LibImportTools.import, get(".LibImportTools.SourceArgs"))
}
