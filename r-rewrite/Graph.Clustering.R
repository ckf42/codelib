# This file contains functions that are related to graphs
# Most functions depends on the igraph package
# Please goto the corresponding function definition for detail description.

if (!require(igraph)){
    stop("GraphLib.R requires the igraph package")
}

Graph.Clustering.Dependency = c(
    "Graph"
)

#'
#' @description finding clusters of a graph with Normalized Spectral
#'              Clustering (NSC)
#'
#' @param similarity.matrix numeric matrix. similarity between items.
#'                          assumed symmetric and has nonnegative entries
#'
#' @param cluster.number integer. target number of clusters
#'
#' @return a list of num_cluster integer vectors. each vector records the node
#'         indices that belongs to that cluster
#'
#' @note the entries of the input matrix are treated as similarity
#'
#' @references http://fourier.eng.hmc.edu/e161/lectures/algebra/node7.html
#'
Graph.Clustering.Algo.normalizedSpectralClusteringOnMatrix = function(similarity.matrix, cluster.number) {
    n = nrow(similarity.matrix)
    d = colSums(similarity.matrix)
    L = diag(d) - similarity.matrix
    # solve generalized eigenproblem L * v = lambda * diag(d) * v
    #     and extract num_cluster eigenvect with smallest eigenval
    # this approach is from
    #     http://fourier.eng.hmc.edu/e161/lectures/algebra/node7.html
    # ? use library / faster approach?
    V = eigen(L / outer(d, d), symmetric = TRUE)$vectors[, n:(n + 1 - cluster.number)] / sqrt(d)
    clusterIndices = kmeans(V, cluster.number)$cluster
    return(lapply(seq_len(cluster.number), function(idx) which(clusterIndices == idx)))
}

#'
#' @description finding clusters of a graph with Normalized Spectral
#'              Clustering (NSC)
#'
#' @param g igraph graph object. the graph to be cluster
#'
#' @param cluster.number integer. number of clusters
#'
#' @param is.weighted.graph boolean. determine if the graph input should be seen as weighted
#'                          if FALSE, edge weights in g will be ignored (or equivalently unit weight)
#'                          if TRUE, edge weights will be used as vertex similarities
#'                          default: FALSE
#'
#' @return igraph::communities object with membership and modularity.
#'         the modularity is computed as g is weighted
#'
#' @note the weights of the edges are treated as similarity
#'
#' @note wrapper of normalized_spectral_clustering
#'
Graph.Clustering.Algo.normalizedSpectralClustering = function(g, cluster.number, is.weighted.graph = FALSE) {
    if (!is.weighted.graph && !is.null(E(g)$weight)) {
        g = igraph::delete_edge_attr(g, 'weight')
    }
    simMatrix = igraph::as_adjacency_matrix(g, sparse = FALSE)
    diag(simMatrix) = 1
    listOfClusters = Graph.Clustering.normalizedSpectralClusteringOnMatrix(simMatrix, cluster.number)
    n = igraph::vcount(g)
    clusterIndices = rep(NA, n)
    for (i in seq_along(listOfClusters)) {
        clusterIndices[listOfClusters[[i]]] = i
    }
    return(igraph::make_clusters(g,
        clusterIndices,
        modularity = igraph::modularity(g, clusterIndices, weights = E(g)$weight)
    ))
}

#'
#' @description convert membership vector to list of clusters
#'
#' @param membership.vect integer vector.
#'                        denote id of cluster an element belongs to
#'
#' @param vect.of.entry.name NULL, or character vector. the names corresponding to the indices
#'                           if NULL, will keep as integers
#'                           default: NULL
#'
#' @return a list of integer vectors. each vector is a cluster and records the indices of its members
#'         if namesOfIdx is not NULL, the vectors will be converted into characters according to it
#'
Graph.Clustering.Transform.membershipVectToCommunityList = function(membership.vect, vect.of.entry.name = NULL){
    listOfComm = lapply(unique(membership.vect),
                        function(idx)which(membership.vect == idx))
    if (!is.null(vect.of.entry.name)){
        listOfComm = lapply(listOfComm, function(indVect)vect.of.entry.name[indVect])
    }
    return(listOfComm)
}


#'
#' @description transform list of communities to membership vector
#'
#' @param list.of.communities list of integer vectors.
#'                            assumed a partition of 1:max(unlist(commList))
#'                            (no overlapping, each integer appears exactly once)
#'
#' @return a integer vector of length max(unlist(commList)) denoting the community index
#'
Graph.Clustering.Transform.communityListToMembershipVect = function(list.of.communities){
    membershipVect = rep(NULL, max(sapply(list.of.communities, max)))
    for (commIdx in seq_along(list.of.communities)){
        membershipVect[list.of.communities[[commIdx]]] = commIdx
    }
    return(membershipVect)
}

#'
#' @description transform clustering items to list of clusters
#'
#' @param clustering igraph::communities object, integer vector, or list of integer vectors
#'                   the clustering object to be transform
#'
#' @return list of integer vectors representing the communities
#'
Graph.Clustering.Transform.clusteringResultToCommunityList = function(clustering){
    if (class(clustering) == 'communities'){
        clustering = clustering$membership
    }
    if (is.vector(clustering)){
        clustering = Graph.Clustering.Transform.membershipVectToCommunityList(clustering)
    }
    return(clustering)
}


