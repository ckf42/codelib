#'
#' @description convert correlation matrix to distance matrix
#'
#' @param corrMatrix input correlation matrix C
#'
#' @return the distance matrix computed as sqrt(2(1-C))
#'
corrToDist = function(corrMatrix){
    return(sqrt(2 * (1 - corrMatrix)))
}
#'
#' @description convert distance matrix to correlation matrix
#'
#' @param corrMatrix input distance matrix D
#'
#' @return the correlation matrix computed as 1-D^2/2
#'
distToCorr = function(distMatrix){
    return(1 - distMatrix * distMatrix / 2)
}

#'
#' @description Compute the Pearson correlation distance matrix
#'
#' @param listOfSeries a list of equal length numeric vectors.
#'                     each vector is a time series on the same time interval
#'
#' @param tau integer, or Inf. The time length concerned
#'            each matrix is computed with only tau data points
#'            if tau <= 2, will return a full-1 matrix
#'            default: Inf
#'
#' @return a list of Pearson correlation distance matrix
#'         each matrix is named according to the names in listOfSeries
#'         if tau is at least the length of the series, only one matrix is returned
#'
Pearson_correlation_matrix = function(listOfSeries, tau = Inf) {
    n = length(listOfSeries)
    timeLen = length(listOfSeries[[1]])
    tau = min(tau, timeLen)
    if (tau == timeLen) {
        if (tau <= 2) {
            return(matrix(1, n, n,
                dimnames = replicate(2, names(listOfSeries), simplify = FALSE)
            ))
        } else {
            corrMatrix = matrix(unlist(listOfSeries), ncol = length(listOfSeries), byrow = FALSE)
            corrMatrix = cor(corrMatrix, use = 'all.obs', method = 'pearson')
            colnames(corrMatrix) = rownames(corrMatrix) = names(listOfSeries)
            return(corrMatrix)
        }
    } else {
        resCount = (timeLen + tau - 1) %/% tau
        res = replicate(resCount, NA, simplify = FALSE)
        for (idx in seq_len(resCount)) {
            res[[idx]] = Pearson_correlation_matrix(
                lapply(
                    listOfSeries,
                    function(x) x[(1 + (idx - 1) * tau):min(idx * tau, timeLen)]
                ), Inf
            )
        }
        return(res)
    }
}

#'
#' @description compute the partial correlation matrix
#'
#' @param corrMatrix numeric matrix. the input correlation matrix
#'
#' @param regularizationPara boolean, or a numeric. parameter for regulatization
#'                           TRUE is alias of 0.2, FALSE is alias of 0
#'                           default: 0
#'
#' @param mixMatrix NULL, or numeric matrix. used to mix with corrMatrix
#'                  if NULL, no mixing (same as mixMatrix = 0)
#'                  otherwise assumed to have the same shape as corrMatrix
#'                  default: NULL
#'
#' @param mixPara numeric. the coefficient for mixing
#'                default: 0
#'
#' @return the partial correlation matrix.
#'         if regularizationPara is not 0, the convex combination of corrMatrix
#'             and identity matrix is used to keep diagonal of precision nonnegative
#'         if mixMatrix is not NULL and mxPara is not 0, mixMatrix will be added before regularizing
#'
partial_corr = function(corrMatrix, regularizationPara = 0, mixMatrix = NULL, mixPara = 0){
    if (isTRUE(regularizationPara)){
        regularizationPara = 0.2
    } else if (isFALSE(regularizationPara)){
        regularizationPara = 0
    }
    if (!is.null(mixMatrix) && mixPara != 0){
        if (any(dim(corrMatrix) != dim(mixMatrix))){
            stop("in partial_corr, shape of corrMatrix does not match shape of mixMatrix")
        }
        corrMatrix = (1 - mixPara) * corrMatrix + mixPara * mixMatrix
    }
    if (regularizationPara != 0){
        corrMatrix = (1 - regularizationPara) * corrMatrix + regularizationPara * diag(nrow(corrMatrix))
    }
    precisionMatrix = MASS::ginv(corrMatrix)
    precisionDiagSqrt = sqrt(diag(precisionMatrix))
    return(-precisionMatrix / outer(precisionDiagSqrt, precisionDiagSqrt))
}

