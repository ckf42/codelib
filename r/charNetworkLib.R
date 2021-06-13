# this script provides the following functions:
# 
# planar_maximally_filtered_graph
# proportional_degree_network
# 
# Please goto the corresponding function definition for detail description

if (!require(igraph)){
    stop('these functions requires igraph')
}

#' 
#' @description constructing the Planar Maximally Filtered Graph (PMFG)
#' 
#' @param similarityMatrix numeric matrix. similarity between items. 
#'                         assumed symmetric and has nonnegative entries
#' 
#' @param forceLibrary NULL, or one of the following string: 
#'                         'MEGENA', 'RBGL', 'IMPLEMENTED'
#'                     affect which routine to use for planarity testing
#'                     'MEGENA':      MEGENA::planaritytest
#'                     'RBGL':        RBGL::boyerMyrvoldPlanarityTest (\~20 times slower than 'MEGENA')
#'                     'IMPLEMENTED': is_planar_graph_DMP implemented above (\~60 times slower than 'RBGL')
#'                     if NULL or not any of above, will use the first available in the list
#'                     default: NULL
#' 
#' @param isSimilarity boolean. indicate if similarityMatrix denote similarity 
#'                     (TRUE) or dissimilarity (FALSE)
#'                     default: TRUE
#' 
#' @return igraph graph object of the PMFG constructed from the 
#'         similarity matrix
#' 
#' @references 
#' 
# TODO speed up
planar_maximally_filtered_graph = function(similarityMatrix, forceLibrary = NULL, isSimilarity = TRUE){
    # if (is.null(forceLibrary)){
    #     if (require(MEGENA)){
    #         forceLibrary = 'MEGENA'
    #     } else if (require(RBGL)){
    #         forceLibrary = 'RBGL'
    #     } else {
    #         forceLibrary = 'IMPLEMENTED'
    #     }
    # }
    # if (forceLibrary == 'MEGENA' && !require(MEGENA)){
    #     stop("Request library MEGENA is not available")
    # }
    # if (forceLibrary == 'RBGL' && !require(RBGL)){
    #     stop("Request library RBGL is not available")
    # }
    supportLibList = c('MEGENA', 'RBGL', 'IMPLEMENTED')
    supportLibCheckAndRequire = c(quote(requireNamespace("MEGENA", quietly = TRUE)), 
                                  quote(requireNamespace("RBGL", quietly = TRUE)),
                                  quote(if (file.exists("DMPLib.r")){
                                      source("DMPLib.r", echo = FALSE); TRUE
                                  } else FALSE))
    # process default
    if (is.null(forceLibrary) || !(forceLibrary %in% supportLibList)){
        forceLibrary = supportLibList[Position(eval, 
                                               supportLibCheckAndRequire, 
                                               nomatch = NULL)]
        if (length(forceLibrary) == 0){
            stop(paste("No library available.", 
                       "Please check if the supported libraries are installed,", 
                       "or if DMPLib.r is in the same directory as this file"))
        } else {
            warning(paste("Library", forceLibrary, "automatically selected"))
        }
    } else {
        # san check user requested lib
        if (!eval(supportLibCheckAndRequire[[match(forceLibrary, supportLibList)]])){
            stop(paste("Request library", forceLibrary, "is not available"))
        }
    }
    n = nrow(similarityMatrix)
    planarity_test_routine = switch(forceLibrary, 
                                    MEGENA = function(g){
                                        gEdgeList = as_edgelist(g, FALSE)
                                        return(MEGENA::planaritytest(n, gEdgeList[, 1], gEdgeList[, 2]))
                                    }, 
                                    RBGL = function(g)RBGL::boyerMyrvoldPlanarityTest(as_graphnel(g)), 
                                    IMPLEMENTED = is_planar_graph_DMP, 
                                    NULL)
    # requested routine not available
    # if (is.null(planarity_test_routine)){
    #     stop(paste0('In planar_maximally_filtered_graph, forceLibrary = ', 
    #                  forceLibrary, 
    #                  ' is not available. '))
    # }
    # refer from lower trig
    similarityMatrix[upper.tri(similarityMatrix, diag = TRUE)] = NA
    simOrdering = order(similarityMatrix, decreasing = isSimilarity, na.last = NA)
    # remove edge with 0 weight
    # simOrdering[similarityMatrix[simOrdering] == 0] = NULL
    simOrdering = simOrdering[similarityMatrix[simOrdering] != 0]
    # simOrdering = Filter(function(x)similarityMatrix[x] != 0, simOrdering)
    E = make_empty_graph(n, directed = FALSE)
    for (idx in simOrdering){
        i = (idx - 1) %/% n + 1
        j = (idx - 1) %% n + 1  # i < j
        newE = add_edges(E, c(i, j), attr = c(weight = similarityMatrix[idx]))
        if (planarity_test_routine(newE)){
            E = newE
        }
    }
    return(E)
}


