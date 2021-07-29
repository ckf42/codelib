# this lib provides somes functions on managing the codelib libraries
# please go to the definitions for more detail
#
# several hidden variables (name starting with a dot) are also defined here

# global var for cross-file configurations reading
.LibImportTools.Global.Config = get0(
    ".LibImportTools.Global.Config",
    ifnotfound = list(
        "auto.import.dependent.func" = FALSE
    )
)

# global var to be written by lib scripts, used to resolve dependency
.LibImportTools.Global.Dependency = NULL

# global var, list what lib are imported. named vector with name being the lib name, val being mtime in POSIXct
.LibImportTools.Global.ImportedLibs = get0(".LibImportTools.Global.ImportedLibs")

# const var recording what lib can be imported
.LibImportTools.Const.KnownLibs = c(
    "Graph.Clustering",
    "Graph",
    "InfoTheory",
    "MiscUtility"
)

# directory of this file
# TODO need a better way of finding where this file is
.LibImportTools.Const.LibDir = getwd()

#'
#' @description get what lib are imported
#'
#' @return (a copy of) the char vector which records all imported libraries
#'
#' @note (read-only) wrapper for hidden var .LibImportTools.Global.ImportedLibs
#'
LibImportTools.getImportedLib = function() {
    return(names(.LibImportTools.Global.ImportedLibs))
}

#'
#' @description get what lib can be imported
#'
#' @return (a copy of) the char vector which records all known libraries
#'
#' @note (read-only) wrapper for hidden var .LibImportTools.Const.KnownLibs
#'
LibImportTools.getKnownLib = function() {
    return(.LibImportTools.Const.KnownLibs)
}

#'
#' @description internal routine used to get the location of a lib file by name
#'
#' @param lib.name char. name of the library file, without extension
#'
#' @return char. the path of the file (in lib dir). if such file does not exist, return NA
#'
#' @note wrapper for file.path
#'
.LibImportTools.getLibFileLoc = function(lib.name) {
    returnPath = file.path(.LibImportTools.Const.LibDir, paste0(lib.name, '.R'))
    if (file.exists(returnPath)) {
        return(returnPath)
    } else {
        return(NA)
    }
}

#' @description internal routine used to import a library file
#'
#' @param lib.name char. name of the library file, without extension
#'
#' @param verbose.print.func function. the function used to print verbose message
#'                           default: an empty function
#'
#' @return no return
#'
.LibImportTools.importLibFile = function(lib.name, verbose.print.func = function(...) NULL) {
    targetFilePath = .LibImportTools.getLibFileLoc(lib.name)
    verbose.print.func("sourcing file", targetFilePath)
    source(targetFilePath, echo = FALSE, local = FALSE)
}