#'
#' @description compute partial correlation matrix from distance matrix and transform into distance matrix
#'
#' @param distMatrix numeric matrix. the input distance matrix
#'
#' @param regularizationPara boolean, or a numeric. passed to partial_corr directly
#'                           default: 0
#'
#' @param mixMatrix NULL, or numeric matrix. used to mix with corrMatrix
#'                  if NULL, no mixing (same as mixMatrix = 0)
#'                  otherwise assumed to have the same shape as corrMatrix
#'                  default: NULL
#'
#' @param mixPara numeric. the coefficient for mixing
#'                default: 0
#'
#' @return a numeric matrix. the distance matrix of the partial correlation matrix.
#'
#' @note wrapper of partial_corr for distance matrix
#'
pcor_dist = function(distMatrix, regularizationPara = 0, mixMatrix = NULL, mixPara = 0){
    return(corrToDist(partial_corr(distToCorr(distMatrix), regularizationPara, mixMatrix, mixPara)))
}

#'
#' @description normalize a vector
#'
#' @param rawSeq numeric vector. the vector to be normalized on
#'
#' @param toZscore boolean. determine how to normalize rawSeq
#'                 if TRUE, reduce to Z-score
#'                 if FALSE, linear scale to [-1, 1]
#'                 default: TRUE
#'
#' @return a normalized numeric vector of the same length as rawSeq
#'
linearNormalize = function(rawSeq, toZscore = TRUE) {
    if (toZscore) {
        return((rawSeq - mean(rawSeq)) / sd(rawSeq))
    } else {
        mx = max(rawSeq)
        mn = min(rawSeq)
        return((rawSeq - mn) / (mx - mn))
    }
}

#'
#' @description normalize a vector
#'
#' @param listOfSeq list of numeric vectors. the vectors to be normalized on
#'
#' @param toZscore boolean. determine how to normalize rawSeq
#'                 if TRUE, reduce to Z-score
#'                 if FALSE, linear scale to [-1, 1]
#'                 default: TRUE
#'
#' @return a list of normalized numeric vectors
#'
#' @note wrapper of linearNormalize
#'
linearNormalize_list = function(listOfSeq, toZscore = TRUE) {
    return(lapply(
        listOfSeq,
        function(x) linearNormalize(x, toZscore = toZscore)
    ))
}

#'
#' @description compute the log return
#'
#' @param rawSeq a numeric vector, represent the time sequence
#'
#' @return a numeric vector recording the log return of rawSeq. Of length length(rawSeq) - 1
#'
toLogReturn = function(rawSeq){
    l = length(rawSeq)
    return(log(rawSeq[2:l] / rawSeq[1:(l - 1)]))
}

#'
#' @description compute the log return
#'
#' @param listOfSeq a list of numeric vector.
#'                  each representing a time sequence on the same time period
#'
#' @return a list of numeric vectors recording the log return of the sequences.
#'
toLogReturn_list = function(listOfSeq){
    return(lapply(listOfSeq, toLogReturn))
}

#' @description linearly interpolate a time series
#'
#' @param dataSeq numeric vector. the time series to be interpolate
#'
#' @param addPt integer. the number of points to be inserted between two points
#'              in dataSeq
#'
#' @return a numeric of interpolated series, of length (length(dataSeq) - 1) * (addPt + 1) + 1
linearInterpolate = function(dataSeq, addPt = 1){
    n = length(dataSeq)
    return(c(unlist(lapply(seq_len(n - 1),
                           function(idx)dataSeq[idx] + 0:addPt * (dataSeq[idx + 1] - dataSeq[idx]) / (addPt + 1))),
             dataSeq[n]))
}

#'
#' @description compute the l^\infty norm
#'
#' @param input1 numeric vector/matrix
#'
#' @param input2 numeric vector/matrix. assumed to have (or can be convert to) same shape as input1
#'               default: 0
#'
#' @return the l^\infty norm of input1 - input2
#'         if input2 is not given, the l^\infty norm of input1
#'
l_inf_norm = function(input1, input2 = 0){
    return(max(abs(input1 - input2)))
}

#'
#' @description determine if a graph is a tree
#'
#' @param g igraph graph object. the graph to be check
#'
#' @return boolean indicates if g is a tree
#'
#' @note this function is not optimized
#'
is.tree = function(g){
    return(is_connected(g) && vcount(g) - 1 == ecount(g))
}