#'
#' @description compute the Adjusted Rand Index (ARI) between two clusterings
#'
#' @param clustering1 a list of integer vectors, or a integer vector
#'                    if it is a list of vectors, each vector contains the
#'                        indices of items in a cluster.
#'                    The vectors partition {1, ..., n} where n is the number of items
#'                    if it is a integer vector, it denotes the index of the cluster
#'                        the item belongs to
#'
#' @param clustering2 a list of integer vectors, or a integer vector
#'                    if it is a list of vectors, each vector contains the
#'                        indices of items in a cluster.
#'                    The vectors partition {1, ..., n} where n is the number of items
#'                    if it is a integer vector, it denotes the index of the cluster
#'                        the item belongs to
#'
#' @return a numeric representing the ARI between the two clusterings
#'
Graph.Clustering.Metric.adjustedRandIndex = function(clustering1, clustering2){
    clustering1 = Graph.Clustering.Transform.clusteringResultToCommunityList(clustering1)
    clustering2 = Graph.Clustering.Transform.clusteringResultToCommunityList(clustering2)
    sumAi = sapply(clustering1, length)
    nC2 = choose(sum(sumAi), 2)
    sumAi = sum(choose(sumAi, 2))
    sumBi = sum(choose(sapply(clustering2, length), 2))
    nij = outer(seq_along(clustering1),
                seq_along(clustering2),
                Vectorize(function(idx1, idx2)
                    length(intersect(clustering1[[idx1]],
                                     clustering2[[idx2]]))))
    denom = (sumAi + sumBi) / 2 - (sumAi * sumBi) / nC2
    if (denom == 0){
        return(1)
    } else {
        return((sum(choose(nij, 2)) - (sumAi * sumBi) / nC2) / denom)
    }
}


#'
#' @description compute the NMI similarity between two clusterings
#'
#' @param clustering1 a list of integer vectors, or a integer vector
#'                    if it is a list of vectors, each vector contains the
#'                        indices of items in a cluster.
#'                    The vectors partition {1, ..., n} where n is the number of items
#'                    if it is a integer vector, it denotes the index of the cluster
#'                        the item belongs to
#'
#' @param clustering2 a list of integer vectors, or a integer vector
#'                    if it is a list of vectors, each vector contains the
#'                        indices of items in a cluster.
#'                    The vectors partition {1, ..., n} where n is the number of items
#'                    if it is a integer vector, it denotes the index of the cluster
#'                        the item belongs to
#'
#' @param to.use.max.entropy boolean. determine if max entropy should be used to normalize
#'                           by default the normalization routine is the arithmetic mean
#'                           default: FALSE
#'
#' @return a numeric representing the similarity of the two clusterings
#'
Graph.Clustering.Metric.clusterNMISimilarity = function(clustering1, clustering2, to.use.max.entropy = FALSE){
    clustering1 = Graph.Clustering.Transform.clusteringResultToCommunityList(clustering1)
    clustering2 = Graph.Clustering.Transform.clusteringResultToCommunityList(clustering2)
    n1 = sapply(clustering1, length)
    n2 = sapply(clustering2, length)
    n = sum(n1)
    nij = outer(seq_along(clustering1),
                seq_along(clustering2),
                Vectorize(function(idx1, idx2)
                    length(intersect(clustering1[[idx1]],
                                     clustering2[[idx2]]))))
    nProd = outer(n1, n2)
    return(sum(ifelse(nij == 0, 0, nij * log2(n * nij / nProd))) /
               (if(to.use.max.entropy) max else mean)(c(sum(n1 * log2(n / n1)), sum(n2 * log2(n / n2)))))
}


#'
#' @description find the maximal cliques of size at least 3 of a graph
#'
#' @param g igraph graph object. the graph to find cliques in
#'
#' @return a list of vectors, each of which is a maximal clique of size at
#'         least 3 and records the vertex indices
#'
#' @note wrapper of igraph::max_cliques with min = 3
#'
Graph.Clustering.Clique.getMaxCliques = function(g){
    return(igraph::max_cliques(g, min = 3))
}

#'
#' @description filter out cliques of certain sizes
#'
#' @param list.of.clique list of integer vectors.
#'                       each vector shoule be a clique and records the indices of the vertices
#'
#' @param vect.of.allowed.size integer vector. the size of cliques that are kept
#'
#' @return a list of integer vectors.
#'         same as list.of.clique, but vectors of size not in vect.of.allowed.size is removed
#'
Graph.Clustering.Clique.filterBySize = function(list.of.clique, vect.of.allowed.size){
    return(Filter(function(vertexVect)length(vertexVect) %in% vect.of.allowed.size, list.of.clique))
}

#'
#' @description compute the ratio of cliques with the same tag
#'
#' @param list.of.clique a list of intege vectors.
#'                       each vector should be a clique and records the indices
#'                           of vertices in this clique
#'
#' @param vect.of.vertex.tags a integet vector representing the tags.
#'                            the tag of vertex i should be encoded in vertexTags[i]
#'
#' @return a numeric between 0 and 1 representing the ratio of cliques that
#'             have the same tags on the vertices
#'
#' @references S. S. Hosseini, N. Wormald, T. Tian
#'             A Weight-based Information Filtration Algorithm for Stock-Correlation Networks
#'
Graph.Clustering.Metric.cliqueHomogeneity = function(list.of.clique, vect.of.vertex.tags){
    isHomogen = sapply(list.of.clique,
                       function(vertexVect)length(unique(vect.of.vertex.tags[vertexVect])) == 1)
    return(sum(isHomogen) / length(isHomogen))
}


