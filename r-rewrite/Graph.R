# This file contains functions that are related to graphs
# Most functions depends on the igraph package
# Please goto the corresponding function definition for detail description.

if (!require(igraph)){
    stop("Graph.R requires the igraph package")
}

# preprocess - dependency registering
.LibImportTools.Global.Dependency = get0(".LibImportTools.Global.Dependency")

#'
#' @description determine if a graph is a tree
#'
#' @param g igraph graph object. the graph to be check
#'
#' @return boolean indicating if g is a tree
#'
#' @note this function is not optimized
#'
#' @note depends on igraph package
#'
Graph.isTree = function(g) {
    return(igraph::is_connected(g) && igraph::vcount(g) - 1 == igraph::ecount(g))
}

#'
#' @description determine if a graph is a forest (a collection of at least one tree)
#'
#' @param g igraph graph object. the graph to be check
#'
#' @return boolean indicating if g is a forest
#'
#' @note this function is not optimized
#'
#' @note depends on igraph package
#'
Graph.isForest = function(g) {
    return(all(sapply(
        igraph::decompose(g),
        function(subG) igraph::vcount(subG) - 1 == igraph::ecount(subG)
    )))
}


#'
#' @description find the Jordan center of a tree
#'
#' @param g.tree igraph graph object. Assumed tree
#'
#' @return vertex index of the center of the tree
#'
#' @references ?
#'
#' @note for weighted case,
#'           this implementation uses the naive algorithm (compare pairwise distance)
#'           basically brute force
#'
#' @note depends on igraph package
#'
Graph.treeCenter = function(g.tree) {
    if (igraph::is.weighted(g.tree)) {
        if (igraph::vcount(g.tree) <= 2) {
            return(1)
        }
        v2 = which.max(igraph::distances(g.tree, 1, weights = NA))
        v3 = which.max(igraph::distances(g.tree, v2, weights = NA))
        geodesicPath = unlist(igraph::shortest_paths(g.tree, v2, v3, weights = NA, output = 'vpath')$vpath)
        # TODO reduce number of shortest paths calculated
        return(geodesicPath[(length(geodesicPath) + 1) %/% 2])
    } else {
        return(which.min(apply(igraph::distances(g.tree), 1, max)))
    }
}

#'
#' @description get the tree layout with center as root
#'
#' @param g.tree igraph graph object. assumed to be a tree
#'
#' @return a two column matrix representing the coordinates of the nodes
#'         the layout is the same as igraph::layout_as_tree, except the root is the Jordan center
#'
#' @note the Jordan center is computed with identical edge weights if g.tree is unweighted
#'
#' @note depends on igraph package
#'
Graph.Layout.asRootCenteredTree = function(g.tree) {
    return(igraph::layout_as_tree(g.tree, root = Graph.treeCenter(g.tree)))
}

#'
#' @description plot a tree, or a forest
#'
#' @param g.forest igraph graph object. assumed to be a forest
#'
#' @param ... other argument passed to plot
#'
#' @return same as plot, which is NULL
#'
#' @note wrapper of plot function with layout overridden
#'
#' @note depends on igraph package
#'
Graph.Plot.tree = function(g.forest, ...) {
    if (!Graph.isForest(g.forest)) {
        stop("In plot_tree, the input graph is not a forest")
    }
    chosenLayoutFunc = igraph::layout_as_tree
    if (Graph.isTree(g.forest)) {
        chosenLayoutFunc = Graph.Layout.asRootCenteredTree
    }
    return(plot(
        g.forest,
        ...,
        layout = chosenLayoutFunc(g.forest)
    ))
}