#'
#' @description determine if a graph is a forest (a collection of at least one tree)
#'
#' @param g igraph graph object. the graph to be check
#'
#' @return boolean indicates if g is a forest
#'
#' @note this function is not optimized
#'
is.forest = function(g){
    return(all(sapply(decompose(g), function(subG)vcount(subG) - 1 == ecount(subG))))
}

#'
#' @description find the Jordan center of a tree
#'
#' @param gTree igraph graph object. Assumed tree
#'
#' @return vertex index of the center of the tree
#'
#' @references ?
#'
#' @note for weighted case,
#'           this implementation uses the naive algorithm (compare pairwise distance)
#'           basically brute force
#'
get_tree_center = function(gTree){
    if (is.weighted(gTree)){
        if (vcount(gTree) <= 2){
            return(1)
        }
        v2 = which.max(distances(gTree, 1, weights = NA))
        v3 = which.max(distances(gTree, v2, weights = NA))
        geodesicPath = unlist(shortest_paths(gTree, v2, v3, weights = NA, output = 'vpath')$vpath)
        # todo reduce number of shortest paths calculated
        return(geodesicPath[(length(geodesicPath) + 1) %/% 2])
    } else {
        return(which.min(apply(distances(gTree), 1, max)))
    }
}

# merged in get_tree_center
# #'
# #' @description find the Jordan center of a weighted tree
# #'
# #' @param g igraph graph object. Assumed tree
# #'
# #' @return vertex index of the center of the tree
# #'
# #' @note this implementation uses the naive algorithm (compare pairwise distance)
# #'       for unweighted tree, get_tree_center would be much faster as this implementation
# #'           is basically brute force
# #'
# get_weighted_tree_center = function(g){
#     return(which.min(apply(distances(g), 1, max)))
# }

#'
#' @description get the tree layout with center as root
#'
#' @param gTree igraph graph object. assumed to be a tree
#'
#' @return a two column matrix representing the coordinates of the nodes
#'         the layout is the same as igraph::layout_as_tree, except the root is the Jordan center
#'
#' @note the Jordan center is computed with identical edge weights if gTree is unweighted
#'
layout_as_tree_with_center_root = function(gTree){
    return(layout_as_tree(gTree, root = get_tree_center(gTree)))
}

# merged in layout_as_tree_with_center_root
# #'
# #' @description get the tree layout with center as root
# #'
# #' @param gTree igraph graph object. assumed to be a weighted tree
# #'
# #' @return a two column matrix representing the coordinates of the nodes
# #'         the layout is the same as igraph::layout_as_tree, except the root is the Jordan center
# #'
# #' @note the Jordan center is computed with edge weights
# #'       if the tree is unweighted, layout_as_tree_with_center_root is faster
# #'
# layout_as_weighted_tree_with_center_root = function(gTree){
#     return(layout_as_tree(gTree, root = get_tree_center(gTree)))
# }

# # merged in layout_as_tree_with_center_root
# #'
# #' @description get the tree layout with center as root
# #'
# #' @param gTree igraph graph object. assumed to be a tree
# #'
# #' @return a two column matrix representing the coordinates of the nodes
# #'         the layout is the same as igraph::layout_as_tree, except the root is the Jordan center
# #'
# #' @note wrapper of layout_as_tree_with_center_root and layout_as_weighted_tree_with_center_root
# #'
# layout_as_rooted_tree = function(gTree){
#     return(layout_as_tree_with_center_root(gTree))
# }

#'
#' @description plot a tree, or a forest
#'
#' @param gForest igraph graph object. assumed to be a forest
#'
#' @param ... other argument passed to plot
#'
#' @return same as plot, which is NULL
#'
#' @note wrapper of plot function with layout overridden
#'
plot_tree = function(gForest, ...){
    if (!is.forest(gForest)){
        stop("In plot_tree, the input graph is not a forest")
    }
    return(plot(gForest,
                ...,
                layout = (if (is.tree(gForest)) layout_as_tree_with_center_root else layout_as_tree)(gForest)))
}