#'
#' @description compute the NOVER score for the edges
#'
#' @param g igraph graph object. the graph to compute NOVER on
#'
#' @param target.edges igraph edge sequence. the edges to compute NOVER score
#'                     default: E(g)
#'
#' @return a numeric vector. the NOVER score of the edges in target.edges
#'
Graph.Clustering.Measure.noverScore = function(g, target.edges = igraph::E(g)){
    adjMatrix = igraph::as_adjacency_matrix(g)
    igraph::V(g)$name = seq_len(igraph::vcount(g))
    edgeEndPt = igraph::ends(g, target.edges)
    .NOVERScore_internal = function(eidx){
        u = as.integer(edgeEndPt[eidx, 1])
        v = as.integer(edgeEndPt[eidx, 2])
        uni = sum(adjMatrix[u, ] | adjMatrix[v, ]) - 2
        if (uni == 0){
            return(0)
        } else {
            return(sum(adjMatrix[u, ] & adjMatrix[v, ]) / uni)
        }
    }
    return(sapply(seq_along(target.edges), .NOVERScore_internal))
}

#' @note This function implements the "Single-link k-clustering algorithm using NOVER"
#'           as presented in the project by K. Kulkarni (with some modifications)
#'       The algorithm works as the following:
#'       1. the NOVER (neighborhood overlap) score of each edge is computed
#'       2. Construct a MST using the NOVER score
#'       3. Remove k edges with highest edge betweenness from the MST. The connected components give a partition
#'       4. Repeat step 3 for a fixed number of times with different k
#'       5. Report the partition with highest modularity score
#'       In the Github implementation, the patience is set as 20 without further explaination
#'
#' @description clustering on a graph with NOVER score
#'
#' @param g igraph graph object. the graph to cluster on
#'
#' @param trial.cut.test.time integer, or Inf. the maximal number of trial cuts
#'                            capped at the number of vertices of g
#'                            default: Inf
#'
#' @param to.use.min.span.tree boolean. determine if Minimal Spanning Tree should be used instead of Maximal Spanning Tree
#'                             default: FALSE
#'
#' @return igraph::communities object with membership and modularity.
#'         the modularity is computed as g is unweighted
#'
#' @references K. Kulkarni.
#'             Community Detection in Social Network
#'             doi: 10.31979/etd.hn5z-3hp9
#'
#' @references https://github.com/ketkik22/Community-detection-on-social-network/blob/master/CommunityDetectionUsingKruskalsAlgorithm.py
#'
Graph.Clustering.Algo.noverSingleLinkClustering = function(g, trial.cut.test.time = Inf, to.use.min.span.tree = FALSE) {
    # compute NOVER score for all edges
    adjMatrix = igraph::as_adjacency_matrix(g)
    edgeEndPt = igraph::ends(g, igraph::E(g))
    NOVERScore = function(eidx) {
        u = edgeEndPt[eidx, 1]
        v = edgeEndPt[eidx, 2]
        uni = sum(adjMatrix[u, ] | adjMatrix[v, ]) - 2
        if (uni == 0) {
            return(0)
        } else {
            return(sum(adjMatrix[u, ] & adjMatrix[v, ]) / uni)
        }
    }
    # WeightScore = function(eidx){
    #     u = edgeEndPt[eidx, 1]
    #     v = edgeEndPt[eidx, 2]
    #     return(sum(adjMatrix[u, ]) + sum(adjMatrix[v, ]))
    # }
    NOVERMST = igraph::mst(g, (if (to.use.min.span.tree) 1 else -1) * sapply(E(g), NOVERScore))
    edgeOrder = order(igraph::edge_betweenness(NOVERMST), decreasing = TRUE)
    numOfEdgeToRemove = sample.int(igraph::ecount(NOVERMST) + 1, min(igraph::ecount(NOVERMST) + 1, trial.cut.test.time)) - 1
    maxQ = -Inf
    maxMembership = NULL
    for (k in numOfEdgeToRemove) {
        cutMST = igraph::delete_edges(NOVERMST, edgeOrder[seq_len(k)])
        thisMembership = igraph::components(cutMST)$membership
        thisQ = igraph::modularity(g, thisMembership)
        if (thisQ > maxQ) {
            maxQ = thisQ
            maxMembership = thisMembership
        }
    }
    return(igraph::make_clusters(g, maxMembership, modularity = maxQ))
}