#'
#' @description import requested libraries
#'
#' @param requested.lib char vector, or a char literal "All". the names of the libraries to be imported
#'                      case sensitive
#'                      if is "All", will import all libraries
#'                      currently known libraries:
#'                          "Graph.Clustering", "Graph", "InfoTheory", "MiscUtility"
#'                      call LibImportTools.getKnownLib to get names of all known libraries
#'                      default: all libraries known (same as "All")
#'
#' @param with.force.reimport boolean.
#'                            determine if imported libraries should be reimported on request
#'                            default: FALSE
#'
#' @param with.mtime.check boolean.
#'                         when with.force.reimport == TRUE,
#'                             reimport only updated files by checking the file modification time
#'                             unlike with.force.reimport, also check on dependencies
#'                         ignored if with.force.reimport == FALSE
#'                         default: TRUE
#'
#' @param with.no.dependency boolean.
#'                           determine if import only the requested libraries and not their dependencies
#'                           default: FALSE
#'
#' @param with.legacy.names boolean. determine if legacy alias should be added
#'                          if TRUE, will add the legacy names as alias for all imported functions
#'                               will add alias even if no library is imported in this call
#'                          only use for compatibility
#'                          default: FALSE
#'
#' @param with.verbose boolean. determine if verbose information should be printed
#'                     default: FALSE
#'
#' @return invisible NULL
#'
LibImportTools.import = function(requested.lib = c(
                                     "Graph.Clustering",
                                     "Graph",
                                     "InfoTheory",
                                     "MiscUtility"
                                 ),
                                 with.force.reimport = FALSE,
                                 with.mtime.check = TRUE,
                                 with.no.dependency = FALSE,
                                 with.legacy.names = FALSE,
                                 with.verbose = FALSE) {
    verbosePrint = function(...) NULL
    if (with.verbose) {
        verbosePrint = function(...) print(paste(...))
    }
    # select lib to import
    if (identical(requested.lib, "All")) {
        requested.lib = .LibImportTools.Const.KnownLibs
    }
    requested.lib = Filter(
        function(x) x %in% .LibImportTools.Const.KnownLibs,
        requested.lib
    )
    if (!with.force.reimport) {
        verbosePrint("filtering out imported lib")
        requested.lib = Filter(
            function(x) !(x %in% names(.LibImportTools.Global.ImportedLibs)),
            requested.lib
        )
    } else if (with.mtime.check) {
        verbosePrint("checking mtime")
        requested.lib = Filter(
            function(x)
                !(x %in% names(.LibImportTools.Global.ImportedLibs) &&
                    .LibImportTools.Global.ImportedLibs[x] >= file.mtime(.LibImportTools.getLibFileLoc(x))),
            requested.lib
        )
    }
    .LibImportTools.Global.Dependency <<- NULL
    if (length(requested.lib) == 0) {
        verbosePrint("No library needs to be imported")
    } else {
        # import requested lib
        currentImported = NULL
        for (libName in requested.lib) {
            verbosePrint("Importing", libName)
            .LibImportTools.importLibFile(libName, verbosePrint)
            currentImported[libName] = file.mtime(.LibImportTools.getLibFileLoc(libName))
        }
        # import dependencies
        .LibImportTools.Global.Dependency <<- Filter(
            function(x) !(x %in% requested.lib),
            unique(.LibImportTools.Global.Dependency)
        )
        needToImport = Filter(
            function(x) !(x %in% names(.LibImportTools.Global.ImportedLibs)),
            .LibImportTools.Global.Dependency
        )
        if (with.mtime.check) {
            verbosePrint("checking dependency mtime")
            needToImport = Filter(
                function(x)
                    !(x %in% names(.LibImportTools.Global.ImportedLibs) &&
                        .LibImportTools.Global.ImportedLibs[x] >= file.mtime(.LibImportTools.getLibFileLoc(x))),
                needToImport
            )
        }
        verbosePrint(length(needToImport), "dependencies needed")
        if (!with.no.dependency && length(needToImport) != 0) {
            verbosePrint("Importing dependencies")
            for (libName in needToImport) {
                verbosePrint("Importing", libName)
                .LibImportTools.importLibFile(libName, verbosePrint)
                currentImported[libName] = file.mtime(.LibImportTools.getLibFileLoc(libName))
            }
        }
        # update record
        verbosePrint(length(currentImported), "libraries imported")
        .LibImportTools.Global.ImportedLibs[names(currentImported)] <<- currentImported
    }
    # handle legacy interface
    if (with.legacy.names) {
        verbosePrint("Adding legacy names")
        .LibImportTools.importLibFile("LibImportTools.LegacyInterface", verbosePrint)
    }
    return(invisible(NULL))
}

# alias
codelibImport = LibImportTools.import

#'
#' @description change codelib global configurations
#'
#' @param ... key-val pairs to be set in config
#'
#' @return invisible NULL. will overwrite all existing configs
#'
LibImportTools.setConfig = function(...) {
    kv = list(...)
    for (k in names(kv)) {
        .LibImportTools.Global.Config[[k]] <<- kv[[k]]
    }
    return(invisible(NULL))
}

#'
#' @description change codelib global configurations
#'
#' @return (read-only copy of) the codelib configurations as a list
#'
LibImportTools.getConfig = function() {
    return(.LibImportTools.Global.Config)
}

#'
#' @description internal routine to check if a function is imported
#'
#' @param func.name char. the name of the function to call
#'
#' @param with.auto.import boolean. determine if function should be imported when missing
#'                         default: FALSE
#'
#' @return the function named func.name
#'         if such function does not exist, throw a stop when with.auto.import == FALSE
#'             if with.auto.import == TRUE, will attempt to import the library the function belongs to
#'
#' @note wrapper of exists and get
#'
.LibImportTools.getDependentFunc = function(func.name,
                                            with.auto.import = .LibImportTools.Global.Config$auto.import.dependent.func) {
    if (exists(func.name, where = .GlobalEnv)) {
        return(get(func.name, pos = .GlobalEnv))
    } else if (with.auto.import) {
        # resolve lib name
        funcNameStruct = strsplit(func.name, ".", fixed = TRUE)[[1]]
        knownLib = LibImportTools.getKnownLib()
        isImportSuccess = FALSE
        for (i in rev(seq_len(length(funcNameStruct) - 1))) {
            testLibName = paste(funcNameStruct[1:i], collapse = '.')
            if (testLibName %in% knownLib) {
                LibImportTools.import(testLibName)
                isImportSuccess = TRUE
                break
            }
        }
        if (isImportSuccess) {
            .LibImportTools.getDependentFunc(func.name, with.auto.import = FALSE)
        } else {
            stop(paste("Cannot find function", func.name))
        }
    } else {
        stop(paste("Dependent function", func.name, "is not imported"))
    }
}

# auto import when sourcing
# a bit hacky
if (exists(".LibImportTools.SourceArgs")) {
    do.call(LibImportTools.import, get(".LibImportTools.SourceArgs"))
    rm(".LibImportTools.SourceArgs")
}