#'
#' @description cutoff the matrix according to the entries
#'
#' @param targetMatrix numeric matrix.
#'
#' @param weightThreshold numeric. the threshold value to transform values
#'
#' @param equalMeansBelow boolean. determine if entries same as threshold is counted as below threshold
#'                        if TRUE, entries with the same value as threshold will be replaced as belowThreshold
#'                        if FALSE, entries with the same value as threshold will be replaced as aboveThreshold
#'
#' @param belowThreshold numeric. what below-threshold values should be transformed to
#'                       default: 0
#'
#' @param aboveThreshold numeric. what equal-and-above-threshold values should be transformed to
#'                       default: 1
#'
#' @return a numeric matrix of the same shape as targetMatrix,
#'             but every entry below weightThreshold is replaced with belowThreshold,
#'             every entry equal or above is replaced with aboveThreshold
#'
#' @note wrapper of ifelse
#'
matrixCutOff = function(targetMatrix, weightThreshold, equalMeansBelow, belowThreshold = 0, aboveThreshold = 1){
    matrixMask = (targetMatrix < weightThreshold)
    if (equalMeansBelow){
        matrixMask = matrixMask | (targetMatrix == weightThreshold)
    }
    return(ifelse(matrixMask, belowThreshold, aboveThreshold))
}

#'
#' @description remove edges from the graph with cutoff threshold
#'
#' @param g igraph graph object. the graph to be cut.
#'          assumed to have edge attribute "weight"
#'
#' @param weightThreshold numeric. the weight threshold to cut edges
#'
#' @param removeBelow boolean. determine if edges weight below the threshold should be removed.
#'                    if TRUE, edges weight above the threshold would be removed
#'                    if FALSE, edges weight above the threshold would be removed
#'
#' @param includeEqual boolean. determine if edges weight equal the threshold would be removed
#'                     if TRUE, will also remove edges with same weight as threshold
#'                     if FALSE, edges with same weight as threshold will be kept
#'
#' @return igraph graph object. the graph with targeted edges removed
#'
graphEdgeCutOff = function(g, weightThreshold, removeBelow, includeEqual){
    edgesToCutMask = NULL
    if (removeBelow){
        edgesToCutMask = (E(g)$weight < weightThreshold)
    } else {
        edgesToCutMask = (E(g)$weight > weightThreshold)
    }
    if (includeEqual){
        edgesToCutMask = edgesToCutMask | (E(g)$weight == weightThreshold)
    }
    return(delete_edges(g, E(g)[edgesToCutMask]))
}