#' @note This function implements the "ACUEB ... with a meta network"
#'           as presented in the project by K. Kulkarni (with some modifications)
#'       The algorithm works as the following:
#'       1. Create a graph, g', with the same number of vertices and no edge
#'       2. Compute the edge betweenness of every edge in g
#'       3. Add the edges in g with minimal edge betweenness not added to g'. The connected components give a partition
#'       4. Contract vertices in the same connected components of g' in g (to build a meta network)
#'       5. Restart from step 2 until there is no edge left or run out of patience
#'       6. Report the partition with highest modularity score
#'       In the Github implementation, the patience is set as 40 without further explaination
#'       The value is 20 with the "one edge at a time" mode,
#'           but is set to 30 once a higher modularity than the current one is found
#'
#' @description Find communities with ACUEB without meta network
#'
#' @param g igraph graph object. the graph to cluster on
#'
#' @param patience integer, or Inf. The maximal number of continuous failure allowed
#'                 default: Inf
#'
#' @param to.one.edge.at.a.time boolean. determine if only one edge should be add at a step
#'                              default: TRUE
#'
#' @return igraph::communities object with membership and modularity.
#'         the modularity is computed as if g is unweighted
#'
#' @references K. Kulkarni.
#'             Community Detection in Social Networks
#'             doi: 10.31979/etd.hn5z-3hp9
#'
#' @references https://github.com/ketkik22/Community-detection-on-social-network/blob/master/ModifiedLouvainAlgorithm.py
#'
#' @references https://github.com/ketkik22/Community-detection-on-social-network/blob/master/ModifiedLouvainAlgorithmWithOneEdgeAtATime.py
#'
Graph.Clustering.Algo.acuebClusteringWithMetaNetwork = function(g, patience = Inf, to.one.edge.at.a.time = TRUE) {
    if (is.null(igraph::E(g)$weight)) {
        igraph::E(g)$weight = 1
    }
    n = igraph::vcount(g)
    gOrigin = g
    gPrime = igraph::make_empty_graph(n, directed = FALSE)
    maxMembership = seq_len(n)
    maxQ = 0
    patienceCounter = patience
    metaGrouping = seq_len(n)
    #'
    #' @param metaEdgeHead integer. one end of the target edge in meta graph
    #' @param metaEdgeTail integer. the other end of the target edge in meta graph
    #' @metaGroupIdx integer vector. The meta vertex ids of the vertices
    #  @return a integer representing the edge id in gOrigin
    #'
    .getOrigEdgeIdFromMeta = function(metaEdgeHead, metaEdgeTail, metaGroupIdx) {
        vGroup = which(metaGroupIdx == metaEdgeHead)
        uGroup = which(metaGroupIdx == metaEdgeTail)
        vuCombn = expand.grid(vGroup, uGroup)
        for (idx in seq_len(nrow(vuCombn))) {
            origEdgeId = get.edge.ids(gOrigin, vuCombn[idx, ])
            if (origEdgeId != 0) {
                return(origEdgeId)
            }
        }
        stop("In Graph.Clustering.Algo.acuebClusteringWithMetaNetwork::.getOrigEdgeIdFromMeta, target edge not found")
    }
    while (patienceCounter > 0 && igraph::ecount(g) > 0) {
        ebList = igraph::edge_betweenness(g)
        minEBEdgeIdx = NULL
        if (to.one.edge.at.a.time) {
            minEBEdgeIdx = which.min(ebList)
        } else {
            minEBEdgeIdx = which(ebList == min(ebList))
        }
        # get edge id on gOrigin from edge id on g (meta)
        origEdgeIdx = sapply(
            minEBEdgeIdx,
            function(edgeIdx) .getOrigEdgeIdFromMeta(
                igraph::head_of(g, edgeIdx),
                igraph::tail_of(g, edgeIdx),
                metaGrouping
            )
        )
        # contract vertices
        gPrime = igraph::add_edges(
            gPrime,
            as.vector(rbind(
                igraph::head_of(gOrigin, origEdgeIdx),
                igraph::tail_of(gOrigin, origEdgeIdx)
            ))
        )
        thisMembership = igraph::components(gPrime)$membership
        thisQ = igraph::modularity(gOrigin, thisMembership)
        metaGrouping = thisMembership
        g = igraph::contract(gOrigin, metaGrouping, vertex.attr.comb = 'min')
        g = igraph::simplify(g, edge.attr.comb = 'min') # remove mult-edge, self-loop
        # update maximal
        if (thisQ > maxQ) {
            patienceCounter = patience
            maxQ = thisQ
            maxMembership = thisMembership
        } else {
            patienceCounter = patienceCounter - 1
        }
    }
    return(igraph::make_clusters(g, maxMembership, modularity = maxQ))
}


#'
#' @note This function implements the "ACUEB ... without a meta network"
#'           as presented in the project by K. Kulkarni (with some modifications)
#'       The algorithm works as the following:
#'       1. Compute the edge betweenness of every edge
#'       2. Create a graph with the same number of vertices and no edge
#'       3. Add the edges with minimal edge betweenness not added to the new graph. The connected components give a partition
#'       4. Repeat step 3 until there is no edge left or run out of patience
#'       5. Report the partition with highest modularity score
#'       In the Github implementation, the patience is set as 50 without further explaination
#'
#' @description Find communities with ACUEB without meta network
#'
#' @param g igraph graph object. the graph to cluster on
#'
#' @param patience integer, or Inf. The maximal number of continuous failure allowed
#'                 default: Inf
#'
#' @return igraph::communities object with membership and modularity.
#'         the modularity is computed as if g is unweighted
#'
#' @references K. Kulkarni.
#'             Community Detection in Social Networks
#'             doi: 10.31979/etd.hn5z-3hp9
#'
#' @references https://github.com/ketkik22/Community-detection-on-social-network/blob/master/ModifiesLouvainAlgorithmWithoutMetaNetwork.py
#'
Graph.Clustering.Algo.acuebClusteringWithoutMetaNetwork = function(g, patience = Inf){
    n = igraph::vcount(g)
    if (is.null(igraph::E(g)$weight)){
        igraph::E(g)$weight = 1
    }
    edgeEndPt = igraph::ends(g, igraph::E(g))
    ebList = igraph::edge_betweenness(g)
    ebOrder = order(ebList)
    ebSPtr = 1
    patienceCounter = patience
    maxMembership = igraph::components(g)$membership
    maxQ = igraph::modularity(g, maxMembership)
    gPrime = igraph::make_empty_graph(n, directed = FALSE)
    while (patienceCounter > 0 && ebSPtr <= length(ebList)){
        ebEPtr = ebSPtr + 1
        while (ebEPtr <= length(ebList) && ebList[ebOrder[ebSPtr]] == ebList[ebOrder[ebEPtr]]){
            ebEPtr = ebEPtr + 1
        } # range [ebSPtr, ebEptr)
        gPrime = igraph::add_edges(gPrime,
                           as.vector(t(edgeEndPt[ebOrder[ebSPtr:(ebEPtr - 1)], ])))
        ebSPtr = ebEPtr
        thisMembership = igraph::components(gPrime)$membership
        thisQ = igraph::modularity(g, thisMembership)
        if (thisQ > maxQ){
            maxQ = thisQ
            maxMembership = thisMembership
            patienceCounter = patience
        } else {
            patienceCounter = patienceCounter - 1
        }
    }
    return(igraph::make_clusters(g, maxMembership, modularity = maxQ))
}