#' 
#' @description constructing simplified network with Proportional Degree
#'              (PD) algorithm
#' 
#' @param similarityMatrix numeric matrix. similarity between items. 
#'                         assumed symmetric and has nonnegative entries
#' 
#' @param M NULL, or number of edges in the output graph. 
#'          if NULL, 3|V|-6 (number of edges in the PMFG) will be used
#'          default: NULL
#' 
#' @param isSimilarity boolean. indicate if similarityMatrix denote similarity 
#'                     (TRUE) or dissimilarity (FALSE)
#'                     default: TRUE
#' 
#' @return igraph graph object of the network constructed from the 
#'         similarity matrix with the PD algorithm
#' 
#' @references 
#' 
proportional_degree_network = function(similarityMatrix, M = NULL, isSimilarity = TRUE){
    n = nrow(similarityMatrix)
    sw = colSums(similarityMatrix) - diag(similarityMatrix)
    if (is.null(M)){
        M = 3 * n - 6
    }
    dPrime = sw / sum(sw) * M * 2
    dPrimeCumSumRounded = round(cumsum(dPrime))
    d = rep(0, n)
    d[1] = dPrimeCumSumRounded[1]
    dCumSum = 0
    for (i in 2:n){ # vectorize? 
        dCumSum = dCumSum + d[i - 1]
        d[i] = dPrimeCumSumRounded[i] - dCumSum
    }
    # refer to lower trig, write in upper trig
    similarityMatrix[upper.tri(similarityMatrix, diag = TRUE)] = NA
    simOrdering = order(similarityMatrix, decreasing = isSimilarity, na.last = NA)
    for (idx in simOrdering){
        i = (idx - 1) %/% n + 1
        j = (idx - 1) %% n + 1  # i < j
        if (d[i] > 0 && d[j] > 0){
            similarityMatrix[i, j] = similarityMatrix[j, i]
            d[i] = d[i] - 1
            d[j] = d[j] - 1
        }
    }
    similarityMatrix[is.na(similarityMatrix)] = 0 # remove NA
    return(graph_from_adjacency_matrix(similarityMatrix, 
                                       mode = 'upper', 
                                       weighted = TRUE))
}

#' 
#' @description find the threshold network
#' 
#' @param g igraph graph object, or a numeric matrix. 
#'          the original graph
#'          if it is numeric matrix, it should be the (weighted) adjacency matrix. 
#'          assumed to be undirected
#' 
#' @param h numeric, or Inf. step parameter. 
#'          if numeric, 1/h is the step size
#'          if Inf, edges are added one by one
#' 
#' @param useEigen boolean. 
#'                 determine if algebraic connectivity should be used to determined connectness
#'                 default: FALSE
#' 
#' @param useNormalizedLaplacian boolean. determine if normalized Laplacian should be used
#'                               ignored if useEigen is FALSE
#'                               default: FALSE
#' 
#' @param printThresholdMsg boolean. determine if the threshold should be printed out at the end
#'                          if TRUE, the threshold will be printed
#'                          default: TRUE
#' 
#' @return igraph graph object. the threshold network
#' 
#' @references M. A. Balci , O. Akguller, S. C. Guzel
#'             Hierarchies in communities of UK stock market from the perspective of Brexit
#'             doi: 10.1080/02664763.2020.1796942
#' 
threshold_algo = function(g, h, useEigen = FALSE, useNormalizedLaplacian = TRUE, printThresholdMsg = TRUE){
    if (is.matrix(g)){
        g = graph_from_adjacency_matrix(g, weighted = TRUE, mode = 'undirected')
    }
    emptyG = make_empty_graph(vcount(g), directed = FALSE)
    newG = emptyG
    edgeWeights = E(g)$weight
    if (is.null(edgeWeights)){
        stop("input graph has no edge attribute called weight")
    }
    endpts = t(ends(g, E(g)))
    loopRoutine = is_connected
    if (useEigen){
        loopRoutine = function(targetG){
            tail(eigen(graph.laplacian(targetG, 
                                       normalized = useNormalizedLaplacian, 
                                       weights = NA), 
                       only.values = TRUE, 
                       symmetric = TRUE)$values, 2)[1] > .Machine$double.eps
        }
    }
    edgeOrderIdx = NULL
    if (is.infinite(h)){
        edgeOrderIdx = order(edgeWeights, decreasing = F)
    }
    t = 0
    tau = NA
    while (!loopRoutine(newG)){
        t = t + 1
        if (is.infinite(h)){
            tau = edgeWeights[edgeOrderIdx[t]]
        } else {
            tau = t / h
        }
        # print(tau)
        edgeMask = (edgeWeights <= tau)
        newG = add_edges(emptyG, 
                         as.vector(endpts[, edgeMask]), 
                         weight = edgeWeights[edgeMask])
    }
    if (printThresholdMsg){
        print(paste("threshold val:", tau))
    }
    return(newG)
}

#' 
#' @description generate a network from the adjacency matrix
#' 
#' @param isDirected boolean. Determine if the graph should be directed
#'                   if FALSE, the matrix is first symmetrized
#'                   default: FALSE
#' 
#' @param isWeighted boolean. Determine if the graph should be weighted
#'                   if FALSE, all nonzero entries (after symmetrized) will be taken as 1
#'                   default: TRUE
#' 
#' @param adjacencyMatrix numeric matrix. similarity between items
#' 
#' @return igraph graph object of the graph constructed from the 
#'         adjacency matrix
#' 
#' @note wrapper of igraph::graph_from_adjacency_matrix
#' 
# TODO speed up
# 
complete_network = function(adjacencyMatrix, isDirected = FALSE, isWeighted = TRUE){
    if (!isDirected){
        adjacencyMatrix = (adjacencyMatrix + t(adjacencyMatrix)) / 2
    }
    if (!isWeighted){
        adjacencyMatrix[adjacencyMatrix != 0] = 1
    }
    return(graph_from_adjacency_matrix(adjacencyMatrix, 
                                       mode = (if (isDirected) "directed" else "undirected"), 
                                       weighted = (if (isWeighted) TRUE else NULL), 
                                       diag = FALSE))
}