#'
#' @description find the evolution of the communities in the data
#'
#' @param listOfData a list of numeric vector.
#'                   each vector is a time series of the same quantitiy on the same time period
#'                   all vectors should have same length
#'                   normalization and transformation should be done before passing in
#'
#' @param matrixMethod a function to generate (weighted) adjacency matrix
#'                     the function should take in a list of numeric vectors and produce a numeric matrix
#'                     segments of listOfData will be passed in
#'
#' @param graphMethod a function to generate graphs to cluster
#'                    the function should take in a numeric matrix and produce a igraph graph object
#'                    output from matrixMethod will passed in directly
#'
#' @param clusterMethod a function to cluster graphs
#'                      it should take a igraph graph object as the only input
#'                      output from graphMethod will be passed in directly
#'                      extra parameters should be enclosed before passing in
#'
#' @param windowSize integer. the size of the sliding window
#'                   assumed positive
#'                   segments of listOfData of this size will be processed in each round
#'
#' @param windowMoveDist integer, or NULL determine how far two consective windows should be
#'                       if integer, the window will move this amount
#'                       if NULL, windows will be closely patched (no overlapping, same as windowSize)
#'                       default: NULL
#'
#' @param layoutMethod function. the method to compute graph layout.
#'                     the layout will be computed from the first graph
#'                     default: igraph::layout.kamada.kawai
#'
#' @param computeARI boolean. determine if pairwise ARI matrix should be computed
#'                   the computation takes time if the number of frames is large
#'                   the coputation is passed to adjusted_Rand_index
#'                   default: FALSE
#'
#' @param computeNMI boolean. determine if pairwise NMI matrix should be computed
#'                   the computation takes time if the number of frames is large
#'                   the coputation is passed to clustering_NMI_similarity
#'                   default: FALSE
#'
#' @param debugMsg boolean. determine if debug message should be printed
#'                 default: FALSE
#'
#' @return a list containing
#'             n, integer, the number of vertices
#'             nFrames, an integer representing the number of time frames
#'             windowSize, the window size
#'             windowMoveDist, the distance the window move
#'             layout, a numeric matrix with 2 columns, the layout to plot the first graph
#'             communities, a list of igraph communities objects
#'             matrices, a list of matrices generated from matrixMethod
#'             graphs, a list of igraph graph objects generated from graphMethod
#'         this two matrices will also be presented if the corresponding config
#'          is set as TRUE:
#'             ARI, a numeric matrix of size nFrame x nFrame representing the adjusted Rand index (ARI)
#'             NMI, a numeric matrix of size nFrame x nFrame representing the normalized mutual information (NMI)
#'
cluster_evolution = function(listOfData,
                             matrixMethod,
                             graphMethod,
                             clusterMethod,
                             windowSize,
                             windowMoveDist = NULL,
                             layoutMethod = layout.kamada.kawai,
                             computeARI = FALSE,
                             computeNMI = FALSE,
                             debugMsg = FALSE){
    windowBegin = 1 # window: [windowBegin, windowBegin + windowSize - 1]
    n = length(listOfData)
    nDays = length(listOfData[[1]])
    commList = list()
    matrixList = list()
    graphList = list()
    firstGraphLayout = NULL
    if (is.null(windowMoveDist)){
        windowMoveDist = windowSize
    }
    while (windowBegin + windowSize < nDays){
        if (debugMsg){
            print(paste(format(Sys.time(), '%T'),
                        "processing [",
                        windowBegin,
                        ",",
                        windowBegin + windowSize - 1,
                        "] out of",
                        nDays))
        }
        # ? can lapply be optimized?
        dataSegment = lapply(listOfData, function(dataSeq)dataSeq[windowBegin:(windowBegin + windowSize - 1)])
        thisMatrix = matrixMethod(dataSegment)
        matrixList[[length(matrixList) + 1]] = thisMatrix
        thisGraph = graphMethod(thisMatrix)
        graphList[[length(graphList) + 1]] = thisGraph
        if (is.null(firstGraphLayout)){
            firstGraphLayout = layoutMethod(thisGraph)
        }
        commList[[length(commList) + 1]] = clusterMethod(thisGraph)
        windowBegin = windowBegin + windowMoveDist
    }
    if (windowBegin <= nDays){
        warning(paste(nDays - (windowBegin - windowMoveDist + windowSize - 1), "data points are not used"))
    }
    returnAns = list(n = n,
                     nFrames = length(commList),
                     windowSize = windowSize,
                     windowMoveDist = windowMoveDist,
                     methods = list(matrix = matrixMethod,
                                    graph = graphMethod,
                                    cluster = clusterMethod),
                     layout = firstGraphLayout,
                     communities = commList,
                     matrices = matrixList,
                     graphs = graphList)
    if (computeARI){
        if (debugMsg){
            print(paste(format(Sys.time(), '%T'), "compute ARI"))
        }
        returnAns$ARI = batch_sim(commList, adjusted_Rand_index)
    }
    if (computeNMI){
        if (debugMsg){
            print(paste(format(Sys.time(), '%T'), "compute NMI"))
        }
        returnAns$NMI = batch_sim(commList, clustering_NMI_similarity)
    }
    return(returnAns)
}

#'
#' @description plot all graphs for the evolution
#'
#' @param evolutionTrack a list from cluster_evolution. the object to play
#'
#' @param fps numeric. determine the time intervel between two plots
#'            the time interval is 1 / fps
#'            the number of plots in one second is approximately fps
#'
#' @return no return
#'
plot_cluster_evolution = function(evolutionTrack, fps = 4){
    if (fps > 20){
        warning(paste("fps =", fps, "is too high. may not be able to plot graphs"))
    }
    g = make_empty_graph(evolutionTrack$n, directed = FALSE)
    for (idx in seq_len(evolutionTrack$nFrames)){
        plot(evolutionTrack$communities[[idx]], g, layout = evolutionTrack$layout)
        # plot(evolutionTrack$graphs[[idx]], layout = evolutionTrack$layout)
        mtext(paste(idx, evolutionTrack$nFrames, sep = '/'), side = 1)
        Sys.sleep(1 / fps)
    }
}