#'
#' @note This function implements the "Neighborhood Overlap-Based Community Detection Algorithm"
#'           as presented in the paper by N. Meghanathan (with some modifications)
#'       The algorithm works as the following:
#'       1. the NOVER (neighborhood overlap) score of each edge is computed
#'       2. Remove the edge with minimal NOVER score. The connected components give a partition
#'       3. Repeat step 2 until there is no edge left
#'       4. Report the partition with highest modularity score
#'
#' @description clustering on a graph with NOVER score
#'
#' @param g igraph graph object. the graph to cluster on
#'
#' @return igraph::communities object with membership and modularity.
#'         the modularity is computed as g is unweighted
#'
#' @references N. Meghanathan
#'             A Greedy Algorithm for Neighborhood Overlap-Based Community Detection
#'
Graph.Clustering.Algo.greedyNOVERClustering = function(g) {
    # compute NOVER score for all edges
    adjMatrix = igraph::as_adjacency_matrix(g)
    igraph::V(g)$name = seq_len(igraph::vcount(g))
    edgeEndPt = igraph::ends(g, igraph::E(g))
    .NOVERList = sapply(E(g), function(eidx) {
        u = as.integer(edgeEndPt[eidx, 1])
        v = as.integer(edgeEndPt[eidx, 2])
        uni = sum(adjMatrix[u, ] | adjMatrix[v, ]) - 2
        if (uni == 0) {
            return(0)
        } else {
            return(sum(adjMatrix[u, ] & adjMatrix[v, ]) / uni)
        }
    })
    NOVEROrder = order(.NOVERList)
    maxMembership = igraph::components(g)$membership
    lastMembership = maxMembership
    maxQ = igraph::modularity(g, maxMembership)
    gCut = g
    for (edgeToCut in seq_len(nrow(edgeEndPt))) {
        gCut = gCut - igraph::E(gCut)[igraph::get.edge.ids(gCut, edgeEndPt[NOVEROrder[edgeToCut], ])]
        thisMembership = igraph::components(gCut)$membership
        if (any(lastMembership != thisMembership)) {
            lastMembership = thisMembership
            thisQ = igraph::modularity(g, thisMembership)
            if (thisQ > maxQ) {
                maxQ = thisQ
                maxMembership = thisMembership
            }
        }
    }
    names(maxMembership) = NULL
    return(igraph::make_clusters(g, maxMembership, modularity = maxQ))
}


#'
#' @note This function implements the maximal split clustering algorithm as presented
#'           in the paper by M. Maravalle, B Simeone and R. Naldini (with some modifications)
#'       The algorithm works as the following:
#'       1. Compute all pairwise distances between vertices and sort them in increasing order
#'       2. Set r = 1
#'       3. For each minimal distance path, label all unlabeled edges within by r and increase r by 1
#'       4. Remove p - 1 edges with maximal labels. The components give a partition
#'       It is proven in the paper that this partition should maximalize split (minimal inter-
#'           cluster distance) among all partitions into p clusters (rather than the modularity)
#'
#' @description find the partition that give maximal split on a tree
#'
#' @param g.tree igraph graph object. assumed to be a tree
#'
#' @param target.cluster.number integer. the number of clusters to return. assumed 1 <= p <= |V|
#'
#' @param to.compute.modularity boolean. determine if modularity should be computed
#'                              default: TRUE
#'
#' @return igraph::communities object with membership and modularity.
#'         the modularity is computed as g is unweighted
#'         if computeMod is FALSE, the modularity returned is 0
#'
#' @references M. Maravalle, B Simeone, R. Naldini.
#'             Clustering on trees
#'
Graph.Clustering.Algo.maximalTreeSplit = function(g.tree, target.cluster.number, to.compute.modularity = TRUE) {
    if (target.cluster.number == 1) {
        maxMembership = igraph::components(g.tree)$membership
        return(igraph::make_clusters(g.tree,
            maxMembership,
            modularity = if (to.compute.modularity) 0 else igraph::modularity(g.tree, maxMembership)
        ))
    }
    N = igraph::vcount(g.tree)
    pairwiseDist = igraph::distances(g.tree)
    pairwiseDist[upper.tri(pairwiseDist, diag = TRUE)] = NA
    edgeOrdering = order(pairwiseDist, na.last = NA)
    E(g.tree)$label = rep(NA, ecount(g.tree))
    r = 1
    for (idxPair in edgeOrdering) {
        pathEdgeIds = igraph::shortest_paths(g.tree,
            (idxPair - 1) %/% N + 1,
            (idxPair - 1) %% N + 1,
            output = 'epath'
        )$epath[[1]]
        writeMask = is.na(E(g.tree)$label[pathEdgeIds])
        if (sum(writeMask)) {
            igraph::E(g.tree)$label[pathEdgeIds[writeMask]] = r
            r = r + 1
        }
        if (all(!is.na(E(g.tree)$label))) {
            break()
        }
    }
    edgeIdToCut = order(igraph::E(g.tree)$label, decreasing = T)[seq_len(target.cluster.number - 1)]
    thisMembership = igraph::components(g.tree - igraph::E(g.tree)[edgeIdToCut])$membership
    return(igraph::make_clusters(g.tree, thisMembership,
        modularity = if (to.compute.modularity) 0 else igraph::modularity(g.tree, thisMembership)
    ))
}


