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
#' @description find the threshold significance graph
#'
#' @param g igraph::graph object. the original graph
#'          assumed to be weighted
#'
#' @param significance numeric. the cutoff value
#'
#' @param weightName char. the name of edge attribute used
#'                   default: 'weight'
#'
#' @return a igraph::graph object of the result threshold significance graph
#'         the same graph but all edges with weight not exceeding significance removed
#'
#' @note miscFuncLib::graphEdgeCutOff but with fewer parameters
#'
#' @references T. Vyrosta, S. Lyocsab, E. Baumohl. Network-Based Asset Allocation Strategies
#'
#' @references C. K. Tse, J. Liu, F. C. M. Lau. A Network Perspective of the Stock Market
#'
thresholdSignificanceGraph = function(g, significance, weightName = 'weight'){
    if (!is.weighted(g)){
        stop("Input graph is unweighted")
    }
    return(delete.edges(g, E(g)[edge_attr(g, weightName) <= significance]))
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
# TODO speed up?
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

#'
#' @description compute the long-run correlation between time series
#'
#' @param list.of.time.series a list of numeric vectors.
#'                            all vectors are assumed to have the same length
#'
#' @param B numeric. the band width. assumed to be positive
#'
#' @param kernelFunction function. the function used in Andrew's estimate
#'                       assumed to be even L^2 function and values 1 at x = 0
#'
#' @param considerRange numeric, or NA. the maximal shift of the window, in units of B
#'                      also affect where the kernelFunction is evaluated
#'                      (the effective domain is [-(considerRange - 1/B), considerRange - 1/B])
#'                      if NA, will be chosen automatically if kernelFunction is predefined
#'                      if numeric, assumed to be positive.
#'                      Inf is also accepted (consider all possible range)
#'                      if kernelFunction has a bounded support (or domain of significant values),
#'                          consider specifing the bound here for speed up
#'                      default: NA
#'
#' @return a symmetric matrix of dimension n*n with diagonal 1,
#'             where n is the number of series in list.of.time.series
#'         Each entry is a number in [0, 1], higher implies stronger correlation
#'
#' @references T. Vyrosta, S. Lyocsab, E. Baumohl. Network-Based Asset Allocation Strategies
#'
#' @references D. W. K. Andrews. Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation
#'
#' @note not sure about implementation. could/likely be wrong
#'       assuming [Z_t Z_{t-m}] means outer product
#'
#' @note current complexity: n^2 T^2
#'       can be optimize with e.g. discrete Fourier?
#'
# TODO speed up
#      current implementation is quite slow (~6 mins for 50 series of ~4000 pts, full range)
#      on computing omegaDiag, same datasets, ~6 secs
#
longRunCorrelation = function(list.of.time.series,
                              B,
                              kernelFunction,
                              considerRange = NA) {
    n = length(list.of.time.series)
    if (n <= 1){
        stop("Insufficient time series")
    }
    TSize = length(list.of.time.series[[1]])
    if (any(sapply(list.of.time.series, length) != TSize)){
        stop("list.of.time.series contains series of unequal length")
    }
    if (is.na(considerRange)) {
        considerRange = switch(
            as.character(substitute(kernelFunction))[1],
            "quadraticSpectralKernel" = 30,
            "truncatedKernel" = 1,
            "bartlettKernel" = 1,
            "parzenKernel" = 1,
            "tukeyHanningKernel" = 1,
            Inf
        )
        warning(paste("considerRange chosen as", considerRange))
    }
    considerRange = min(abs(considerRange * B), TSize)
    omegaDiag = sapply(list.of.time.series,
                       function(timeSeries) {
                           mean(timeSeries ^ 2) +
                               sum(kernelFunction(seq_len(considerRange - 1) / B) * 2 / TSize *
                                       sapply(seq_len(considerRange - 1),
                                              function(m)
                                                  sum(timeSeries[1:(TSize - m)] * timeSeries[(m + 1):TSize])))
                       })
    res = matrix(0, nrow = n, ncol = n)
    for (i in 2:n) {
        for (j in 1:(i - 1)) {
            omega = sum(kernelFunction((1 - considerRange):(considerRange - 1) / B) / TSize *
                            sapply((1 - considerRange):(considerRange - 1),
                                   function(m)
                                       sum(list.of.time.series[[i]][max(1, 1 - m):min(TSize, TSize - m)] *
                                               list.of.time.series[[j]][max(1, 1 + m):min(TSize, TSize + m)])))
            res[i, j] = res[j, i] = omega / sqrt(omegaDiag[i] * omegaDiag[j])
        }
    }
    diag(res) = 1
    return(res)
}

#'
#' @description kernel function for Andrew's estimate
#'
#' @param x numeric vector
#'
#' @return numeric vector. the values from the Quadratic Spectral kernel function
#'
#' @note this function is one of the common function used in computing Andrew's estimate
#'           (and also in longRunCorrelation)
#'       this function is an even function on real number,
#'           k(0) = 1
#'           continuous at x = 0,
#'           has at most finite discontinuous points,
#'           and is L^2
#'
#' @references D. W. K. Andrews. Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation
#'
quadraticSpectralKernel = function(x) {
    k = 6 * pi * x / 5
    return(ifelse(k == 0, 1, 3 / k ^ 2 * (sin(k) / k - cos(k))))
}

#'
#' @description kernel function for Andrew's estimate
#'
#' @param x numeric vector
#'
#' @return numeric vector. the values from the truncated kernel function
#'
#' @note this function is one of the common function used in computing Andrew's estimate
#'           (and also in longRunCorrelation)
#'       this function is an even function on real number,
#'           k(0) = 1
#'           continuous at x = 0,
#'           has at most finite discontinuous points,
#'           and is L^2
#'
#' @references D. W. K. Andrews. Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation
#'
truncatedKernel = function(x) {
    return(ifelse(abs(x) <= 1, 1, 0))
}

#'
#' @description kernel function for Andrew's estimate
#'
#' @param x numeric vector
#'
#' @return numeric vector. the values from the Bartlett kernel function
#'
#' @note this function is one of the common function used in computing Andrew's estimate
#'           (and also in longRunCorrelation)
#'       this function is an even function on real number,
#'           k(0) = 1
#'           continuous at x = 0,
#'           has at most finite discontinuous points,
#'           and is L^2
#'
#' @references D. W. K. Andrews. Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation
#'
bartlettKernel = function(x) {
    return(ifelse(abs(x) <= 1, 1 - abs(x), 0))
}

#'
#' @description kernel function for Andrew's estimate
#'
#' @param x numeric vector
#'
#' @return numeric vector. the values from the Parzen kernel function
#'
#' @note this function is one of the common function used in computing Andrew's estimate
#'           (and also in longRunCorrelation)
#'       this function is an even function on real number,
#'           k(0) = 1
#'           continuous at x = 0,
#'           has at most finite discontinuous points,
#'           and is L^2
#'
#' @references D. W. K. Andrews. Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation
#'
parzenKernel = function(x) {
    return(ifelse(abs(x) <= 1 / 2,
                  1 - 6 * x ^ 2 + 6 * abs(x) ^ 3,
                  ifelse(abs(x) <= 1,
                         2 * (1 - abs(x)) ^ 3,
                         0)
                  )
           )
}

#'
#' @description kernel function for Andrew's estimate
#'
#' @param x numeric vector
#'
#' @return numeric vector. the values from the Tukey-Hanning kernel function
#'
#' @note this function is one of the common function used in computing Andrew's estimate
#'           (and also in longRunCorrelation)
#'       this function is an even function on real number,
#'           k(0) = 1
#'           continuous at x = 0,
#'           has at most finite discontinuous points,
#'           and is L^2
#'
#' @references D. W. K. Andrews. Heteroskedasticity and Autocorrelation Consistent Covariance Matrix Estimation
#'
tukeyHanningKernel = function(x) {
    return(ifelse(abs(x) <= 1, (1 + cos(pi * x)) / 2, 0))
}

#'
#' @description construct complete from long-run correlation
#'
#' @param list.of.time.series a list of numeric vectors.
#'                            all vectors are assumed to have the same length
#'
#' @param B numeric. the band width. assumed to be nonzero
#'
#' @param kernelFunction function. the function used in Andrew's estimate
#'                       assumed to be even function and has value 1 at x = 0
#'                       default: quadraticSpectralKernel
#'
#' @param considerRange numeric, or NA. the maximal shift of the window, in units of B
#'                      refer to the description in longRunCorrelation
#'
#' @return igraph graph object of the graph constructed from the
#'         long-run correlation matrix
#'
#' @note wrapper of complete_network and longRunCorrelation
#'
longRunCorrelationNetwork = function(list.of.time.series, B, kernelFunction = quadraticSpectralKernel, considerRange = NA){
    return(complete_network(longRunCorrelation(list.of.time.series, B, kernelFunction, considerRange),
                            isDirected = FALSE,
                            isWeighted = TRUE))
}


#'
#' @description compute the network node dispersion (NND) via shortest paths
#'
#' @param g igraph::graph object. the graph in question
#'          assumed undirected connected
#'
#' @return a numeric representing the dispersion
#'
#' @references T. Schieber, L. Carpi, A. Diaz-Guilera.
#'             Quantification of Network Structural Dissimilarities
#'             doi: 10.1038/ncomms13928
#'
#' @note require infoTheoryLib::jensenShannonDivergence
#'
networkNodeDispersion = function(g) {
    n = vcount(g)
    diam = diameter(g)
    d = apply( # use table?
        distances(g),
        1,
        function(distVect) sapply(seq_len(diam), function(x) sum(distVect == x) / (n - 1)),
        simplify = FALSE
    )
    return(jensenShannonDivergence(d) / log2(1 + diam))
}

#'
#' @description compute the network dissimilarity proposed by T. Schieber et al.
#'
#' @param g1 igraph::graph object. the graph in question
#'           assumed undirected connected
#'
#' @param g2 igraph::graph object. the graph in question
#'           assumed undirected connected
#'           assumed to have same number of vertices as g1
#'
#' @param weightVect numeric vector containing 3 elements.
#'                   assume nonnegative and sums to 1
#'                   default: c(0.45, 0.45, 0.1)
#'
#' @return a numeric representing the dissimilarity
#'
#' @references T. Schieber, L. Carpi, A. Diaz-Guilera.
#'             Quantification of Network Structural Dissimilarities
#'             doi: 10.1038/ncomms13928
#'
#' @references https://github.com/tischieber/Quantifying-Network-Structural-Dissimilarities
#'
#' @note require infoTheoryLib::jensenShannonDivergence
#'
#' @note in the github code, during the computation of the last term,
#'           alpha-centrality is computed with exo = degree(g) / (N - 1) and alpha = 1 / N,
#'           which is then normalized by N^2, sorted and augmented
#'       the proceeding computation is also weird
#'       not sure why
#'       in this implementation, only use the same exo and alpha
#'
schieberNetworkDissimilarity = function(g1, g2, weightVect = c(0.45, 0.45, 0.1)) {
    res = 0
    # basic var
    diam1 = diameter(g1)
    diam2 = diameter(g2)
    n1 = vcount(g1)
    n2 = vcount(g2)
    # aux var
    distDistri1 = apply( # use table?
        distances(g1),
        1,
        function(distVect) sapply(seq_len(diam1), function(x) sum(distVect == x) / (n1 - 1)),
        simplify = FALSE
    )
    distDistri2 = apply( # use table?
        distances(g2),
        1,
        function(distVect) sapply(seq_len(diam2), function(x) sum(distVect == x) / (n2 - 1)),
        simplify = FALSE
    )
    totalDistDistri1 = Reduce('+', distDistri1, accumulate = FALSE)
    totalDistDistri2 = Reduce('+', distDistri2, accumulate = FALSE)
    alphaCentralityRoutine = function(g) alpha.centrality(g, exo = degree(g) / (vcount(g) - 1), alpha = 1 / vcount(g))
    # compute work
    if (weightVect[1] != 0) {
        res = weightVect[1] * sqrt(jensenShannonDivergence(list(totalDistDistri1, totalDistDistri2)))
    }
    if (weightVect[2] != 0) {
        res = res + weightVect[2] * abs(
            sqrt(jensenShannonDivergence(distDistri1) / log2(1 + diam1) * log2(exp(1))) -
                sqrt(jensenShannonDivergence(distDistri2) / log2(1 + diam2) * log2(exp(1)))
        )
    }
    if (weightVect[3] != 0) {
        res = res + weightVect[3] * (
            sqrt(
                jensenShannonDivergence(list(
                    alphaCentralityRoutine(g1),
                    alphaCentralityRoutine(g2)
                ))
            ) + sqrt(
                jensenShannonDivergence(list(
                    alphaCentralityRoutine(complementer(g1)),
                    alphaCentralityRoutine(complementer(g2))
                ))
            )
        ) / 2
    }
    return(res)
}

#'
#' @description
#'
#' @param list.of.matrix a list of matrices. a time series of vertices correlations
#'                       assumed all matrices have the same dimenion
#'
#' @param tau integer. the self-correlating period
#'            assume positive
#'
#' @param nPts integer. the number of cutoff threshold to choose from
#'             default: 1000
#'
#' @param doRandom boolean. determine if should use random points instead of equally spaced points
#'                 if TRUE, will use points from runif
#'                 if FALSE, will use equally spaces points
#'                 default: FALSE
#'
#' @return a named list containing:
#'             theta: the optimal theta
#'             networkList: a list of all (undirected unweighted) threshold networks
#'
#' @references X.-J. Xu, K. Wang, L. Zhu, L.-J. Zhang.
#'             Efficient Construction of Threshold Networks of Stock Markets
#'             doi: 10.1016/j.physa.2018.06.083
#'
#' @note require miscFuncLib::matrixCutOff
#'
optimalThresholdNetwork = function(list.of.matrix, tau, nPts = 1000, doRandom = FALSE) {
    thetaList = NULL
    if (doRandom) {
        thetaList = runif(nPts, -1, 1)
    } else {
        thetaList = (-((nPts - 1) / 2):((nPts - 1) / 2)) / (nPts - 1) * 2
    }
    totalTime = length(list.of.matrix)
    WSeries = sapply(
        seq_len(totalTime - tau),
        function(idx) Matrix::norm(list.of.matrix[[idx]] - list.of.matrix[[idx + tau]], '2')
    )
    optimalTheta = NULL
    optimalNetworkList = NULL
    optimalConsistentVal = -Inf
    for (thisTheta in thetaList) {
        thisNetworkList = lapply(list.of.matrix, function(m) complete_network(matrixCutOff(m, thisTheta, FALSE), isWeighted = FALSE))
        NSeries = sapply(
            seq_len(totalTime - tau),
            function(idx) schieberNetworkDissimilarity(thisNetworkList[[idx]], thisNetworkList[[idx + tau]])
        )
        thisConsistentVal = cor(WSeries, NSeries)
        if (thisConsistentVal > optimalConsistentVal) {
            optimalTheta = thisTheta
            optimalNetworkList = thisNetworkList
            optimalConsistentVal = thisConsistentVal
        }
    }
    return(list(
        theta = optimalTheta,
        networkList = optimalNetworkList
    ))
}