#'
#' @description plot clustering result
#'
#' @param g igraph::graph object. the graph in question
#'
#' @param clusterCommunities igraph::communities object. how the graph is clustered
#'
#' @param ... all other parameters are passed to plot
#'
#' @return no return
#'
#' @note wrapper for plot
#'
plot_cluster = function(g, clusterCommunities, ...){
    plot(g, mark.groups=clusterCommunities, ...)
}

#'
#' @description plot clustering result
#'
#' @param g igraph::graph object. the graph in question
#'
#' @param clusterFunc function. should takes only one parameter (the graph)
#'                        and return a igraph::communities object
#'
#' @param ... all other parameters are passed to plot
#'
#' @return the return from clusterFunc
#'
#' @note wrapper for plot
#'
plot_after_clustering = function(g, clusterFunc, ...){
    clusterRes = clusterFunc(g)
    plot_cluster(g, clusterRes, ...)
    return(clusterRes)
}

#'
#' @description compute the Cronbach's alpha coefficient
#'
#' @param listOfData a list of equal length numeric vectors
#'                   each vector is data series of a feature
#'
#' @param findOneOutCoeff boolean.
#'                        Determine if one-out Cronbach alpha should be computed.
#'                        default: FALSE
#'
#' @return a numeric representing the coefficient
#'         if findOneOutCoeff is TRUE, a numeric vector of the same length as listOfData
#'             where the entries represent the Cronbach alpha coefficient after removing one feature
#'
CronbachAlpha = function(listOfData, findOneOutCoeff = FALSE){
    k = length(listOfData)
    seriesLength = length(listOfData[[1]])
    sumOfFeatures = sapply(seq_len(seriesLength),
                           function(idx)
                               sum(sapply(seq_len(k),
                                          function(featureIdx)
                                              listOfData[[featureIdx]][[idx]]))) # better method?
    varVect = sapply(seq_len(k),
                     function(featureIdx)
                         var(listOfData[[featureIdx]]))
    res = NULL
    sumOfVar = sum(varVect)
    if (findOneOutCoeff){
        varOfOneOutSum = sapply(seq_len(k),
                                function(featureIdx)
                                    var(sumOfFeatures - listOfData[[featureIdx]]))
        oneOutSumOfVar = sumOfVar - varVect
        res = (1 + 1 / (k - 1)) * (1 - oneOutSumOfVar / varOfOneOutSum)
    } else {
        varOfSum = var(sumOfFeatures)
        res = (1 + 1 / (k - 1)) * (1 - sumOfVar / varOfSum)
    }
    return(res)
}


#'
#' @description plot the overlapping communities on a graph
#'
#' @param g igraph graph object. assumed to be a undirected unweighted simple
#'
#' @param overlapCommunities a numeric matrix representing the belonging coefficients,
#'                               or a list containing the modularity and the matrix
#'                           this input is passed directly to overlapCommInfo as belongingMatrix
#'
#' @param ... other argument passed to plot
#'
#' @return same as plot, which is NULL
#'
#' @note wrapper of plot function with mark.groups overridden
#'
plot_overlapComm = function(g, overlapCommunities, ...){
    commInfo = overlapCommInfo(overlapCommunities)
    commMembers = commInfo$communityMembers
    colorPal = rainbow(length(commMembers), alpha = NULL)
    overlapCount = length(commInfo$overlappedVertex)
    return(plot(g,
                mark.groups = commMembers,
                vertex.shape = if (overlapCount == 0) "circle" else "pie",
                vertex.pie = belongVectListFromMatrix(commInfo$belongingMatrix),
                vertex.pie.color = list(colorPal),
                vertex.color = if (overlapCount == 0) colorPal[commInfo$vertexClass] else NULL,
                ...))
}

#'
#' @description plot the overlapping communities on a graph directly with algorithms
#'
#' @param g igraph graph object. assumed to be a undirected unweighted simple
#'
#' @param algo a function that takes a igraph graph object and return a numeric matrix
#'
#' @param ... other argument passed to algo
#'
#' @return the output of the clustering from algo
#'
#' @note wrapper of plot_overlapComm
#'
plot_overlapComm_algo = function(g, algo, ...){
    res = algo(g, ...)
    plot_overlapComm(g, res)
    return(res)
}