#'
#' @description remove edges from the graph with cutoff threshold
#'
#' @param g igraph graph object. the graph to be cut.
#'          assumed to have edge attribute "weight"
#'
#' @param weight.threshold numeric. the weight threshold to cut edges
#'
#' @param to.remove.below boolean. determine if edges weight below the threshold should be removed.
#'                        if TRUE, edges weight above the threshold would be removed
#'                        if FALSE, edges weight above the threshold would be removed
#'
#' @param to.include.equal boolean. determine if edges weight equal the threshold would be removed
#'                         if TRUE, will also remove edges with same weight as threshold
#'                         if FALSE, edges with same weight as threshold will be kept
#'
#' @return igraph graph object. the graph with targeted edges removed
#'
#' @note depends on igraph package
#'
Graph.Transform.edgeCutOff = function(g, weight.threshold, to.remove.below, to.include.equal) {
    edgesToCutMask = NULL
    if (to.remove.below) {
        edgesToCutMask = (igraph::E(g)$weight < weight.threshold)
    } else {
        edgesToCutMask = (igraph::E(g)$weight > weight.threshold)
    }
    if (to.include.equal) {
        edgesToCutMask = edgesToCutMask | (igraph::E(g)$weight == weight.threshold)
    }
    return(igraph::delete_edges(g, igraph::E(g)[edgesToCutMask]))
}