#'
#' @description clustering graph with maximal split clustering on mst
#'
#' @param g igraph graph object. the graph to cluster on
#'
#' @param weight.attr.name character. the name of the edge attribute used to build MST
#'                         used as distance, so large weight means further distance
#'                         default: 'weight'
#'
#' @return igraph::communities object with membership and modularity.
#'         the modularity is computed as g is unweighted
#'
#' @note This function is a simple modification of maximal_split_on_tree:
#'       It finds the mst of g according to the edge attribute weightAttr
#'       It then enumerates maximal_split_on_tree on all possible p and reports the one
#'           with highest modularity on g
#'
Graph.Clustering.Algo.maximalMSTSplitClustering = function(g, weight.attr.name = 'weight') {
    gTree = igraph::mst(g, igraph::get.edge.attribute(g, weight.attr.name))
    maxMembership = igraph::components(gTree)$membership
    maxQ = igraph::modularity(gTree, maxMembership)
    N = igraph::vcount(gTree)
    pairwiseDist = igraph::distances(gTree)
    pairwiseDist[upper.tri(pairwiseDist, diag = TRUE)] = NA
    edgeOrdering = order(pairwiseDist, na.last = NA)
    igraph::E(gTree)$label = rep(NA, ecount(gTree))
    r = 1
    for (idxPair in edgeOrdering) {
        pathEdgeIds = igraph::shortest_paths(gTree,
            (idxPair - 1) %/% N + 1,
            (idxPair - 1) %% N + 1,
            output = 'epath'
        )$epath[[1]]
        writeMask = is.na(E(gTree)$label[pathEdgeIds])
        if (sum(writeMask)) {
            E(gTree)$label[pathEdgeIds[writeMask]] = r
            r = r + 1
        }
        if (all(!is.na(E(gTree)$label))) {
            break()
        }
    }
    gTreeLabelOrder = order(E(gTree)$label, decreasing = T)
    for (p in 2:igraph::vcount(g)) {
        edgeIdToCut = gTreeLabelOrder[seq_len(p - 1)]
        thisMembership = igraph::components(gTree - E(gTree)[edgeIdToCut])$membership
        thisQ = igraph::modularity(g, thisMembership)
        if (thisQ > maxQ) {
            maxQ = thisQ
            maxMembership = thisMembership
        }
    }
    return(igraph::make_clusters(g, maxMembership, modularity = maxQ))
}


#'
#' @note This function implements the "Spanning Tree Based Algorithm (STBA) for Community Detection"
#'           as presented in the paper by R. K. Beheraa, S. K. Ratha and M. Jena (with some modifications)
#'       The algorithm works as the following:
#'       1. Compute the weight w for each edge in the graph
#'       2. Build a mst using the weight w
#'       3. Remove the edge in the mst with lowest weight w. The components give a partition
#'       4. Compute the modularity of the partition, reduce patience if the modularity is not improving
#'       5. Repeat step 3 and step 4 until there is no edge left or run out of patience
#'       6. Report the partition with highest modularity score
#'       In the original paper, the patience is 0, i.e. the loop quits at the first failure of improvment
#'       Also, the original algorithm is designed to maximal the Min-Max modularity,
#'           rather than the usual modularity
#'       Furthermore, in the original algorithm, the Min-Max modularity takes into
#'           account the vertices that are ''related'' but ''between which there exist no edge''.
#'       In this implementation, no such relation is taken into account
#'
#' @description find communities with min-max modularity
#'
#' @param g igraph graph object. the graph to cluster on
#'
#' @param to.use.min.max.modularity boolean. determine if Min-Max modularity should be used
#'                                  if TRUE, the report modularity would be Min-Max modularity
#'                                  default: FALSE
#'
#' @param patience integer, or Inf. The maximal number of continuous failure allowed
#'                 default: Inf
#'
#' @return igraph::communities object with membership and modularity.
#'         the modularity is computed as if g is unweighted
#'
#' @references R. K. Beheraa, S. K. Ratha, M. Jena.
#'             Spanning Tree Based Community Detection using Min-Max Modularity
#'
Graph.Clustering.Algo.stbaClustering = function(g, to.use.min.max.modularity = FALSE, patience = Inf) {
    .modu = function(membershipVect) igraph::modularity(g, membershipVect)
    N = igraph::vcount(g)
    adjMatrix = igraph::as_adjacency_matrix(g, sparse = FALSE)
    edgeEndPt = igraph::ends(g, igraph::E(g))
    if (to.use.min.max.modularity) {
        complementG = igraph::graph_from_adjacency_matrix(1 - adjMatrix, mode = "undirected", diag = FALSE)
        .modu = function(membershipVect) igraph::modularity(g, membershipVect) - igraph::modularity(complementG, membershipVect)
    }
    CNei = sapply(seq_len(igraph::ecount(g)), function(eIdx) {
        return(sum(adjMatrix[edgeEndPt[eIdx, 1], ] & adjMatrix[edgeEndPt[eIdx, 2], ]))
    })
    TNei = sapply(seq_len(igraph::ecount(g)), function(eIdx) {
        return(sum(adjMatrix[edgeEndPt[eIdx, 1], ] | adjMatrix[edgeEndPt[eIdx, 2], ]))
    })
    CEdge = sapply(seq_len(igraph::ecount(g)), function(eIdx) {
        return(sum(adjMatrix[adjMatrix[edgeEndPt[eIdx, 1], ], adjMatrix[edgeEndPt[eIdx, 2], ]]))
    })
    igraph::E(g)$w = (CNei + CEdge) / (TNei + choose(CNei, 2))
    gMST = igraph::mst(g, igraph::E(g)$w)
    gMSTEdgePt = igraph::ends(gMST, igraph::E(gMST))[order(igraph::E(gMST)$w), ]
    maxMembership = igraph::components(gMST)$membership
    maxQ = .modu(maxMembership)
    patienceCounter = patience
    for (edgeToCut in seq_len(nrow(gMSTEdgePt))) {
        gMST = gMST - igraph::E(gMST)[igraph::get.edge.ids(gMST, gMSTEdgePt[edgeToCut, ])]
        thisMembership = igraph::components(gMST)$membership
        thisQ = .modu(thisMembership)
        if (thisQ > maxQ) {
            patienceCounter = patience
            maxQ = thisQ
            maxMembership = thisMembership
        } else {
            patienceCounter = patienceCounter - 1
        }
        if (patienceCounter < 0) {
            break()
        }
    }
    return(igraph::make_clusters(g, maxMembership, modularity = maxQ))
}