#'
#' @description compute the size of the component of a vertex
#'
#' @param g igraph graph object.
#'
#' @param vs igraph vertex sequence. the id of the target vertex
#'
#' @return an integer vector representing the size of the component which vs belongs to
#'
getComponentSize = function(g, vs){
    comp = components(g)
    return(comp$csize[comp$membership[vs]])
}

#'
#' @description compute the vertices in the same component as the given vertex
#'
#' @param g igraph graph object.
#'
#' @param vs igraph vertex sequence. the id of the target vertex
#'
#' @return a list of integer vectors representing the vertices which are in the same
#'             component
#'         if vs has only one vertex, returns the integer vector
#'
getComponentMembers = function(g, vs){
    comp = components(g)$membership
    return(sapply(vs, function(vid)which(comp == comp[vid]), simplify = "vector"))
}

#'
#' @description align string by centering
#'
#' @param lines a vector of strings
#'
#' @param padding a string of length 1, or a vector of such strings
#'                Used to pad strings
#'                if a single string is provided, all strings use this pad
#'                if a vector, there should be exactly one pad for every string, inclusing empty ones
#'                default: " ", a space character
#'
#' @param stripWSFirst boolean. determine if leading and trailing white spaces shuold be trimmed first
#'                     if TRUE, strings are processed with trimws() before padding
#'                     if FALSE, strings are padded as inputed
#'                     default: TRUE
#'
#' @return the same vector of strings, but the strings are centered by padding on both sides
#'         empty strings are not processed
#'
centerLinesOfStrings = function(lines, padding = " ", stripWSFirst = TRUE){
    numLines = length(lines)
    if (stripWSFirst){
        lines = sapply(lines, trimws)
    }
    if (any(sapply(padding, function(pad)nchar(pad) != 1))){
        stop("padding is not of length 1")
    }
    if (length(padding) != 1){
        if (length(padding) != numLines){
            stop("Number of paddings does not match the numbers of lines provided")
        }
    } else {
        padding = rep(padding, numLines)
    }
    alignIndices = sapply(lines, function(x)as.integer((nchar(x) + 1) / 2))
    strLen = sapply(lines, nchar)
    preLen = max(alignIndices) - alignIndices
    postLen = max(strLen) - strLen - preLen
    for (lIdx in seq_along(lines)){
        if (nchar(lines[lIdx]) == 0){
            next
        }
        lines[lIdx] = paste0(paste(rep(padding[lIdx], preLen[lIdx]), collapse = ''),
                             lines[lIdx],
                             paste(rep(padding[lIdx], preLen[lIdx]), collapse = ''))
    }
    return(lines)
}

#'
#' @description find the top results
#'
#' @param val numeric vector. The values to look at
#'
#' @param N integer. The number of results to return
#'          default: 10
#'
#' @param takeMax boolean. Determine if the largest ones should be returned
#'                default: TRUE
#'
#' @param valOnly boolean. Determine if only the values should be returned
#'                default: FALSE
#'
#' @return  if valOnly == FALSE, a list containing two equal-length vectors:
#'              values: the N largest (if takeMax == TRUE, otherwise smallest)
#'                          values in val
#'              indices: the corresponding indices in val
#'          if valOnly == FALSE, only the values vector would be returned
#'
topResults = function(val, N = 10, takeMax = TRUE, valOnly = FALSE){
    targetIdx = order(val,
                      decreasing = takeMax)[1:min(N, length(val))]
    if (valOnly){
        return(val[targetIdx])
    } else {
        return(list(indices = targetIdx,
                    values = val[targetIdx]))
    }
}

#'
#' @description clipping to a range
#'
#' @param x numeric vector
#'
#' @param minVal numeric. the minimal value outputed.
#'               can be -Inf
#'               default: 0
#'
#' @param maxVal numeric. the maximal value outputed.
#'               can be Inf
#'               assumed to be not less than minVal
#'               default: 1
#'
#' @return a numeric vector of the clipped value
#'
#' @note wrapper of pmin and pmax
#'
clipRange = function(x, minVal = 0, maxVal = 1){
    return(pmin(pmax(x, minVal), maxVal))
}