#'
#' @description plot clustering result
#'
#' @param g igraph::graph object. the graph in question
#'
#' @param clustered.community igraph::communities object. how the graph is clustered
#'
#' @param ... all other parameters are passed to plot
#'
#' @return no return
#'
#' @note wrapper for plot
#'
Graph.Plot.clusterResult = function(g, clustered.community, ...) {
    igraph::plot(g, mark.groups = clustered.community, ...)
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
Graph.Plot.plotAfterClustering = function(g, clustering.func, ...) {
    clusterRes = clustering.func(g)
    Graph.Plot.clusterResult(g, clusterRes, ...)
    return(clusterRes)
}


#'
#' @description plot the overlapping communities on a graph
#'
#' @param g igraph graph object. assumed to be a undirected unweighted simple
#'
#' @param overlap.communities a numeric matrix representing the belonging coefficients,
#'                               or a list containing the modularity and the matrix
#'                           this input is passed directly to Graph.Clustering.Overlap.getCommunityInfo as belongingMatrix
#'
#' @param ... other argument passed to plot
#'
#' @return same as igraph::plot, which is NULL
#'
#' @note wrapper of igraph::plot function with mark.groups overridden
#'
Graph.Plot.overlapCommunity = function(g, overlap.communities, ...) {
    commInfo = Graph.Clustering.Overlap.getCommunityInfo(overlap.communities)
    commMembers = commInfo$communityMembers
    colorPal = rainbow(length(commMembers), alpha = NULL)
    overlapCount = length(commInfo$overlappedVertex)
    return(igraph::plot(g,
        mark.groups = commMembers,
        vertex.shape = if (overlapCount == 0) "circle" else "pie",
        vertex.pie = Graph.Clustering.Overlap.Transform.belongMatrixToVectList(commInfo$belongingMatrix),
        vertex.pie.color = list(colorPal),
        vertex.color = if (overlapCount == 0) colorPal[commInfo$vertexClass] else NULL,
        ...
    ))
}

#'
#' @description plot the overlapping communities on a graph directly with algorithms
#'
#' @param g igraph graph object. assumed to be a undirected unweighted simple
#'
#' @param overlap.community.clustering.method a function that takes a igraph graph object and return a numeric matrix
#'
#' @param ... other argument passed to algo
#'
#' @return the output of the clustering from algo
#'
#' @note wrapper of Graph.Plot.overlapCommunity
#'
Graph.Plot.overlapCommunityFromAlgo = function(g, overlap.community.clustering.method, ...){
    res = overlap.community.clustering.method(g, ...)
    Graph.Plot.overlapCommunity(g, res)
    return(res)
}


#'
#' @description compute the size of the component of a vertex
#'
#' @param g igraph graph object.
#'
#' @param target.vertex.id igraph vertex sequence. the id of the target vertex
#'
#' @return an integer vector representing the size of the component which vs belongs to
#'
Graph.getSubordinatedComponentSize = function(g, target.vertex.id){
    comp = igraph::components(g)
    return(comp$csize[comp$membership[target.vertex.id]])
}

#'
#' @description compute the vertices in the same component as the given vertex
#'
#' @param g igraph graph object.
#'
#' @param target.vertex.seq igraph vertex sequence. the ids of the target vertices
#'
#' @return a list of integer vectors representing the vertices which are in the same
#'             component
#'         if vs has only one vertex, returns the integer vector
#'
Graph.getSubordinatedComponentMembers = function(g, target.vertex.seq){
    comp = igraph::components(g)$membership
    return(sapply(target.vertex.seq, function(vid)which(comp == comp[vid]), simplify = "vector"))
}


#'
#' @description constructing the Planar Maximally Filtered Graph (PMFG)
#'
#' @param relation.matrix numeric matrix. defines relation between items.
#'                        assumed symmetric and has nonnegative entries
#'
#' @param enforce.library NULL, or one of the following string:
#'                            'MEGENA', 'RBGL', 'IMPLEMENTED'
#'                        affect which routine to use for planarity testing
#'                        'MEGENA':      MEGENA::planaritytest
#'                        'RBGL':        RBGL::boyerMyrvoldPlanarityTest (\~20 times slower than 'MEGENA')
#'                        'IMPLEMENTED': is_planar_graph_DMP implemented above (\~60 times slower than 'RBGL')
#'                        if NULL or not any of above, will use the first available in the list
#'                        default: NULL
#'
#' @param is.similar.matrix boolean
#'                          indicate if relation.matrix denote similarity (TRUE) or dissimilarity (FALSE)
#'                          default: TRUE
#'
#' @return igraph graph object of the PMFG constructed from the
#'         similarity matrix
#'
#' @references
#'
# TODO speed up
Graph.Characteristic.planarMaximallyFilteredGraph = function(relation.matrix, enforce.library = NULL, is.similar.matrix = TRUE) {
    supportLibList = c('MEGENA', 'RBGL', 'IMPLEMENTED')
    supportLibCheckAndRequire = c(
        quote(requireNamespace("MEGENA", quietly = TRUE)),
        quote(requireNamespace("RBGL", quietly = TRUE)),
        quote(if (file.exists("DMPLib.r")) {
            source("Graph.isPlanarGraphDMP.R", echo = FALSE); TRUE
        } else FALSE)
    )
    # process default
    if (is.null(enforce.library) || !(enforce.library %in% supportLibList)) {
        enforce.library = supportLibList[Position(eval,
            supportLibCheckAndRequire,
            nomatch = NULL
        )]
        if (length(enforce.library) == 0) {
            stop(paste(
                "No library available.",
                "Please check if the supported libraries are installed,",
                "or if Graph.isPlanarGraphDMP.R is in the same directory as this file"
            ))
        } else {
            warning(paste("Library", enforce.library, "automatically selected"))
        }
    } else {
        # san check user requested lib
        if (!eval(supportLibCheckAndRequire[[match(enforce.library, supportLibList)]])) {
            stop(paste("Request library", enforce.library, "is not available"))
        }
    }
    n = nrow(relation.matrix)
    planarity_test_routine = switch(enforce.library,
        MEGENA = function(g) {
            gEdgeList = as_edgelist(g, FALSE)
            return(MEGENA::planaritytest(n, gEdgeList[, 1], gEdgeList[, 2]))
        },
        RBGL = function(g) RBGL::boyerMyrvoldPlanarityTest(as_graphnel(g)),
        IMPLEMENTED = Graph.isPlanarGraphDMP,
        NULL
    )
    # refer from lower trig
    relation.matrix[upper.tri(relation.matrix, diag = TRUE)] = NA
    simOrdering = order(relation.matrix, decreasing = is.similar.matrix, na.last = NA)
    # remove edge with 0 weight
    simOrdering = simOrdering[relation.matrix[simOrdering] != 0]
    E = make_empty_graph(n, directed = FALSE)
    for (idx in simOrdering) {
        i = (idx - 1) %/% n + 1
        j = (idx - 1) %% n + 1 # i < j
        newE = add_edges(E, c(i, j), attr = c(weight = relation.matrix[idx]))
        if (planarity_test_routine(newE)) {
            E = newE
        }
    }
    return(E)
}



#'
#' @description constructing simplified network with Proportional Degree
#'              (PD) algorithm
#'
#' @param relation.matrix numeric matrix. defines relation between items.
#'                        assumed symmetric and has nonnegative entries
#'
#' @param output.edge.number NULL, or number of edges in the output graph.
#'                           if NULL, 3V-6 (number of edges in the PMFG) will be used
#'                           default: NULL
#'
#' @param is.similar.matrix boolean.
#'                          indicate if relation.matrix denote similarity (TRUE) or dissimilarity (FALSE)
#'                          default: TRUE
#'
#' @return igraph graph object of the network constructed from the
#'         similarity matrix with the PD algorithm
#'
#' @references
#'
Graph.Characteristic.proportionalDegreeNetwork = function(relation.matrix, output.edge.number = NULL, is.similar.matrix = TRUE){
    n = nrow(relation.matrix)
    sw = colSums(relation.matrix) - diag(relation.matrix)
    if (is.null(output.edge.number)){
        output.edge.number = 3 * n - 6
    }
    dPrime = sw / sum(sw) * output.edge.number * 2
    dPrimeCumSumRounded = round(cumsum(dPrime))
    d = rep(0, n)
    d[1] = dPrimeCumSumRounded[1]
    dCumSum = 0
    for (i in 2:n){ # vectorize?
        dCumSum = dCumSum + d[i - 1]
        d[i] = dPrimeCumSumRounded[i] - dCumSum
    }
    # refer to lower trig, write in upper trig
    relation.matrix[upper.tri(relation.matrix, diag = TRUE)] = NA
    simOrdering = order(relation.matrix, decreasing = is.similar.matrix, na.last = NA)
    for (idx in simOrdering){
        i = (idx - 1) %/% n + 1
        j = (idx - 1) %% n + 1  # i < j
        if (d[i] > 0 && d[j] > 0){
            relation.matrix[i, j] = relation.matrix[j, i]
            d[i] = d[i] - 1
            d[j] = d[j] - 1
        }
    }
    relation.matrix[is.na(relation.matrix)] = 0 # remove NA
    return(graph_from_adjacency_matrix(relation.matrix,
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
#' @param step.para numeric, or Inf. step parameter.
#'                  if numeric, 1/h is the step size
#'                  if Inf, edges are added one by one
#'
#' @param with.use.eigenvalue boolean.
#'                            determine if algebraic connectivity should be used to determined connectivity
#'                            default: FALSE
#'
#' @param with.use.normalized.laplacian boolean. determine if normalized Laplacian should be used
#'                                      ignored if with.use.eigenvalue is FALSE
#'                                      default: FALSE
#'
#' @param with.print.threshold.msg boolean. determine if the threshold should be printed out at the end
#'                                 if TRUE, the threshold will be printed
#'                                 default: TRUE
#'
#' @return igraph graph object. the threshold network
#'
#' @references M. A. Balci , O. Akguller, S. C. Guzel
#'             Hierarchies in communities of UK stock market from the perspective of Brexit
#'             doi: 10.1080/02664763.2020.1796942
#'
Graph.Characteristic.balciThresholdNetwork = function(g,
                                                      step.para,
                                                      with.use.eigenvalue = FALSE,
                                                      with.use.normalized.laplacian = TRUE,
                                                      with.print.threshold.msg = TRUE) {
    if (is.matrix(g)) {
        g = graph_from_adjacency_matrix(g, weighted = TRUE, mode = 'undirected')
    }
    emptyG = make_empty_graph(vcount(g), directed = FALSE)
    newG = emptyG
    edgeWeights = E(g)$weight
    if (is.null(edgeWeights)) {
        stop("input graph has no edge attribute called weight")
    }
    endpts = t(ends(g, E(g)))
    loopRoutine = is_connected
    if (with.use.eigenvalue) {
        loopRoutine = function(targetG) {
            tail(eigen(graph.laplacian(targetG,
                normalized = with.use.normalized.laplacian,
                weights = NA
            ),
            only.values = TRUE,
            symmetric = TRUE
            )$values, 2)[1] > .Machine$double.eps
        }
    }
    edgeOrderIdx = NULL
    if (is.infinite(step.para)) {
        edgeOrderIdx = order(edgeWeights, decreasing = F)
    }
    t = 0
    tau = NA
    while (!loopRoutine(newG)) {
        t = t + 1
        if (is.infinite(step.para)) {
            tau = edgeWeights[edgeOrderIdx[t]]
        } else {
            tau = t / step.para
        }
        # print(tau)
        edgeMask = (edgeWeights <= tau)
        newG = add_edges(emptyG,
            as.vector(endpts[, edgeMask]),
            weight = edgeWeights[edgeMask]
        )
    }
    if (with.print.threshold.msg) {
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
#' @param significance.cutoff numeric. the cutoff value
#'
#' @param weight.attr.name char. the name of edge attribute used
#'                         default: 'weight'
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
Graph.Characteristic.thresholdSignificanceGraph = function(g, significance.cutoff, weight.attr.name = 'weight') {
    if (!is.weighted(g)) {
        stop("Input graph is unweighted")
    }
    return(delete.edges(g, E(g)[edge_attr(g, weight.attr.name) <= significance.cutoff]))
}



#'
#' @description generate a network from the adjacency matrix
#'
#' @param relation.matrix numeric matrix. defines relation between items.
#'                        assumed symmetric and has nonnegative entries
#'
#' @param is.directed.matrix boolean. Determine if the graph should be directed
#'                           if FALSE, the matrix is first symmetrized
#'                           default: FALSE
#'
#' @param is.weighted.matrix boolean. Determine if the graph should be weighted
#'                           if FALSE, all nonzero entries (after symmetrized) will be taken as 1
#'                           default: TRUE
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
Graph.Characteristic.completeNetwork = function(relation.matrix, is.directed.matrix = FALSE, is.weighted.matrix = TRUE) {
    if (!is.directed.matrix) {
        relation.matrix = (relation.matrix + t(relation.matrix)) / 2
    }
    if (!is.weighted.matrix) {
        relation.matrix[relation.matrix != 0] = 1
    }
    return(graph_from_adjacency_matrix(relation.matrix,
        mode = (if (is.directed.matrix) "directed" else "undirected"),
        weighted = (if (is.weighted.matrix) TRUE else NULL),
        diag = FALSE
    ))
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
#' @note depends on MiscUtility.Statistics.longRunCorrMatrix
#'
Graph.Characteristic.longRunCorrNetwork = function(list.of.time.series,
                                                   band.width,
                                                   kernel.func = MiscUtility.Statistics.ParzenKernel.quadraticSpectral,
                                                   considered.range = NA) {
    return(Graph.Characteristic.completeNetwork(
        MiscUtility.Statistics.longRunCorrMatrix(
            list.of.time.series, band.width, kernel.func, considered.range
        ),
        is.directed.matrix = FALSE,
        is.weighted.matrix = TRUE
    ))
}
.LibImportTools.Global.Dependency = append(.LibImportTools.Global.Dependency, "MiscUtility")

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
#' @note depends on InfoTheory.Divergence.jensenShannonDivergence
#'
Graph.Metric.networkNodeDispersion = function(g) {
    n = vcount(g)
    diam = diameter(g)
    d = apply( # use table?
        distances(g),
        1,
        function(distVect) sapply(seq_len(diam), function(x) sum(distVect == x) / (n - 1)),
        simplify = FALSE
    )
    return(InfoTheory.Divergence.jensenShannonDivergence(d) / log2(1 + diam))
}
.LibImportTools.Global.Dependency = append(.LibImportTools.Global.Dependency, "InfoTheory")

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
#' @param weight.vect numeric vector containing 3 elements.
#'                    assume nonnegative and sums to 1
#'                    default: c(0.45, 0.45, 0.1)
#'
#' @return a numeric representing the dissimilarity
#'
#' @references T. Schieber, L. Carpi, A. Diaz-Guilera.
#'             Quantification of Network Structural Dissimilarities
#'             doi: 10.1038/ncomms13928
#'
#' @references https://github.com/tischieber/Quantifying-Network-Structural-Dissimilarities
#'
#' @note depends on InfoTheory.Divergence.jensenShannonDivergence
#'
#' @note in the github code, during the computation of the last term,
#'           alpha-centrality is computed with exo = degree(g) / (N - 1) and alpha = 1 / N,
#'           which is then normalized by N^2, sorted and augmented
#'       the proceeding computation is also weird
#'       not sure why
#'       in this implementation, only use the same exo and alpha
#'
Graph.Metric.schieberNetworkDissimilarity = function(g1, g2, weight.vect = c(0.45, 0.45, 0.1)) {
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
    if (weight.vect[1] != 0) {
        res = weight.vect[1] * sqrt(InfoTheory.Divergence.jensenShannonDivergence(list(totalDistDistri1, totalDistDistri2)))
    }
    if (weight.vect[2] != 0) {
        res = res + weight.vect[2] * abs(
            sqrt(InfoTheory.Divergence.jensenShannonDivergence(distDistri1) / log2(1 + diam1) * log2(exp(1))) -
                sqrt(InfoTheory.Divergence.jensenShannonDivergence(distDistri2) / log2(1 + diam2) * log2(exp(1)))
        )
    }
    if (weight.vect[3] != 0) {
        res = res + weight.vect[3] * (
            sqrt(
                InfoTheory.Divergence.jensenShannonDivergence(list(
                    alphaCentralityRoutine(g1),
                    alphaCentralityRoutine(g2)
                ))
            ) + sqrt(
                InfoTheory.Divergence.jensenShannonDivergence(list(
                    alphaCentralityRoutine(complementer(g1)),
                    alphaCentralityRoutine(complementer(g2))
                ))
            )
        ) / 2
    }
    return(res)
}
.LibImportTools.Global.Dependency = append(.LibImportTools.Global.Dependency, "InfoTheory")

#'
#' @description find the optimal value for cutting threshold network
#'
#' @param list.of.matrix.series a list of matrices. a time series of vertices correlations
#'                              assumed all matrices have the same dimenion
#'
#' @param sample.pt.number integer. the number of cutoff threshold to choose from
#'                         default: 1000
#'
#' @param with.random.sample boolean. determine if should use random points instead of equally spaced points
#'                           if TRUE, will use points from runif
#'                           if FALSE, will use equally spaces points
#'                           default: FALSE
#'
#' @return a named list containing:
#'             theta: the optimal theta
#'             networkList: a list of all (undirected unweighted) threshold networks
#'
#' @references X.-J. Xu, K. Wang, L. Zhu, L.-J. Zhang.
#'             Efficient Construction of Threshold Networks of Stock Markets
#'             doi: 10.1016/j.physa.2018.06.083
#'
#' @note depends on MiscUtility.Transform.matrixCutOff
#'
Graph.Characteristic.optimalThresholdNetwork = function(list.of.matrix.series, sample.pt.number = 1000, with.random.sample = FALSE) {
    thetaList = NULL
    if (with.random.sample) {
        thetaList = runif(sample.pt.number, -1, 1)
    } else {
        thetaList = (-((sample.pt.number - 1) / 2):((sample.pt.number - 1) / 2)) / (sample.pt.number - 1) * 2
    }
    totalTime = length(list.of.matrix.series)
    WSeries = sapply(
        seq_len(totalTime - 1),
        function(idx) Matrix::norm(list.of.matrix.series[[idx]] - list.of.matrix.series[[idx + 1]], '2')
    )
    optimalTheta = NULL
    optimalNetworkList = NULL
    optimalConsistentVal = -Inf
    for (thisTheta in thetaList) {
        thisNetworkList = lapply(
            list.of.matrix.series,
            function(m) Graph.Characteristic.completeNetwork(MiscUtility.Transform.matrixCutOff(m, thisTheta, FALSE),
                is.weighted.matrix = FALSE
            )
        )
        NSeries = sapply(
            seq_len(totalTime - 1),
            function(idx) Graph.Metric.schieberNetworkDissimilarity(
                thisNetworkList[[idx]],
                thisNetworkList[[idx + 1]]
            )
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
.LibImportTools.Global.Dependency = append(.LibImportTools.Global.Dependency, "MiscUtility")