#'
#' @note This function implements novel Louvain algorithm as presented in
#'           the paper by Souliou et al.
#'       The algorithm works as following:
#'       1. Compute the NOVER score and edge betweenness for each edge
#'       2. Compute the quotient of NOVER score and edge betweenness for each edge
#'       3. Use the quotient as edge weight to run Louvain algorithm
#'       Here, the definition of NOVER score is different from usual.
#'       The NOVER score is computed as size(intersection) / size(union),
#'           rather than size(intersection) / (size(union) - 2)
#'       To use the original version of NOVER score (i.e. with the -2),
#'           use NOVER_Louvain with ebNormalize = TRUE
#'
#' @description Find communities with novel Louvain
#'
#' @param g igraph graph object. the graph to cluster on
#'
#' @template with.edge.weight.correction boolean. determine if edge weight correction should be done
#'                                       default: FALSE
#'
#' @return igraph::communities object with membership and modularity.
#'         the modularity is computed as if g is unweighted
#'
#' @references A. Pagourtzis, D. Souliou, P. Potikas, K. Potika.
#'             Weight assignment on edges towards improved community detection.
#'             doi: 10.1145/3331076.3331121
#'
Graph.Clustering.Algo.novelLouvainClustering = function(g, with.edge.weight.correction = FALSE){
    adjMatrix = as_adjacency_matrix(g)
    edgeEndPt = ends(g, E(g))
    novelScore = function(eidx){
        u = edgeEndPt[eidx, 1]
        v = edgeEndPt[eidx, 2]
        return(sum(adjMatrix[u, ] & adjMatrix[v, ]) / sum(adjMatrix[u, ] | adjMatrix[v, ]))
    }
    louvainEdgeWeight = sapply(E(g), novelScore) / edge_betweenness(g)
    if (with.edge.weight.correction && !is.null(E(g)$weight)){
        louvainEdgeWeight = louvainEdgeWeight / E(g)$weight * max(E(g)$weight)
    }
    thisMembership = cluster_louvain(g, louvainEdgeWeight)$membership
    thisQ = modularity(g, thisMembership)
    return(make_clusters(g, thisMembership, modularity = thisQ))
}


#'
#' @description find the evolution of the communities in the data
#'
#' @param list.of.time.series a list of numeric vector.
#'                   each vector is a time series of the same quantity on the same time period
#'                   all vectors should have same length
#'                   normalization and transformation should be done before passing in
#'
#' @param adj.matrix.generate.method a function to generate (weighted) adjacency matrix
#'                                   the function should take in a list of numeric vectors and produce a numeric matrix
#'                                   segments of list.of.time.series will be passed in
#'
#' @param graph.generate.method a function to generate graphs to cluster
#'                              the function should take in a numeric matrix and produce a igraph graph object
#'                              output from adj.matrix.generate.method will passed in directly
#'
#' @param clustering.method a function to cluster graphs
#'                          it should take a igraph graph object as the only input
#'                          output from graph.generate.method will be passed in directly
#'                          extra parameters should be enclosed before passing in
#'
#' @param window.dist integer. the size of the sliding window
#'                    assumed positive
#'                    segments of list.of.time.series of this size will be processed in each round
#'
#' @param window.dist integer, or NULL determine how far two consecutive windows should be
#'                    if integer, the window will move this amount
#'                    if NULL, windows will be closely patched (no overlapping, same as window.size)
#'                    default: NULL
#'
#' @param layout.generate.method function. the method to compute graph layout.
#'                               the layout will be computed from the first graph
#'                               default: igraph::layout.kamada.kawai
#'
#' @param to.compute.ARI boolean. determine if pairwise ARI matrix should be computed
#'                       the computation takes time if the number of frames is large
#'                       the computation is done via Graph.Clustering.Metric.adjustedRandIndex
#'                       default: FALSE
#'
#' @param to.compute.NMI boolean. determine if pairwise NMI matrix should be computed
#'                       the computation takes time if the number of frames is large
#'                       the computation is done via Graph.Clustering.Metric.clusterNMISimilarity
#'                       default: FALSE
#'
#' @param to.print.debug.msg boolean. determine if debug message should be printed
#'                           default: FALSE
#'
#' @return a list containing
#'             n, integer, the number of vertices
#'             nFrames, an integer representing the number of time frames
#'             windowSize, the window size used (window.size)
#'             windowMoveDist, the distance the window move (window.dist)
#'             layout, a numeric matrix with 2 columns, the layout to plot the first graph
#'             communities, a list of igraph communities objects
#'             matrices, a list of matrices generated from adj.matrix.generate.method
#'             graphs, a list of igraph graph objects generated from graph.generate.method
#'         this two matrices will also be presented if the corresponding config
#'          is set as TRUE:
#'             ARI, a numeric matrix of size nFrame x nFrame representing the adjusted Rand index (ARI)
#'             NMI, a numeric matrix of size nFrame x nFrame representing the normalized mutual information (NMI)
#'
Graph.Clustering.Animation.evolutions = function(list.of.time.series,
                                                 adj.matrix.generate.method,
                                                 graph.generate.method,
                                                 clustering.method,
                                                 window.size,
                                                 window.dist = NULL,
                                                 layout.generate.method = igraph::layout.kamada.kawai,
                                                 to.compute.ARI = FALSE,
                                                 to.compute.NMI = FALSE,
                                                 to.print.debug.msg = FALSE) {
    windowBegin = 1 # window: [windowBegin, windowBegin + windowSize - 1]
    n = length(list.of.time.series)
    nDays = length(list.of.time.series[[1]])
    commList = list()
    matrixList = list()
    graphList = list()
    firstGraphLayout = NULL
    if (is.null(window.dist)) {
        window.dist = window.size
    }
    while (windowBegin + window.size < nDays) {
        if (to.print.debug.msg) {
            print(paste(
                format(Sys.time(), '%T'),
                "processing [",
                windowBegin,
                ",",
                windowBegin + window.size - 1,
                "] out of",
                nDays
            ))
        }
        # ? can lapply be optimized?
        dataSegment = lapply(list.of.time.series, function(dataSeq) dataSeq[windowBegin:(windowBegin + window.size - 1)])
        thisMatrix = adj.matrix.generate.method(dataSegment)
        matrixList[[length(matrixList) + 1]] = thisMatrix
        thisGraph = graph.generate.method(thisMatrix)
        graphList[[length(graphList) + 1]] = thisGraph
        if (is.null(firstGraphLayout)) {
            firstGraphLayout = layout.generate.method(thisGraph)
        }
        commList[[length(commList) + 1]] = clustering.method(thisGraph)
        windowBegin = windowBegin + window.dist
    }
    if (windowBegin <= nDays) {
        warning(paste(nDays - (windowBegin - window.dist + window.size - 1), "data points are not used"))
    }
    returnAns = list(
        n = n,
        nFrames = length(commList),
        windowSize = window.size,
        windowMoveDist = window.dist,
        methods = list(
            matrix = adj.matrix.generate.method,
            graph = graph.generate.method,
            cluster = clustering.method
        ),
        layout = firstGraphLayout,
        communities = commList,
        matrices = matrixList,
        graphs = graphList
    )
    if (to.compute.ARI) {
        if (to.print.debug.msg) {
            print(paste(format(Sys.time(), '%T'), "compute ARI"))
        }
        returnAns$ARI = Graph.Clustering.Metric.Batch.similarity(commList, Graph.Clustering.Metric.adjustedRandIndex)
    }
    if (to.compute.NMI) {
        if (to.print.debug.msg) {
            print(paste(format(Sys.time(), '%T'), "compute NMI"))
        }
        returnAns$NMI = Graph.Clustering.Metric.Batch.similarity(commList, Graph.Clustering.Metric.clusterNMISimilarity)
    }
    return(returnAns)
}

#'
#' @description plot all graphs for the evolution
#'
#' @param evolution.track a list from cluster_evolution. the object to play
#'
#' @param fps numeric. determine the time intervel between two plots
#'            the time interval is 1 / fps
#'            the number of plots in one second is approximately fps
#'
#' @return no return
#'
Graph.Clustering.Animation.plotEvolution = function(evolution.track, fps = 4) {
    if (fps > 20) {
        warning(paste("fps =", fps, "is too high. may not be able to plot graphs"))
    }
    g = igraph::make_empty_graph(evolution.track$n, directed = FALSE)
    for (idx in seq_len(evolution.track$nFrames)) {
        igraph::plot(evolution.track$communities[[idx]], g, layout = evolution.track$layout)
        # plot(evolutionTrack$graphs[[idx]], layout = evolutionTrack$layout)
        mtext(paste(idx, evolution.track$nFrames, sep = '/'), side = 1)
        Sys.sleep(1 / fps)
    }
}
