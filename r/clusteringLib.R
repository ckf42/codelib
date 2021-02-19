# this script provides the following functions:
# 
# normalized_spectral_clustering
# normalized_spectral_clustering_graph
# commListFromMembership
# clusteringToCommList
# adjusted_Rand_index
# clustering_NMI_similarity
# get_max_cliques
# filter_clique_by_size
# clique_homogeneity
# NOVER_score
# NOVER_single_link_clustering
# ACUEB_with_meta
# ACUEB_without_meta
# NOVER_clustering
# maximal_split_on_tree
# maximal_split_clustering
# STBA_clustering
# NOVER_Louvain
# novel_Louvain
# novel_ST_clustering
# modNOVER_score
# modNOVER_Louvain
# edge_nbhd_score
# custom_weight_Louvain
# custom_weight_Louvain_hoffman
# custom_weight_Louvain_maxwell
# custom_weight_Louvain_phi
# custom_weight_Louvain_rand
# custom_weight_Louvain_kulcyznski
# custom_weight_Louvain_preferential
# custom_weight_Louvain_jaccard
# custom_weight_Louvain_nover
# custom_weight_Louvain_novel
# custom_weight_Louvain_invnovel
# ST_clustering
# ST_clustering_hoffman
# ST_clustering_maxwell
# ST_clustering_phi
# ST_clustering_rand
# ST_clustering_kulcyznski
# ST_clustering_preferential
# ST_clustering_jaccard
# ST_clustering_nover
# ST_clustering_novel
# ST_clustering_invnovel
# ST_clustering_unweighted
# testFunctionOnClustering_differentMeasure
# testFunctionOnClustering_differentSTConfig
# testFunctionOnClustering_givenFunction
# mean_clique_disparity
# fourCliqueRatio
# batch_sim
# overlapCommInfoFromBelongCoeffMatrix
# overlapping_modularity
# belongCoeffVectFromCommList
# belongCoeffMatrixFromVectList
# split_betweenness_forest
# OST_clustering
# split_betweenness_greedy
# CONGA
# 
# Please goto the corresponding function definition for detail description
# 

if (!require(igraph)){
    stop('these functions requires igraph')
}

#' 
#' @description finding clusters of a graph with Normalized Spectral 
#'              Clustering (NSC)
#' 
#' @param similarityMatrix numeric matrix. similarity between items. 
#'                         assumed symmetric and has nonnegative entries
#' 
#' @param num_cluster number of clusters
#' 
#' @return a list of num_cluster integer vectors. each vector records the node 
#'         indices that belongs to that cluster
#' 
#' @note the entries of the input matrix are treated as similarity
#' 
#' @references http://fourier.eng.hmc.edu/e161/lectures/algebra/node7.html
#' 
normalized_spectral_clustering = function(similarityMatrix, num_cluster){
    n = nrow(similarityMatrix)
    d = colSums(similarityMatrix)
    L = diag(d) - similarityMatrix
    # solve generalized eigenproblem L * v = lambda * diag(d) * v
    #     and extract num_cluster eigenvect with smallest eigenval
    # this approach is from 
    #     http://fourier.eng.hmc.edu/e161/lectures/algebra/node7.html
    # ? use library / faster approach? 
    V = eigen(L / outer(d, d), symmetric = TRUE)$vectors[, n:(n + 1 - num_cluster)] / sqrt(d)
    clusterIndices = kmeans(V, num_cluster)$cluster
    return(lapply(seq_len(num_cluster), function(idx)which(clusterIndices == idx)))
}

#' 
#' @description finding clusters of a graph with Normalized Spectral 
#'              Clustering (NSC)
#' 
#' @param g igraph graph object. the graph to be cluster
#' 
#' @param num_cluster integer. number of clusters
#' 
#' @param weighted boolean. determine if the graph input should be seen as unweighted
#'                 if FALSE, edge weights in g will be ignored
#'                 if TRUE, edge weights will be used as vertex similarities
#'                 default: FALSE
#' 
#' @return igraph::communities object with membership and modularity. 
#'         the modularity is computed as g is weighted
#' 
#' @note the weights of the edges are treated as similarity
#' 
#' @note wrapper of normalized_spectral_clustering
#' 
normalized_spectral_clustering_graph = function(g, num_cluster, weighted = FALSE){
    if (!weighted && !is.null(E(g)$weight)){
        g = delete_edge_attr(g, 'weight') 
    }
    simMatrix = as_adjacency_matrix(g, sparse = FALSE)
    diag(simMatrix) = 1
    listOfClusters = normalized_spectral_clustering(simMatrix, num_cluster)
    n = vcount(g)
    clusterIndices = rep(NA, n)
    for (i in seq_along(listOfClusters)){
        clusterIndices[listOfClusters[[i]]] = i
    }
    return(make_clusters(g, 
                         clusterIndices, 
                         modularity = modularity(g, clusterIndices, weights = E(g)$weight)))
}


#' 
#' @description convert membership vector to list of clusters
#' 
#' @param membershipVector integer vector. 
#'                         denote id of cluster an element belongs to
#' 
#' @param namesOfIdx NULL, or character vector. the names corresponding to the indices
#'                   if NULL, will keep as integers
#'                   default: NULL
#' 
#' @return a list of integer vectors. each vector is a cluster and records the indices of its members
#'         if namesOfIdx is not NULL, the vectors will be converted into characters according to it
#' 
commListFromMembership = function(membershipVector, namesOfIdx = NULL){
    listOfComm = lapply(unique(membershipVector), 
                        function(idx)which(membershipVector == idx))
    if (!is.null(namesOfIdx)){
        listOfComm = lapply(listOfComm, function(indVect)namesOfIdx[indVect])
    }
    return(listOfComm)
}

#' 
#' @description transform list of communities to membership vector
#' 
#' @param commList list of integer vectors. 
#'                 assumed a partition of 1:max(unlist(commList))
#'                 (no overlapping, each integer appears exactly once)
#' 
#' @return a integer vector of length max(unlist(commList)) denoting the community index
#' 
membershipFromCommList = function(commList){
    membershipVect = rep(NULL, max(sapply(commList, max)))
    for (commIdx in seq_along(commList)){
        membershipVect[commList[[commIdx]]] = commIdx
    }
    return(membershipVect)
}

#' 
#' @description transform clustering items to list of clusters
#' 
#' @param clustering igraph::communities object, integer vector, or list of integer vectors
#'                   the clustering object to be transform
#' 
#' @return list of integer vectors
#' 
clusteringToCommList = function(clustering){
    if (class(clustering) == 'communities'){
        clustering = clustering$membership
    }
    if (is.vector(clustering)){
        clustering = commListFromMembership(clustering)
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
adjusted_Rand_index = function(clustering1, clustering2){
    clustering1 = clusteringToCommList(clustering1)
    clustering2 = clusteringToCommList(clustering2)
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
#' @param useMax boolean. determine if max entropy should be used to normalize
#'               by default the normalizer is the arithmetic mean
#'               default: FALSE
#' 
#' @return a numeric representing the similarity of the two clusterings
#' 
clustering_NMI_similarity = function(clustering1, clustering2, useMax = FALSE){
    clustering1 = clusteringToCommList(clustering1)
    clustering2 = clusteringToCommList(clustering2)
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
               (if(useMax) max else mean)(c(sum(n1 * log2(n / n1)), sum(n2 * log2(n / n2)))))
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
get_max_cliques = function(g){
    return(max_cliques(g, min = 3))
}

#' 
#' @description filter out cliques of certain sizes
#' 
#' @param listOfCliques list of integer vectors. 
#'                      each vector shoule be a clique and records the indices of the vertices
#' 
#' @param allowSize integer vector. the size of cliques that are kept
#' 
#' @return a list of integer vectors. 
#'         same as listOfCliques, but vectors of size not in allowSize is removed
#' 
filter_clique_by_size = function(listOfCliques, allowSize){
    return(Filter(function(vertexVect)length(vertexVect) %in% allowSize, listOfCliques))
}

#' 
#' @description compute the ratio of cliques with the same tag
#' 
#' @param listOfCliques a list of intege vectors. 
#'                      each vector should be a clique and records the indices 
#'                          of vertices in this clique
#' 
#' @param vertexTags a integet vector representing the tags. 
#'                   the tag of vertex i should be vertexTags[i]
#' 
#' @return a numeric between 0 and 1 representing the ratio of cliques that 
#'             have the same tags on the vertices
#' 
#' @references S. S. Hosseini, N. Wormald, T. Tian
#'             A Weight-based Information Filtration Algorithm for Stock-Correlation Networks
#' 
clique_homogeneity = function(listOfCliques, vertexTags){
    isHomogen = sapply(listOfCliques, 
                       function(vertexVect)length(unique(vertexTags[vertexVect])) == 1)
    return(sum(isHomogen) / length(isHomogen))
}

#' 
#' @description compute the NOVER score for the edges
#' 
#' @param g igraph graph object. the graph to compute NOVER on
#' 
#' @param targetEdges igraph edge sequence. the edges to compute NOVER score
#'                    default: E(g)
#' 
#' @return a numeric vector. the NOVER score of the edges in targetEdges
#' 
NOVER_score = function(g, targetEdges = E(g)){
    adjMatrix = as_adjacency_matrix(g)
    V(g)$name = seq_len(vcount(g))
    edgeEndPt = ends(g, targetEdges)
    NOVERScore_internal = function(eidx){
        u = as.integer(edgeEndPt[eidx, 1])
        v = as.integer(edgeEndPt[eidx, 2])
        uni = sum(adjMatrix[u, ] | adjMatrix[v, ]) - 2
        if (uni == 0){
            return(0)
        } else {
            return(sum(adjMatrix[u, ] & adjMatrix[v, ]) / uni)
        }
    }
    return(sapply(seq_along(targetEdges), NOVERScore_internal))
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
#' @param testTime integer, or Inf. the maximal number of trial cuts
#'                 capped at the number of vertices of g
#'                 default: Inf
#' 
#' @param useMinSpanTree boolean. determine if Minimal Spanning Tree should be used instead of Maximal Spanning Tree
#'                       default: FALSE
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
NOVER_single_link_clustering = function(g, testTime = Inf, useMinSpanTree = FALSE){
    # compute NOVER score for all edges
    adjMatrix = as_adjacency_matrix(g)
    edgeEndPt = ends(g, E(g))
    NOVERScore = function(eidx){
        u = edgeEndPt[eidx, 1]
        v = edgeEndPt[eidx, 2]
        uni = sum(adjMatrix[u, ] | adjMatrix[v, ]) - 2
        if (uni == 0){
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
    NOVERMST = mst(g, (if (useMinSpanTree) 1 else -1) * sapply(E(g), NOVERScore))
    edgeOrder = order(edge_betweenness(NOVERMST), decreasing = TRUE)
    numOfEdgeToRemove = sample.int(ecount(NOVERMST) + 1, min(ecount(NOVERMST) + 1, testTime)) - 1
    maxQ = -Inf
    maxMembership = NULL
    for (k in numOfEdgeToRemove){
        cutMST = delete_edges(NOVERMST, edgeOrder[seq_len(k)])
        thisMembership = components(cutMST)$membership
        thisQ = modularity(g, thisMembership)
        if (thisQ > maxQ){
            maxQ = thisQ
            maxMembership = thisMembership
        }
    }
    return(make_clusters(g, maxMembership, modularity = maxQ))
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
#' @param oneEdgeAtATime boolean. determine if only one edge should be add at a step
#'                       default: TRUE
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
ACUEB_with_meta = function(g, patience = Inf, oneEdgeAtATime = TRUE){
    if (is.null(E(g)$weight)){
        E(g)$weight = 1
    }
    n = vcount(g)
    gOrigin = g
    gPrime = make_empty_graph(n, directed = FALSE)
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
    getOrigEdgeIdFromMeta = function(metaEdgeHead, metaEdgeTail, metaGroupIdx){
        vGroup = which(metaGroupIdx == metaEdgeHead)
        uGroup = which(metaGroupIdx == metaEdgeTail)
        vuCombn = expand.grid(vGroup, uGroup)
        for (idx in seq_len(nrow(vuCombn))){
            origEdgeId = get.edge.ids(gOrigin, vuCombn[idx, ])
            if (origEdgeId != 0){
                return(origEdgeId)
            }
        }
        stop("In ACUEB_with_meta::getOrigEdgeIdFromMeta, target edge not found")
    }
    while (patienceCounter > 0 && ecount(g) > 0){
        ebList = edge_betweenness(g)
        minEBEdgeIdx = NULL
        if (oneEdgeAtATime){
            minEBEdgeIdx = which.min(ebList)
        } else {
            minEBEdgeIdx = which(ebList == min(ebList))
        }
        # get edge id on gOrigin from edge id on g (meta)
        origEdgeIdx = sapply(minEBEdgeIdx, 
                             function(edgeIdx)getOrigEdgeIdFromMeta(head_of(g, edgeIdx), 
                                                                    tail_of(g, edgeIdx), 
                                                                    metaGrouping))
        # contract vertices
        gPrime = add_edges(gPrime, 
                           as.vector(rbind(head_of(gOrigin, origEdgeIdx), 
                                           tail_of(gOrigin, origEdgeIdx))))
        thisMembership = components(gPrime)$membership
        thisQ = modularity(gOrigin, thisMembership)
        metaGrouping = thisMembership
        g = contract(gOrigin, metaGrouping, vertex.attr.comb = 'min')
        g = simplify(g, edge.attr.comb = 'min') # remove mult-edge, self-loop
        # update maximal
        if (thisQ > maxQ){
            patienceCounter = patience
            maxQ = thisQ
            maxMembership = thisMembership
        } else {
            patienceCounter = patienceCounter - 1
        }
    }
    return(make_clusters(g, maxMembership, modularity = maxQ))
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
ACUEB_without_meta = function(g, patience = Inf){
    n = vcount(g)
    if (is.null(E(g)$weight)){
        E(g)$weight = 1
    }
    edgeEndPt = ends(g, E(g))
    ebList = edge_betweenness(g)
    ebOrder = order(ebList)
    ebSPtr = 1
    patienceCounter = patience
    maxMembership = components(g)$membership
    maxQ = modularity(g, maxMembership)
    gPrime = make_empty_graph(n, directed = FALSE)
    while (patienceCounter > 0 && ebSPtr <= length(ebList)){
        ebEPtr = ebSPtr + 1
        while (ebEPtr <= length(ebList) && ebList[ebOrder[ebSPtr]] == ebList[ebOrder[ebEPtr]]){
            ebEPtr = ebEPtr + 1
        } # range [ebSPtr, ebEptr)
        gPrime = add_edges(gPrime, 
                           as.vector(t(edgeEndPt[ebOrder[ebSPtr:(ebEPtr - 1)], ])))
        ebSPtr = ebEPtr
        thisMembership = components(gPrime)$membership
        thisQ = modularity(g, thisMembership)
        if (thisQ > maxQ){
            maxQ = thisQ
            maxMembership = thisMembership
            patienceCounter = patience
        } else {
            patienceCounter = patienceCounter - 1
        }
    }
    return(make_clusters(g, maxMembership, modularity = maxQ))
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
NOVER_clustering = function(g){
    # compute NOVER score for all edges
    adjMatrix = as_adjacency_matrix(g)
    V(g)$name = seq_len(vcount(g))
    edgeEndPt = ends(g, E(g))
    NOVERList = sapply(E(g), function(eidx){
        u = as.integer(edgeEndPt[eidx, 1])
        v = as.integer(edgeEndPt[eidx, 2])
        uni = sum(adjMatrix[u, ] | adjMatrix[v, ]) - 2
        if (uni == 0){
            return(0)
        } else {
            return(sum(adjMatrix[u, ] & adjMatrix[v, ]) / uni)
        }
    })
    NOVEROrder = order(NOVERList)
    maxMembership = components(g)$membership
    lastMembership = maxMembership
    maxQ = modularity(g, maxMembership)
    gCut = g
    for (edgeToCut in seq_len(nrow(edgeEndPt))){
        gCut = gCut - E(gCut)[get.edge.ids(gCut, edgeEndPt[NOVEROrder[edgeToCut], ])]
        thisMembership = components(gCut)$membership
        if (any(lastMembership != thisMembership)){
            lastMembership = thisMembership
            thisQ = modularity(g, thisMembership)
            if (thisQ > maxQ){
                maxQ = thisQ
                maxMembership = thisMembership
            }
        } 
    }
    names(maxMembership) = NULL
    return(make_clusters(g, maxMembership, modularity = maxQ))
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
#' @param gTree igraph graph object. assumed to be a tree
#' 
#' @param p integer. the number of clusters to return. assumed 1 <= p <= |V|
#' 
#' @param computeMod boolean. determine if modularity should be computed
#'                   default: TRUE
#' 
#' @return igraph::communities object with membership and modularity. 
#'         the modularity is computed as g is unweighted
#'         if computeMod is FALSE, the modularity returned is 0
#' 
#' @references M. Maravalle, B Simeone, R. Naldini. 
#'             Clustering on trees
#' 
maximal_split_on_tree = function(gTree, p, computeMod = TRUE){
    if (p == 1){
        maxMembership = components(gTree)$membership
        return(make_clusters(gTree, 
                             maxMembership, 
                             modularity = if (computeMod) 0 else modularity(gTree, maxMembership)))
    }
    N = vcount(gTree)
    pairwiseDist = distances(gTree)
    pairwiseDist[upper.tri(pairwiseDist, diag = TRUE)] = NA
    edgeOrdering = order(pairwiseDist, na.last = NA)
    E(gTree)$label = rep(NA, ecount(gTree))
    r = 1
    for (idxPair in edgeOrdering){
        pathEdgeIds = shortest_paths(gTree, 
                                     (idxPair - 1) %/% N + 1, 
                                     (idxPair - 1) %% N + 1, 
                                     output = 'epath')$epath[[1]]
        writeMask = is.na(E(gTree)$label[pathEdgeIds])
        if(sum(writeMask)){
            E(gTree)$label[pathEdgeIds[writeMask]] = r
            r = r + 1
        }
        if (all(!is.na(E(gTree)$label))){
            break()
        }
    }
    edgeIdToCut = order(E(gTree)$label, decreasing = T)[seq_len(p - 1)]
    thisMembership = components(gTree - E(gTree)[edgeIdToCut])$membership
    return(make_clusters(gTree, thisMembership, 
                         modularity = if (computeMod) 0 else modularity(gTree, thisMembership)))
}

#' 
#' @description clustering graph with maximal split clustering on mst
#' 
#' @param g igraph graph object. the graph to cluster on
#' 
#' @param weightAttr character. the name of the edge attribute used to build MST
#'                   used as distance, so large weight means further distance
#'                   default: 'weight'
#' 
#' @return igraph::communities object with membership and modularity. 
#'         the modularity is computed as g is unweighted
#' 
#' @note This function is a simple modification of maximal_split_on_tree:
#'       It finds the mst of g according to the edge attribute weightAttr
#'       It then enumerates maximal_split_on_tree on all possible p and reports the one 
#'           with highest modularity on g
#' 
maximal_split_clustering = function(g, weightAttr = 'weight'){
    gTree = mst(g, get.edge.attribute(g, weightAttr))
    maxMembership = components(gTree)$membership
    maxQ = modularity(gTree, maxMembership)
    N = vcount(gTree)
    pairwiseDist = distances(gTree)
    pairwiseDist[upper.tri(pairwiseDist, diag = TRUE)] = NA
    edgeOrdering = order(pairwiseDist, na.last = NA)
    E(gTree)$label = rep(NA, ecount(gTree))
    r = 1
    for (idxPair in edgeOrdering){
        pathEdgeIds = shortest_paths(gTree, 
                                     (idxPair - 1) %/% N + 1, 
                                     (idxPair - 1) %% N + 1, 
                                     output = 'epath')$epath[[1]]
        writeMask = is.na(E(gTree)$label[pathEdgeIds])
        if(sum(writeMask)){
            E(gTree)$label[pathEdgeIds[writeMask]] = r
            r = r + 1
        }
        if (all(!is.na(E(gTree)$label))){
            break()
        }
    }
    gTreeLabelOrder = order(E(gTree)$label, decreasing = T)
    for (p in 2:vcount(g)){
        edgeIdToCut = gTreeLabelOrder[seq_len(p - 1)]
        thisMembership = components(gTree - E(gTree)[edgeIdToCut])$membership
        thisQ = modularity(g, thisMembership)
        if (thisQ > maxQ){
            maxQ = thisQ
            maxMembership = thisMembership
        }
    }
    return(make_clusters(g, maxMembership, modularity = maxQ))
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
#' @param useMinMaxMod boolean. determine if Min-Max modularity should be used
#'                     if TRUE, the report modularity would be Min-Max modularity
#'                     default: FALSE
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
STBA_clustering = function(g, useMinMaxMod = FALSE, patience = Inf){
    modu = function(membershipVect)modularity(g, membershipVect)
    N = vcount(g)
    adjMatrix = as_adjacency_matrix(g, sparse = FALSE)
    edgeEndPt = ends(g, E(g))
    if (useMinMaxMod){
        complementG = graph_from_adjacency_matrix(1 - adjMatrix, mode = "undirected", diag = FALSE)
        modu = function(membershipVect)modularity(g, membershipVect) - modularity(complementG, membershipVect)
    }
    CNei = sapply(seq_len(ecount(g)), function(eIdx){
        return(sum(adjMatrix[edgeEndPt[eIdx, 1], ] & adjMatrix[edgeEndPt[eIdx, 2], ]))
    })
    TNei = sapply(seq_len(ecount(g)), function(eIdx){
        return(sum(adjMatrix[edgeEndPt[eIdx, 1], ] | adjMatrix[edgeEndPt[eIdx, 2], ]))
    })
    CEdge = sapply(seq_len(ecount(g)), function(eIdx){
        return(sum(adjMatrix[adjMatrix[edgeEndPt[eIdx, 1], ], adjMatrix[edgeEndPt[eIdx, 2], ]]))
    })
    E(g)$w = (CNei + CEdge) / (TNei + choose(CNei, 2))
    gMST = mst(g, E(g)$w)
    gMSTEdgePt = ends(gMST, E(gMST))[order(E(gMST)$w), ]
    maxMembership = components(gMST)$membership
    maxQ = modu(maxMembership)
    patienceCounter = patience
    for (edgeToCut in seq_len(nrow(gMSTEdgePt))){
        gMST = gMST - E(gMST)[get.edge.ids(gMST, gMSTEdgePt[edgeToCut, ])]
        thisMembership = components(gMST)$membership
        thisQ = modu(thisMembership)
        if (thisQ > maxQ){
            patienceCounter = patience
            maxQ = thisQ
            maxMembership = thisMembership
        } else {
            patienceCounter = patienceCounter - 1
        }
        if (patienceCounter < 0){
            break()
        }
    }
    return(make_clusters(g, maxMembership, modularity = maxQ))
}

#' 
#' @description Find clustering with NOVER-Louvain
#' 
#' @param g igraph graph object. the graph to cluster on
#' 
#' @param ebNormalize boolean. determine if the NOVER score should be divided by edge betweenness
#'                    default: FALSE
#' 
#' @return igraph::communities object with membership and modularity. 
#'         the modularity is computed as if g is unweighted
#'         
#' @note this function use a variant of Louvain algorithm to find clustering
#'       The algorithm works in the following way:
#'       1. Compute for each edge the NOVER score
#'       2. Find the clustering with Louvain algorithm using the NOVER score as similarity 
#' 
NOVER_Louvain = function(g, ebNormalize = FALSE){
    # compute NOVER score for all edges
    adjMatrix = as_adjacency_matrix(g)
    edgeEndPt = ends(g, E(g))
    edgeScore = sapply(E(g), function(eidx){
        u = edgeEndPt[eidx, 1]
        v = edgeEndPt[eidx, 2]
        uni = sum(adjMatrix[u, ] | adjMatrix[v, ]) - 2
        if (uni == 0){
            return(0)
        } else {
            return(sum(adjMatrix[u, ] & adjMatrix[v, ]) / uni)
        }
    })
    if (ebNormalize){
        edgeScore = edgeScore / edge_betweenness(g)
    }
    thisMembership = cluster_louvain(g, edgeScore)$membership
    thisQ = modularity(g, thisMembership)
    return(make_clusters(g, thisMembership, modularity = thisQ))
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
#' @return igraph::communities object with membership and modularity. 
#'         the modularity is computed as if g is unweighted 
#'         
#' @references A. Pagourtzis, D. Souliou, P. Potikas, K. Potika. 
#'             Weight assignment on edges towards improved community detection. 
#'             doi: 10.1145/3331076.3331121
#' 
novel_Louvain = function(g, edgeWeightCorrection = FALSE){
    adjMatrix = as_adjacency_matrix(g)
    edgeEndPt = ends(g, E(g))
    novelScore = function(eidx){
        u = edgeEndPt[eidx, 1]
        v = edgeEndPt[eidx, 2]
        return(sum(adjMatrix[u, ] & adjMatrix[v, ]) / sum(adjMatrix[u, ] | adjMatrix[v, ]))
    }
    louvainEdgeWeight = sapply(E(g), novelScore) / edge_betweenness(g)
    if (edgeWeightCorrection && !is.null(E(g)$weight)){
        louvainEdgeWeight = louvainEdgeWeight / E(g)$weight * max(E(g)$weight)
    }
    thisMembership = cluster_louvain(g, louvainEdgeWeight)$membership
    thisQ = modularity(g, thisMembership)
    return(make_clusters(g, thisMembership, modularity = thisQ))
}


#' 
#' @note This function implements novelST algorithm as presented in 
#'           the paper by Souliou et al. 
#'       The algorithm works as following:
#'       1. Compute the NOVER score and edge betweenness for each edge
#'       2. Compute the quotient of edge betweenness NOVER score for each edge
#'       3. Use the quotient to build a minimal spanning tree
#'       4. Remove the edge with highest edge betweenness in the MST. The components give a partition
#'       5. Repeat step 4 until there is no edge left
#'       6. Report the partition with highest modularity score
#'       Here, the definition of NOVER score is different from usual.
#'       The NOVER score is computed as size(intersection) / size(union), 
#'           rather than size(intersection) / (size(union) - 2) 
#' 
#' @description Find communities with novelST
#' 
#' @param g igraph graph object. the graph to cluster on
#' 
#' @return igraph::communities object with membership and modularity. 
#'         the modularity is computed as if g is unweighted 
#'         
#' @references A. Pagourtzis, D. Souliou, P. Potikas, K. Potika. 
#'             Weight assignment on edges towards improved community detection. 
#'             doi: 10.1145/3331076.3331121
#' 
novel_ST_clustering = function(g, oneEdgeAtATime = TRUE, edgeWeightCorrection = FALSE){
    # compute NOVER score for all edges
    adjMatrix = as_adjacency_matrix(g)
    edgeEndPt = ends(g, E(g))
    novelScore = function(eidx){
        u = edgeEndPt[eidx, 1]
        v = edgeEndPt[eidx, 2]
        return(sum(adjMatrix[u, ] & adjMatrix[v, ]) / sum(adjMatrix[u, ] | adjMatrix[v, ]))
    }
    novelMSTEdgeWeight = edge.betweenness(g) / sapply(E(g), novelScore)
    if (edgeWeightCorrection && !is.null(E(g)$weight)){
        novelMSTEdgeWeight = novelMSTEdgeWeight * E(g)$weight / max(E(g)$weight)
    }
    novelMST = mst(g, novelMSTEdgeWeight)
    edgeOrder = order(edge_betweenness(novelMST), decreasing = TRUE)
    maxMembership = components(novelMST)$membership
    maxQ = modularity(g, maxMembership)
    for (k in seq_len(vcount(novelMST) - 1)){
        cutMST = delete_edges(novelMST, edgeOrder[seq_len(k)])
        thisMembership = components(cutMST)$membership
        thisQ = modularity(g, thisMembership)
        if (thisQ > maxQ){
            maxQ = thisQ
            maxMembership = thisMembership
        }
    }
    # while (ecount(novelMST) != 0){
    #     edgeToRemove = NULL
    #     ebMST = edge_betweenness(novelMST)
    #     if (oneEdgeAtATime){
    #         edgeToRemove = which.max(ebMST)
    #     } else {
    #         edgeToRemove = which(ebMST == max(ebMST))
    #     }
    #     novelMST = delete.edges(novelMST, E(novelMST)[edgeToRemove])
    #     thisMembership = components(novelMST)$membership
    #     thisQ = modularity(g, thisMembership)
    #     if (thisQ > maxQ){
    #         maxQ = thisQ
    #         maxMembership = thisMembership
    #     }
    # }
    return(make_clusters(g, maxMembership, modularity = maxQ))
}

modNOVER_score = function(g){
    deg = degree(g)
    adjMatrix = as_adjacency_matrix(g, sparse = FALSE)
    edgeEndPt = ends(g, E(g))
    return(sapply(E(g), 
                  function(eidx){
                      u = edgeEndPt[eidx, 1]
                      v = edgeEndPt[eidx, 2]
                      uniMask = adjMatrix[u, ] | adjMatrix[v, ]
                      uniMask[c(u, v)] = FALSE
                      return(sum(deg[adjMatrix[u, ] & adjMatrix[v, ]]) / sum(deg[uniMask]))
                  }))
}

modNOVER_Louvain = function(g){
    thisMembership = cluster_louvain(g, modNOVER_score(g))$membership
    thisQ = modularity(g, thisMembership)
    return(make_clusters(g, thisMembership, modularity = thisQ))
}

#' 
#' @description Find communities by recursively finding leading eigenvector
#' 
#' @param g igraph::graph object. The graph to cluster on
#'          assumed undirected and simple
#'          the weight attribute will be ignored
#' 
#' @return igraph::communities object with membership and modularity. 
#' 
#' @references M. E. J. Newman. 
#'             Modularity and community structure in networks
#'             arxiv: physics/0602124
#' 
NewmanEigenClustering = function(g){
    eps = .Machine$double.eps # tolerance to 0
    vc = vcount(g)
    m = ecount(g)
    A = as_adjacency_matrix(g)
    d = degree(g)
    QMatrix = A - outer(d, d) / (2 * m)
    NewmanEigenClustering_internal = function(subGIndices){
        if (length(subGIndices) <= 1){
            return(list(partition = list(subGIndices), 
                        QCon = 0))
        }
        k = d[subGIndices]
        dg = Matrix::rowSums(A[subGIndices, subGIndices])
        eigenPair = eigen(QMatrix[subGIndices, subGIndices] - 
                              Matrix::Diagonal(x = dg - k * sum(k) / (2 * m)), 
                          symmetric = TRUE)
        if (eigenPair$values[1] < eps){
            return(list(partition = list(subGIndices), 
                        QCon = 0))
        }
        s = ifelse(eigenPair$vectors[, 1] > eps , 1, -1)
        QCon = sum(eigenPair$values * (t(eigenPair$vectors) %*% s)^2) / (4 * m)
        if (QCon <= eps){
            return(list(partition = list(subGIndices), 
                        QCon = 0))
        }
        gp1Idx = which(s == 1)
        gp1Part = NewmanEigenClustering_internal(subGIndices[gp1Idx])
        gp2Part = NewmanEigenClustering_internal(subGIndices[-gp1Idx])
        return(list(partition = c(gp1Part$partition, gp2Part$partition), 
                    QCon = QCon + gp1Part$QCon + gp2Part$QCon))
    }
    res = NewmanEigenClustering_internal(seq_len(vc))
    return(make_clusters(g, 
                         membershipFromCommList(res$partition), 
                         modularity = res$QCon))
}

# name of edge neighbour overlapping measures, 
# used for   edge_nbhd_score
edge_nbhd_score_measure_list = c('hoffman', 'maxwell', 'phi', 'rand', 
                                 'kulcyznski', 'preferential', 'jaccard', 'nover', 
                                 'novel', 'invnovel', 'unweighted')

#' 
#' @description compute edge measures based on neighborhood overlapping
#' 
#' @param g igraph graph object. the graph to compute measure on
#' 
#' @param measure character string. the name of the measure to use
#'                accepted names are: 
#'                    'hoffman' for adjusted Rand index proposed by Hoffman et al., 
#'                    'maxwell' for adjusted Rand index proposed by Maxwell and Pilliner,
#'                    'phi' for phi coefficient, 
#'                    'rand' for (unadjusted) Rand index, 
#'                    'kulcyznski' for Kulcyznski's measure,
#'                    'preferential' for preferential attachment, 
#'                    'jaccard' for Jaccard coefficient, 
#'                    'nover' for NOVER score (same as Jaccard but denominator is subtracted by 2), 
#'                    'novel' for the modified NOVER score used in the algorithms by Souliou et al., 
#'                    'invnovel' for the reciprocal of novel score
#'                    'unweighted' for uniform weight (1)
#'                the accepted names are stored in edge_nbhd_score_measure_list
#'                the name entered should be exact, otherwise it will be rejected
#'                A rejected name is regarded as unweighted
#'                default: 'hoffman'
#'
#' @param edgeList edge sequence of g. the edges to compute on
#'                 default: E(g)
#' 
#' @return a numeric vector with the same length as edgeList representing the score
#' 
#' @references M. Hoffman, D. Steinley, M. J. Brusco. 
#'             A Note on using the Adjusted Rand Index for Link Prediction in Networks
#'             doi: 10.1016 j.socnet.2015.03.002
#' 
#' @references A. Pagourtzis, D. Souliou, P. Potikas, K. Potika. 
#'             Weight assignment on edges towards improved community detection. 
#'             doi: 10.1145/3331076.3331121
#' 
edge_nbhd_score = function(g, measure = 'hoffman', edgeList = E(g)){
    adjMatrix = as_adjacency_matrix(g)
    edgeEndPt = ends(g, edgeList)
    edgeWeights = sapply(edgeList, function(eidx){
        uNei = adjMatrix[edgeEndPt[eidx, 1], ]
        vNei = adjMatrix[edgeEndPt[eidx, 2], ]
        aVal = uNei %*% vNei
        bVal = uNei %*% (!vNei)
        cVal = (!uNei) %*% vNei
        dVal = (!uNei) %*% (!vNei)
        return(switch(measure, 
                      hoffman = 2 * (aVal * dVal - bVal * cVal) / ((aVal + bVal) * (bVal + dVal) + (aVal + cVal) * (cVal + dVal)), 
                      maxwell = 2 * (aVal * dVal - bVal * cVal) / ((aVal + bVal) * (cVal + dVal) + (aVal + cVal) * (bVal + dVal)), 
                      phi = (aVal * dVal - bVal * cVal) / sqrt((aVal + bVal) * (aVal + cVal) * (bVal + dVal) * (cVal + dVal)), 
                      rand = (aVal + dVal) / (aVal + bVal + cVal + dVal), 
                      # the following measures use only a, b, c
                      # TODO optimize so that d is not computed
                      kulcyznski = aVal * (1 / (aVal + bVal) + 1 / (aVal + cVal)) / 2, 
                      preferential = (aVal + bVal) * (aVal + cVal),
                      novel =,
                      invnovel =,
                      jaccard = aVal / (aVal + bVal + cVal),
                      nover = if (aVal + bVal + cVal == 2) 0 else (aVal / (aVal + bVal + cVal - 2)),
                      # default: 1
                      unweighted =,
                      1))
    })
    if (measure == 'novel'){ # extra computation
        edgeWeights = edgeWeights / edge.betweenness(g, edgeList)
    } else if (measure == 'invnovel'){
        edgeWeights = edge.betweenness(g, edgeList) / edgeWeights
    }
    return(edgeWeights)
}

#' 
#' @description find clustering with Louvain on edge measure
#' 
#' @param g igraph graph object. the graph to find cluster on
#' 
#' @param measure character string. the edge measure to use
#'                accepted strings are the same as edge_nbhd_score
#'                the parameter is passed directly to edge_nbhd_score
#' 
#' @param linearNormalize boolean. determine if measures should be linearly transform before cutoff
#'                        if TRUE, the measure will be transformed as x -> (x + 1) / 2
#'                                 should transform weight in [-1, 1] to [0, 1]
#'                        default: FALSE
#' 
#' @return igraph::communities object with membership and modularity. 
#'         the modularity is computed as if g is unweighted 
#' 
custom_weight_Louvain = function(g, measure, linearNormalize = TRUE){
    edgeWeight = edge_nbhd_score(g, measure)
    if (linearNormalize){
        edgeWeight = (edgeWeight + 1) / 2
    }
    edgeWeight = pmax(edgeWeight, 0)
    thisMembership = cluster_louvain(g, edgeWeight)$membership
    thisQ = modularity(g, thisMembership)
    return(make_clusters(g, thisMembership, modularity = thisQ))
}

custom_weight_Louvain_measures = list(
    
    # instantiation of custom_weight_Louvain on edge measures starts here
    custom_weight_Louvain_hoffman = function(g){
        return(custom_weight_Louvain(g, 'hoffman'))
    }, 
    
    custom_weight_Louvain_maxwell = function(g){
        return(custom_weight_Louvain(g, 'maxwell'))
    }, 
    
    custom_weight_Louvain_phi = function(g){
        return(custom_weight_Louvain(g, 'phi'))
    }, 
    
    custom_weight_Louvain_rand = function(g){
        return(custom_weight_Louvain(g, 'rand'))
    }, 
    
    custom_weight_Louvain_kulcyznski = function(g){
        return(custom_weight_Louvain(g, 'kulcyznski'))
    }, 
    
    custom_weight_Louvain_preferential = function(g){
        return(custom_weight_Louvain(g, 'preferential'))
    }, 
    
    custom_weight_Louvain_jaccard = function(g){
        return(custom_weight_Louvain(g, 'jaccard'))
    }, 
    
    custom_weight_Louvain_nover = function(g){
        return(custom_weight_Louvain(g, 'nover'))
    }, 
    
    custom_weight_Louvain_novel = function(g){
        return(custom_weight_Louvain(g, 'novel'))
    }, 
    
    custom_weight_Louvain_invnovel = function(g){
        return(custom_weight_Louvain(g, 'invnovel'))
    }
    # instantiation of custom_weight_Louvain on edge measures ends here
    
)


# all possible configs, better way than hard-coded?
ST_clustering_optionalPara_all = list(list(precomputeOrder = FALSE, useMaxSpanTree = TRUE, oneEdgeAtATime = TRUE), 
                                      list(precomputeOrder = FALSE, useMaxSpanTree = TRUE, oneEdgeAtATime = FALSE), 
                                      list(precomputeOrder = FALSE, useMaxSpanTree = FALSE, oneEdgeAtATime = TRUE), 
                                      list(precomputeOrder = FALSE, useMaxSpanTree = FALSE, oneEdgeAtATime = FALSE), 
                                      list(precomputeOrder = TRUE, useMaxSpanTree = TRUE, oneEdgeAtATime = NA), 
                                      list(precomputeOrder = TRUE, useMaxSpanTree = FALSE, oneEdgeAtATime = NA))

#' 
#' @note this function implements a framework of clustering based on the spanning tree
#'       the base algorithm works as follow:
#'       1. compute the edge measure for each edge
#'       2. find the minimal (or maximal, if useMaxSpanTree is TRUE) spanning tree 
#'              according to the measure
#'       3. if precomputeOrder is TRUE, 
#'              sort the edges in MST according to edge betweenness in MST in decreasing order
#'                  and remove the edges one by one
#'          if precomputeOrder is FALSE, 
#'              find the edge (or all edges, if oneEdgeAtATime is FALSE) with maximal 
#'                  edge betweenness and remove the edge(s)
#'              if there are still edges remain, continue removeing edges
#'       4. the components after each removal give a partition
#'       5. report the partition with the highest modularity score
#' 
#' @description general framework for clustering with spanning tree (ST)
#' 
#' @param g igraph graph object. the graph to cluster on
#' 
#' @param edgeMeasure character string, or NULL. the weight to spanning tree.
#'                    if character, it must be one of the accepted string in edge_nbhd_score
#'                    if NULL, the edge weight attribute of g will be used
#'                        if g has no such attribute, uniform weight (1) will be used
#'                    default: NULL
#' 
#' @param precomputeOrder boolean. determine if the order of edges to cut is computed before cutting
#'                        if TRUE, the order is determined by the edge betweenness of the spanning tree
#'                        if FALSE, the next edge to cut is one with highest edge betweenness in the current tree
#'                        default: FALSE
#' 
#' @param useMaxSpanTree boolean. determine if maximal spanning tree should be 
#'                           used instead of minimal spanning tree
#'                       default: TRUE
#' 
#' @param oneEdgeAtATime boolean. determine if only one edge should be removed even when multiple edges are qualified
#'                       if TRUE, the edge with smallest index will be selected
#'                       ignored if precomputeOrder us TRUE
#'                       default: TRUE
#' 
#' @references K. Kulkarni, A. Pagourtzis, K. Potika, P. Potikas. 
#'             Community Detection via Neighborhood Overlap and Spanning Tree Computations
#'             doi: 10.1007/978-3-030-19759-9_2
#' 
#' @note the reference only serve as a reference as the ST algorithm presented in it
#'           uses only NOVER score for edge measure
#'       the implementation here is a modification of that algorithm
#' 
ST_clustering = function(g, edgeMeasure = NULL, precomputeOrder = FALSE, useMaxSpanTree = TRUE, oneEdgeAtATime = TRUE){
    edgeWeight = NULL
    if (!is.null(edgeMeasure)){
        edgeWeight = edge_nbhd_score(g, edgeMeasure)
        if (is.na(edgeWeight[1])){
            stop(paste("In ST_clustering, edgeMeasure =", edgeMeasure, "is not an accepted name"))
        }
    } else {
        edgeMeasure = E(g)$weight
        if (is.null(edgeMeasure)){
            edgeMeasure = rep(1, ecount(g))
        }
    }
    if (useMaxSpanTree){
        edgeWeight = -edgeWeight
    }
    gMST = mst(g, weights = edgeWeight)
    maxMembership = components(gMST)$membership
    maxQ = modularity(g, maxMembership)
    edgeOrderPtr = 0
    edgeOrder = NULL
    if (precomputeOrder){
        edgeOrder = order(edge_betweenness(gMST), decreasing = TRUE)
    }
    while (TRUE){
        cutMST = NULL
        if (precomputeOrder){
            edgeOrderPtr = edgeOrderPtr + 1
            if (edgeOrderPtr > length(edgeOrder)){
                break
            }
            cutMST = delete_edges(gMST, edgeOrder[seq_len(edgeOrderPtr)])
        } else {
            if (ecount(gMST) == 0){
                break
            }
            ebMST = edge_betweenness(gMST)
            cutMST = gMST = delete.edges(gMST, E(gMST)[
                if (oneEdgeAtATime) which.max(ebMST) 
                else which(ebMST == max(ebMST))])
        }
        thisMembership = components(cutMST)$membership
        thisQ = modularity(g, thisMembership)
        if (thisQ > maxQ){
            maxQ = thisQ
            maxMembership = thisMembership
        }
    }
    return(make_clusters(g, maxMembership, modularity = maxQ))
}

ST_clustering_measures = list(
    # instantiation of ST_clustering on edge measures starts here
    ST_clustering_hoffman = function(g){
        return(ST_clustering(g, 'hoffman', FALSE, TRUE, TRUE))
    }, 
    
    ST_clustering_maxwell = function(g){
        return(ST_clustering(g, 'maxwell', FALSE, TRUE, TRUE))
    }, 
    
    ST_clustering_phi = function(g){
        return(ST_clustering(g, 'phi', FALSE, TRUE, TRUE))
    }, 
    
    ST_clustering_rand = function(g){
        return(ST_clustering(g, 'rand', FALSE, TRUE, TRUE))
    }, 
    
    ST_clustering_kulcyznski = function(g){
        return(ST_clustering(g, 'kulcyznski', FALSE, TRUE, TRUE))
    }, 
    
    ST_clustering_preferential = function(g){
        return(ST_clustering(g, 'preferential', TRUE, TRUE, NA))
    }, 
    
    ST_clustering_jaccard = function(g){
        return(ST_clustering(g, 'jaccard', FALSE, TRUE, TRUE))
    }, 
    
    ST_clustering_nover = function(g){
        return(ST_clustering(g, 'nover', FALSE, TRUE, TRUE))
    }, 
    
    ST_clustering_novel = function(g){
        return(ST_clustering(g, 'novel', FALSE, TRUE, TRUE))
    }, 
    
    ST_clustering_invnovel = function(g){
        return(ST_clustering(g, 'invnovel', TRUE, TRUE, NA))
    }, 
    
    ST_clustering_unweighted = function(g){
        return(ST_clustering(g, 'unweighted', FALSE, TRUE, TRUE))
    }
    # instantiation of ST_clustering on edge measures ends here
)

testFunctions = list(
    #' 
    #' @description a function to test clustering algorithms
    #' 
    #' @param testGraph igraph graph object. the graph to test clustering on
    #' 
    #' @param configForST a named list, or NULL. the parameters to pass to ST_clustering
    #'                    should be one of ST_clustering_optionalPara_all
    #'                    if some optional parameter in ST_clustering is missing, 
    #'                        the default config (precomputeOrder = F, useMaxSpanTree = T, oneEdgeAtATime = T) is used
    #'                        this default config is the same as in the paper by Kulkarni et al.
    #'                    if NULL, same as all three parameters are missing
    #'                    default: NULL
    #' 
    #' @param attachPara boolean. determine of the parameters used should be attached to the test names
    #' 
    #' @return a list containing 
    #'             res, a list of igraph communities objects where each is an output of an algorithm
    #'             modularity, a numeric vector recording the outputed modularity of each algorithm
    #'             clusterCount, a integer vector containing the number of clusters each algorithm finds
    #'             ARI, a numeric matrix representing the adjusted Rand index between clusterings
    #'             NMI, a numeric matrix representing the normalized mutual infromation similarity between clusterings
    #' 
    #' @note this function loops through all edge measures with the same config
    #' 
    #' @details this function compares algorithms using different edge measures
    #'          it will test the following algorithms on testGraph: 
    #'              - unweighted_Louvain: classical Louvain, unweighted
    #'              - louvain_*: custom_weight_Louvain, classical Louvain but with given edge measure as weight
    #'              - louvain_\*_F: same as louvain_\*, but with linearNormalize = FALSE (default: TRUE)
    #'              - ST_\*: ST_clustering with different edge measures
    #'                       (the parameters needed for ST_clustering is given in configForST)
    #'          after clustering, it will compute some simple statistics based on the results:
    #'              - ARI: pairwise clustering result similarity by adjusted Rand index
    #'              - NMI: same as ARI but with normalized mutual information
    #'              - modularity: the output modularities found by each algorithm
    #'              - clusterCount: the numbers of the clusters found by each algorithm
    #'              - res: all output clusterings
    #'          also, it will plot the modularities as a bar chart
    #' 
    testFunctionOnClustering_differentMeasure = function(testGraph, configForST = NULL, attachPara = FALSE){
        if (is.null(configForST)){
            configForST = list()
        }
        ST_optionalPara_name = c('precomputeOrder', 'useMaxSpanTree', 'oneEdgeAtATime')
        ST_optionalPara_val = c(FALSE, TRUE, TRUE)
        configForST[ST_optionalPara_name] = ifelse(sapply(configForST[ST_optionalPara_name], 
                                                          is.null), 
                                                   ST_optionalPara_val, 
                                                   configForST[ST_optionalPara_name])
        resCommObj = list(unweighted_Louvain = cluster_louvain(testGraph, NA))
        resCommObj[paste('louvain', 
                         edge_nbhd_score_measure_list, 
                         sep = '_')] = lapply(edge_nbhd_score_measure_list, 
                                              function(measureName)custom_weight_Louvain(testGraph, measureName))
        resCommObj[paste('louvain', 
                         edge_nbhd_score_measure_list, 
                         'F',
                         sep = '_')] = lapply(edge_nbhd_score_measure_list, 
                                              function(measureName)custom_weight_Louvain(testGraph, measureName, F))
        configName = ''
        if (attachPara){
            configName = paste(names(configForST), configForST, collapse = '_', sep = '=')
        }
        resCommObj[paste('ST',
                         edge_nbhd_score_measure_list,
                         configName,
                         sep = '_')] = lapply(edge_nbhd_score_measure_list,
                                              function(measureName)do.call(ST_clustering,
                                                                           c(list(g = testGraph,
                                                                                  edgeMeasure = measureName),
                                                                             configForST)))
        n = length(resCommObj)
        ARIMatrix = matrix(0, n, n, dimnames = list(names(resCommObj), names(resCommObj)))
        NMIMatrix = matrix(0, n, n, dimnames = list(names(resCommObj), names(resCommObj)))
        idxToCompute = combn(n, 2)
        for (idx in seq_len(ncol(idxToCompute))){
            ARIMatrix[idxToCompute[1, idx], 
                      idxToCompute[2, idx]] = adjusted_Rand_index(resCommObj[[idxToCompute[1, idx]]], 
                                                                  resCommObj[[idxToCompute[2, idx]]])
            NMIMatrix[idxToCompute[1, idx], 
                      idxToCompute[2, idx]] = clustering_NMI_similarity(resCommObj[[idxToCompute[1, idx]]], 
                                                                        resCommObj[[idxToCompute[2, idx]]])
        }
        ARIMatrix = ARIMatrix + t(ARIMatrix)
        NMIMatrix = NMIMatrix + t(NMIMatrix)
        diag(ARIMatrix) = 1
        diag(NMIMatrix) = 1
        modu = sapply(resCommObj, function(comm)max(comm$modularity))
        origParMai = par("mai")
        par(mai = c(1, 2, 1, 1))
        barplot(modu, horiz = TRUE, las = 1)
        par(mai = origParMai)
        return(list(res = resCommObj, 
                    modularity = modu, 
                    clusterCount = sapply(resCommObj, function(comm)max(comm$membership)), 
                    ARI = ARIMatrix, 
                    NMI = NMIMatrix))
    }, 
    
    #' 
    #' @description a function to test clustering algorithms
    #' 
    #' @param testGraph igraph graph object. the graph to test clustering on
    #' 
    #' @param measureName character string. the name of the edge measure used
    #'                    should be one of edge_nbhd_score_measure_list
    #' 
    #' @return a list containing 
    #'             res, a list of igraph communities objects where each is an output of an algorithm
    #'             modularity, a numeric vector recording the outputed modularity of each algorithm
    #'             clusterCount, a integer vector containing the number of clusters each algorithm finds
    #'             ARI, a numeric matrix representing the adjusted Rand index between clusterings
    #'             NMI, a numeric matrix representing the normalized mutual infromation similarity between clusterings
    #' 
    #' @note this function loops through all configuations for ST_clustering with the same edge measure
    #' 
    #' @details this function compares different config for ST_clustering with given edge measure
    #'          it will test all configs in ST_clustering_optionalPara_all on testGraph
    #'          like testFunctionOnClustering_differentMeasure, it will compute the same set of statistics
    #'          it will not plot the bar chart
    #' 
    testFunctionOnClustering_differentSTConfig = function(testGraph, measureName){
        if (is.directed(testGraph)){
            testGraph = as.undirected(testGraph)
        }
        resCommObj = list(unweighted_Louvain = cluster_louvain(testGraph, NA))
        resCommObj[[paste(measureName, T, sep = '_')]] = custom_weight_Louvain(testGraph, measureName, TRUE)
        resCommObj[[paste(measureName, F, sep = '_')]] = custom_weight_Louvain(testGraph, measureName, FALSE)
        resCommObj[paste(measureName, 
                         sapply(ST_clustering_optionalPara_all, 
                                function(configs)paste(configs, 
                                                       collapse = '_')), 
                         sep = '_')] = lapply(ST_clustering_optionalPara_all, 
                                              function(configs)do.call(ST_clustering, 
                                                                       c(list(g = testGraph, edgeMeasure = measureName), 
                                                                         configs)))
        n = length(resCommObj)
        ARIMatrix = matrix(0, n, n, dimnames = list(names(resCommObj), names(resCommObj)))
        NMIMatrix = matrix(0, n, n, dimnames = list(names(resCommObj), names(resCommObj)))
        idxToCompute = combn(n, 2)
        for (idx in seq_len(ncol(idxToCompute))){
            ARIMatrix[idxToCompute[1, idx], 
                      idxToCompute[2, idx]] = adjusted_Rand_index(resCommObj[[idxToCompute[1, idx]]], 
                                                                  resCommObj[[idxToCompute[2, idx]]])
            NMIMatrix[idxToCompute[1, idx], 
                      idxToCompute[2, idx]] = clustering_NMI_similarity(resCommObj[[idxToCompute[1, idx]]], 
                                                                        resCommObj[[idxToCompute[2, idx]]])
        }
        ARIMatrix = ARIMatrix + t(ARIMatrix)
        NMIMatrix = NMIMatrix + t(NMIMatrix)
        diag(ARIMatrix) = 1
        diag(NMIMatrix) = 1
        return(list(res = resCommObj, 
                    modularity = sapply(resCommObj, function(comm)max(comm$modularity)), 
                    clusterCount = sapply(resCommObj, function(comm)max(comm$membership)), 
                    ARI = ARIMatrix, 
                    NMI = NMIMatrix))
    }, 
    
    #' 
    #' @description a function to test clustering algorithms
    #' 
    #' @param testGraph igraph graph object. the graph to test clustering on
    #' 
    #' @param clusteringFuncList a list of functions. the algorithm to be tested
    #'                           each function should take only one argument, the input graph
    #'                           since this parameter is parsed to generated names, 
    #'                               all function passing in should be wrapped as a single variable function, 
    #'                               if it requires more parameters
    #' 
    #' @return a list containing 
    #'             res, a list of igraph communities objects where each is an output of an algorithm
    #'             modularity, a numeric vector recording the outputed modularity of each algorithm
    #'             clusterCount, a integer vector containing the number of clusters each algorithm finds
    #'             ARI, a numeric matrix representing the adjusted Rand index between clusterings
    #'             NMI, a numeric matrix representing the normalized mutual infromation similarity between clusterings
    #' 
    #' @note this function loops through all functions in clusteringFuncList
    #' 
    #' @details this function compares the results of different algorithms
    #'          it will test all functions in clusteringFuncList on testGraph
    #'          like testFunctionOnClustering_differentMeasure, it will compute the same set of statistics
    #'          it will not plot the bar chart
    #' 
    testFunctionOnClustering_givenFunction = function(testGraph, clusteringFuncList){
        if (is.directed(testGraph)){
            testGraph = as.undirected(testGraph)
        }
        resCommObj = list()
        n = length(clusteringFuncList)
        for (i in seq_len(n)){
            resCommObj[[as.character(substitute(clusteringFuncList)[i + 1])]] = clusteringFuncList[[i]](testGraph)
        }
        if (n == 1){
            return(list(res = resCommObj, 
                        modularity = max(resCommObj[[1]]$modularity), 
                        clusterCount = max(resCommObj[[1]]$membership)))
        }
        ARIMatrix = matrix(0, n, n, dimnames = list(names(resCommObj), names(resCommObj)))
        NMIMatrix = matrix(0, n, n, dimnames = list(names(resCommObj), names(resCommObj)))
        idxToCompute = combn(n, 2)
        for (idx in seq_len(ncol(idxToCompute))){
            ARIMatrix[idxToCompute[1, idx], 
                      idxToCompute[2, idx]] = adjusted_Rand_index(resCommObj[[idxToCompute[1, idx]]], 
                                                                  resCommObj[[idxToCompute[2, idx]]])
            NMIMatrix[idxToCompute[1, idx], 
                      idxToCompute[2, idx]] = clustering_NMI_similarity(resCommObj[[idxToCompute[1, idx]]], 
                                                                        resCommObj[[idxToCompute[2, idx]]])
        }
        ARIMatrix = ARIMatrix + t(ARIMatrix)
        NMIMatrix = NMIMatrix + t(NMIMatrix)
        diag(ARIMatrix) = 1
        diag(NMIMatrix) = 1
        return(list(res = resCommObj, 
                    modularity = sapply(resCommObj, function(comm)max(comm$modularity)), 
                    modOrder = as.character(
                        substitute(clusteringFuncList)[-1][order(
                            sapply(resCommObj, 
                                   function(comm)max(comm$modularity)), 
                            decreasing = T)]), 
                    clusterCount = sapply(resCommObj, function(comm)max(comm$membership)), 
                    ARI = ARIMatrix, 
                    NMI = NMIMatrix))
    }
)


#' 
#' @description compute the mean clique disparity
#' 
#' @param distG igraph graph object. the graph to compute on. 
#'              assumed to have edge attribute "weight". higher weight should mean higher disparity
#' 
#' @param listOfCliqueVertices list of integer vectors or igraph vertex sequences, or integer vector
#'                             the list of cliques represented as the vertex indices in the clique
#'                             if it is integer vector, the whole vector is seen as one clique
#'                             default: cliques(distG, 4, 4)
#' 
#' @param forceSparse boolean. Determine if sparse matrix should be used in computation
#'                    if FALSE, will fall back to default setting (igraph_opt("sparsematrices"))
#'                    default: FALSE
#' 
#' @return numeric vector representing the mean disparity for each clique
#' 
#' @references M. A. Balci, O. Akguller, S. C. Guzel. 
#'             Hierarchies in communities of UK stock market from the perspective of Brexit
#'             doi: 10.1080/02664763.2020.1796942
#' 
mean_clique_disparity = function(distG, listOfCliqueVertices = cliques(distG, 4, 4), forceSparse = FALSE){
    adjMatrix = as_adjacency_matrix(distG, 
                                    attr = 'weight', 
                                    sparse = forceSparse || igraph_opt("sparsematrices"))
    if (is.atomic(listOfCliqueVertices)){
        listOfCliqueVertices = list(listOfCliqueVertices)
    }
    if (class(listOfCliqueVertices[[1]]) == 'igraph.vs'){
        listOfCliqueVertices = lapply(listOfCliqueVertices, as.integer)
    }
    print(paste("number of cliques:", length(listOfCliqueVertices)))
    yi = lapply(listOfCliqueVertices, 
                function(cliq){
                    cliqDistMatrix = adjMatrix[cliq, cliq]
                    cliqDistMatrix[cliqDistMatrix == 0] = Inf # in case not clique
                    diag(cliqDistMatrix) = 0
                    return(Matrix::rowSums(cliqDistMatrix^2) / Matrix::rowSums(cliqDistMatrix)^2)
                })
    return(sapply(yi, mean))
}

#' 
#' @description compute the 4-clique intra-connectedness of clusters
#' 
#' @param g igraph graph object. the graph to check on
#'          assumed the weight edge attr means distance
#' 
#' @param clusterMemberVect integer vector, or igraph communities object
#'                          the clustering to look at
#'                          if integer vector, it should record the indices of the clusters the vertices belong to
#'                          if communities, it should be a clustering on the graph g
#'                          default: rep(1, vcount(g)) (all vertices in one cluster)
#' 
#' @return a list of 3 numeric vectors (c4, ns, ratio)
#'         c4 is an integer vector representing the number of 4-cliques in each cluster
#'         ns is the number of vertices in the clusters minus 3
#'         ratio is the ratio between c4 and ns
#' 
#' @references M. A. Balci, O. Akguller, S. C. Guzel. 
#'             Hierarchies in communities of UK stock market from the perspective of Brexit
#'             doi: 10.1080/02664763.2020.1796942
#' 
fourCliqueRatio = function(g, clusterMemberVect = rep(1, vcount(g))){
    if (class(clusterMemberVect) == 'communities'){
        clusterMemberVect = clusterMemberVect$membership
    }
    commList = commListFromMembership(clusterMemberVect)
    commSubgraphs = lapply(commList, function(comm)induced_subgraph(g, comm))
    vectFourCliqueCount = sapply(commSubgraphs, function(subG)length(cliques(subG, 4, 4)))
    vectNs = sapply(commList, length)
    return(list(c4 = vectFourCliqueCount, 
                ns = vectNs, 
                ratio = vectFourCliqueCount / (vectNs - 3)))
}

#' 
#' @description compute similarity between clusters
#' 
#' @param listOfComm list of igraph communties objects. the list to be processed
#' 
#' @param clusterSimFunc function. the function used to compute similarity
#'                       it should take two communities as input and returns a numeric
#'                       assumed symmetric and return 1 when two inputs are identical
#' 
#' @return a numeric matrix of size nxn, where n is the length of listOfComm
#'         entry (i,j) is the similarity between community i and j
#'         symmetric and 1-diagonal
#' 
batch_sim = function(listOfComm, clusterSimFunc){
    n = length(listOfComm)
    if (n <= 1){
        return(1)
    }
    res = matrix(0, n, n)
    idxToCompute = combn(n, 2)
    for (idx in seq_len(ncol(idxToCompute))){
        res[idxToCompute[1, idx], 
            idxToCompute[2, idx]] = clusterSimFunc(listOfComm[[idxToCompute[1, idx]]], 
                                                   listOfComm[[idxToCompute[2, idx]]])
    }
    res = res + t(res)
    diag(res) = 1
    return(res)
}

#'
#' @description extraction info from belonging coefficients
#' 
#' @param belongingMatrix a numeric matrix. 
#'                        the belonging coefficients of each vertex
#'                        belongingMatrix[vertexID, communityID] is 
#'                            the belonging coefficient of vertexID in communityID
#'                        alternatively, a named list with names "modularity" and "belongingCoeff"
#'                            in this case, the named component "belongingCoeff" will be used
#' 
#' @param queryTarget NULL, or a string containing the name of the return object
#'                    if it is a string, it must be one of
#'                        vertexCount, communityCount, belongingMatrix, communityMembers, communitySize, vertexClass, overlappedVertex
#' 
#' @return a list containing the following information:
#'             vertexCount: the total number of vertices included
#'             communityCount: the total number of communities detected
#'             belongingMatrix: the belonging coefficients of each vertex, the input matrix
#'             communityMembers: the vertices which has nonzero belonging coefficient in the community
#'             communitySize: the sices of the communities
#'             vertexClass: the communities each vertex belongs to with nonzero belonging coefficient
#'             overlappedVertex: the vertices that are contained in more than one communities
#'         if queryTarget is not NULL and match one of the names above, 
#'             only the corresponding object is returned
#' 
overlapCommInfo = function(belongingMatrix, queryTarget = NULL){
    # TODO reduce usage of if
    if (!is.null(names(belongingMatrix)) && all(names(belongingMatrix) == c("modularity", "belongingCoeff"))){
        # input directly from overlapping clustering output and not stripped
        belongingMatrix = belongingMatrix[["belongingCoeff"]]
    }
    if (is.null(queryTarget)){ # temp
        queryTarget = ""
    }
    if (queryTarget == "belongingMatrix"){ # why though
        return(belongingMatrix)
    }
    vertexCount = nrow(belongingMatrix)
    if (queryTarget == "vertexCount"){
        return(vertexCount)
    }
    communityCount = ncol(belongingMatrix)
    if (queryTarget == "communityCount"){
        return(communityCount)
    }
    vertexClass = apply(belongingMatrix, 1, function(colByComm)which(colByComm != 0))
    if (queryTarget == "vertexClass"){
        return(vertexClass)
    }
    communityMembers = apply(belongingMatrix, 2, function(rowByVertex)which(rowByVertex != 0))
    if (queryTarget == "communityMembers"){
        return(communityMembers)
    }
    communitySize = sapply(communityMembers, length)
    if (queryTarget == "communitySize"){
        return(communitySize)
    }
    overlappedVertex = which(sapply(vertexClass, length) >= 2)
    if (queryTarget == "overlappedVertex"){
        return(overlappedVertex)
    }
    return(list(vertexCount = vertexCount, 
                communityCount = communityCount, 
                belongingMatrix = belongingMatrix, 
                communityMembers = communityMembers, 
                communitySize = communitySize, 
                vertexClass = vertexClass, 
                overlappedVertex = overlappedVertex))
}

#' 
#' @description Compute modularity for overlapping communities
#' 
#' @param g igraph graph object. the graph to cluster on. assumed unweighted undirected simple
#' 
#' @param belongingVectList a list of numeric vectors. 
#'                          each vector is the normalized belonging vector of the vertex
#'                          all vectors must have the same length
#' 
#' @param edgeBelongingCoeffFunc a function that takes two numerics and return a numeric
#'                               the function to compute the belonging coefficient of an edge
#'                               the inputs are the belonging coefficients of the endpoints 
#'                                   in a fixed community
#'                               default: prod
#' 
#' @return a numeric representing the overlapping modularity
#' 
#' @references V. Nicosia, G. Mangioni, V. Carchiolo, M. Malgeri.
#'             Extending the definition of modularity to directed graphs with overlapping communities
#'             doi: 10.1088/1742-5468/2009/03/P03024
#' 
# TODO use matrix rather than vect list
#
overlapping_modularity = function(g, belongingVectList, edgeBelongingCoeffFunc = prod){
    m = ecount(g)
    vCount = vcount(g)
    cCount = length(belongingVectList[[1]])
    if (cCount == 1){
        return(0)
    }
    degreeVect = degree(g)
    adjMatrix = as_adjacency_matrix(g)
    # FMatrix[[cIdx]][i, j] = edgeBelongingCoeffFunc(belongingVectList[[i]][cIdx], belongingVectList[[j]][cIdx])
    FMatrix = lapply(seq_len(cCount), 
                     function(cIdx){
                         outer(seq_len(vCount), 
                               seq_len(vCount), 
                               Vectorize(function(i, j){
                                   edgeBelongingCoeffFunc(belongingVectList[[i]][cIdx], 
                                                          belongingVectList[[j]][cIdx])
                               }))
                     }) # better approach?
    r = Reduce("+", FMatrix) # r[i, j] = (sum_c FMatrix[[c]])[i, j]
    s = Reduce(function(a, b) a + b %*% b, FMatrix) / (vCount ^ 2) # s[i, j] = sum_c MatrixPower(FMatrix[[c]], 2)[i, j]
    K = outer(degreeVect, degreeVect) # K[i, j] = deg(g, i) * deg(g, j)
    return(sum(r * adjMatrix - s * K / (2 * m)) / (2 * m))
}

#' 
#' @description compute belonging coefficient vectors from list of communities
#' 
#' @param communitiesList a list of integer vectors, each represents the members of a community
#'                        assumed no missing values, i.e. when unlisted is a permutation of continuous sequence of intergers
#' 
#' @return a list of length as the total number of nodes of numeric vectors, 
#'             each represents the belonging coefficients in communities of a vertex
#' 
#' @note the belonging coefficient is computed with uniform weight in each involving community
#' 
belongCoeffVectFromCommList = function(communitiesList){
    cCount = length(communitiesList)
    m = max(unlist(communitiesList))
    belongCoeffMatrix = matrix(0, cCount, m)
    for (commPtr in seq_len(cCount)){
        belongCoeffMatrix[commPtr, communitiesList[[commPtr]]] = belongCoeffMatrix[commPtr, communitiesList[[commPtr]]] + 1
    }
    return(split(t(t(belongCoeffMatrix) / colSums(belongCoeffMatrix)), 
                 rep(seq_len(m), 
                     each = cCount)))
}

#' 
#' @description compute the belonging coefficient matrix from vector list
#' 
#' @param belongVectList a list of equal length numeric vectors representing the belonging coefficients
#' 
#' @return a matrix recording the belonging coefficients where return[vID, cID] is 
#'             the belonging coefficient of vertex vID in community cID
#' 
#' @note a transformation on list of equal length numeric vectors into matrix
#' 
belongCoeffMatrixFromVectList = function(belongVectList){
    return(matrix(unlist(belongVectList), 
                  length(belongVectList), 
                  byrow = TRUE))
}

#' 
#' @description split the belonging coefficient matrix into vectors
#' 
#' @param belongMatrix a numeric matrix. the belonging matrix
#' 
#' @return a list of numeric vectors representing the belonging coefficients. 
#'         return[[vID]][cID] = belongMatrix[vID, cID]
#' 
#' @note a transformation that splits matrix by rows
#' 
belongVectListFromMatrix = function(belongMatrix){
    return(split(t(belongMatrix), 
                 rep(seq_len(nrow(belongMatrix)), 
                     each = ncol(belongMatrix))))
}

#' 
#' @description compute the split betweenness of a vertex
#' 
#' @param gForest igraph graph object. the graph in question. assumed to be a forset, unweighted and undirected
#' 
#' @param v the vertex to compute split betweenness. 
#'          default: V(gForest), all vertex
#' 
#' @param returnPartition boolean. Determine if the corresponding partition is also returned
#'                        the partition is returned as a numeric vector which contains  
#'                            the sizes of branches in one side
#'                        default: FALSE
#' 
#' @return a numeric vector with the same length as v, representing the split betweeness
#'         the split betweenness of a vertex is the maximal edge betweenness of 
#'             the new edge added when the vertex is replaced with a pair of vertices
#'             connected with an edge, among all possible partition of neighbours
#'         for tree node, the split betweenness is found by the partition with nearest difference
#' 
#' @references A. Pagourtzis, D. Souliou, P. Potikas, K. Potikas. 
#'             Overlapping Community Detection via Minimum Spanning Tree Computations
#'             doi: 10.1109/BigDataService49289.2020.00017
#' 
split_betweenness_forest = function(gForest, v = V(gForest), returnPartition = FALSE){
    result = lapply(v, function(vid){
        # get connected component of vid
        # verticesToKeep = na.exclude(dfs(gForest, vid, unreachable = FALSE)$order)
        verticesToKeep = getComponentMembers(gForest, vid)
        vid = match(vid, sort(verticesToKeep)) # update vid in g
        g = induced_subgraph(gForest, verticesToKeep)
        branchSize = components(g - vid)$csize # size of branches connected to vid
        branchCount = length(branchSize)
        if (branchCount == 0){ # no branch, isolated vertex
            if (returnPartition){
                return(list(val = 1, partition = NULL, altPartition = NULL))
            } else {
                return(1)
            }
        }
        if (branchCount == 1){ # single branch, c(a), return a+1
            if (returnPartition){
                return(list(val = branchSize + 1, partition = branchSize, altPartition = NULL))
            } else {
                return(branchSize + 1)
            }
        }
        if (branchCount == 2){ # 2 branches, c(a, b), return ab+a+b+1
            if (returnPartition){
                return(list(val = prod(branchSize) + sum(branchSize) + 1, 
                            partition = branchSize[1], 
                            altPartition = branchSize[2]))
            } else {
                return(prod(branchSize) + sum(branchSize) + 1)
            }
        }
        # now has at least 3 branches, branchCount >= 3
        # find nearest partition difference with DP
        maxSum = vcount(g) - 1
        # the commented part only finds if the partition is possible, not how
        # dpTable = matrix(FALSE, 2, maxSum + 1) # [0, maxSum]
        # currentRow = 1
        # dpTable[currentRow, branchSize[1] + 1] = TRUE
        # for (rowIndex in 2:branchCount){
        #     for (targetSum in 0:maxSum){
        #         dpTable[3 - currentRow, targetSum + 1] = 
        #             (if (targetSum + branchSize[rowIndex] <= maxSum) 
        #                 dpTable[currentRow, targetSum + branchSize[rowIndex] + 1] 
        #              else FALSE) || dpTable[currentRow, abs(targetSum - branchSize[rowIndex]) + 1]
        #     }
        #     currentRow = 3 - currentRow
        # }
        # minSum = match(TRUE, dpTable[currentRow, ]) - 1
        dpTable = replicate(2, replicate(maxSum + 1, NULL))
        currentRow = 1
        dpTable[[branchSize[1] + 1, currentRow]] = c(branchSize[1])
        for (rowIndex in 2:branchCount){
            # for (targetSum in 0:maxSum){
            #     newVect = NULL
            #     isByAdd = FALSE
            #     # select only one approach
            #     if (targetSum + branchSize[rowIndex] <= maxSum # ob check necessary?
            #         && !is.null(dpTable[[targetSum + branchSize[rowIndex] + 1, currentRow]])){
            #         # get targetSum by decreasing difference
            #         newVect = dpTable[[targetSum + branchSize[rowIndex] + 1, currentRow]]
            #         isByAdd = TRUE
            #     } else if (!is.null(dpTable[[abs(targetSum - branchSize[rowIndex]) + 1, currentRow]])){
            #         # get targetSum by increasing difference
            #         newVect = dpTable[[abs(targetSum - branchSize[rowIndex]) + 1, currentRow]]
            #     }
            #     if (!is.null(newVect)){
            #         dpTable[[targetSum + 1, 3 - currentRow]] = c(newVect, (-1)^isByAdd * branchSize[rowIndex])
            #     }
            # }
            for (origSum in 0:maxSum){
                currentPartition = dpTable[[origSum + 1, currentRow]]
                if (is.null(currentPartition)){
                    # cannot achieve origSum
                    next
                }
                if (origSum + branchSize[rowIndex] <= maxSum 
                    && is.null(dpTable[[origSum + branchSize[rowIndex] + 1, 3 - currentRow]])){
                    # add to larger set
                    dpTable[[origSum + branchSize[rowIndex] + 1, 3 - currentRow]] = c(currentPartition, branchSize[rowIndex])
                }
                if (is.null(dpTable[[abs(origSum - branchSize[rowIndex]) + 1, 3 - currentRow]])){
                    # add to smaller set
                    dpTable[[abs(origSum - branchSize[rowIndex]) + 1, 3 - currentRow]] = c(currentPartition, -branchSize[rowIndex])
                }
            }
            currentRow = 3 - currentRow
        }
        minSum = match(FALSE, sapply(dpTable[, currentRow], is.null)) - 1
        sbVal = (maxSum + minSum + 2) * (maxSum - minSum + 2) / 4
        # reconstruct partition
        minPartitionInstruction = dpTable[[minSum + 1, currentRow]]
        minPartition = NULL
        setSum = c(0, 0)
        for (idx in seq_along(minPartitionInstruction)){
            addToIdx = (if (minPartitionInstruction[idx] > 0) which.max else which.min)(setSum)
            setSum[addToIdx] = setSum[addToIdx] + abs(minPartitionInstruction[idx])
            minPartition[idx] = addToIdx
        }
        # minPartition = abs(minPartitionInstruction[which(minPartition == 1)])
        if (returnPartition){
            return(list(val = sbVal, 
                        partition = abs(minPartitionInstruction[which(minPartition == 1)]), 
                        altPartition = abs(minPartitionInstruction[which(minPartition == 2)])))
        } else {
            return(sbVal)
        }
    })
    if (is.list(result[[1]])){ # returnPartition == T
        return(result)
    } else {
        return(unlist(result))
    }
}

#' 
#' @description clustering with Spanning Tree clustering with Overlapping communities 
#' 
#' @param g igraph graph object. the graph to cluster on. unweighted and undirected
#'
#' @param edgeBelongingCoeffFunc a function that takes two numerics and return a numeric
#'                               the function to compute the belonging coefficient of an edge
#'                               the inputs are the belonging coefficients of the endpoints 
#'                                   in a fixed community
#'                               default: prod
#' 
#' @param mstWeightFunc a function that takes a graph and compute a numeric for each edge, 
#'                        or a string in edge_nbhd_score_measure_list
#'                      the weight function to compute the MST from
#'                      higher value means larger distance
#'                      default: NOVER_score
#' 
#' @return a matrix of belonging coefficients representing how the communities are defined, 
#'         along with the overlapping modularity
#'         entry at [vertexID, communityID] is the belonging coefficient of vertexID in communityID
#' 
#' @references A. Pagourtzis, D. Souliou, P. Potikas, K. Potikas. 
#'             Overlapping Community Detection via Minimum Spanning Tree Computations
#'             doi: 10.1109/BigDataService49289.2020.00017
#' 
#' @note for splitting vertices, the partition of branch splitting is chosen arbitrarily
#'           but deterministically(?), in that the selection is chosen by other functions
#'       TODO: make this random
#' 
OST_clustering = function(g, edgeBelongingCoeffFunc = prod, mstWeightFunc = NOVER_score, debugVerboseLevel = 0){
    computedLayout = layout.auto(g)
    if (is.character(mstWeightFunc) && mstWeightFunc %in% edge_nbhd_score_measure_list){
        # bodge to avoid recursive reference
        targetMeasureName = mstWeightFunc
        mstWeightFunc = function(gInput)edge_nbhd_score(gInput, measure = targetMeasureName)
    }
    vc = vcount(g)
    E(g)$weight = mstWeightFunc(g)
    gMST = delete_edge_attr(mst(g, E(g)$weight), "weight")
    # V(gMST)$realID = seq_along(V(gMST))
    V(gMST)$realID = seq_len(vc)
    # Cov = replicate(vcount(g), c(1), simplify = FALSE)
    currentVC = vc
    Cov = as.list(rep(1, currentVC))
    Qov = 0
    loopCounter = 0
    while (ecount(gMST) != 0){
        loopCounter = loopCounter + 1
        if (debugVerboseLevel >= 1){
            print(paste("loop", loopCounter, 
                        "ecount", ecount(gMST), 
                        "vcount", vcount(gMST)))
            if (debugVerboseLevel >= 3){
                plot_tree(gMST)
            }
        }
        E(gMST)$eb = edge.betweenness(gMST) # igraph::edge.betweenness is still fast on tree
        maxeb = max(E(gMST)$eb)
        sbRes = split_betweenness_forest(gMST, returnPartition = TRUE)
        V(gMST)$sb = sapply(sbRes, function(x)x$val)
        maxsb = max(V(gMST)$sb)
        if (maxsb < maxeb){
            # rm edge
            edgeToRemove = which.max(E(gMST)$eb)
            if (debugVerboseLevel >= 1){
                print(paste("remove edge", edgeToRemove))
            }
            gMST = delete.edges(gMST, edgeToRemove)
        } else if (all(components(gMST)$csize %in% c(1, 2))){ # only add a new vertex
            break
        } else {
            if (debugVerboseLevel >= 1){
                print(paste("max component size:", max(components(gMST)$csize)))
            }
            vertexToSplit = which.max(V(gMST)$sb)
            if (debugVerboseLevel >= 1){
                print(paste("split vertex id", vertexToSplit, 
                            "sb: ", V(gMST)$sb[vertexToSplit]))
            }
            nbhdPartitionForSB = sbRes[[vertexToSplit]]$partition
            # special cases?
            # find nb partition
            vertexNb = neighbors(gMST, vertexToSplit)
            # branchSizes = sapply(vertexNb, function(nbVID){
            #     length(na.exclude(dfs(delete.edges(gMST, 
            #                                        gMST[vertexToSplit, 
            #                                             nbVID, 
            #                                             edges = TRUE]), 
            #                           nbVID, 
            #                           unreachable = FALSE)$order))
            # })
            branchSizes = sapply(vertexNb, function(nbVID){
                getComponentSize(delete.edges(gMST, 
                                              gMST[vertexToSplit, 
                                                   nbVID, 
                                                   edges = TRUE]), 
                                 nbVID)
            })
            nbVIDToSplit = rep(NA, length(nbhdPartitionForSB))
            for (idx in seq_along(nbhdPartitionForSB)){
                matchIdx = match(nbhdPartitionForSB[idx], branchSizes)
                nbVIDToSplit[idx] = vertexNb[matchIdx]
                branchSizes[matchIdx] = NA
            }
            # split vertex
            gMST = add.vertices(gMST, 1, realID = V(gMST)$realID[vertexToSplit])
            currentVC = currentVC + 1
            # newVertexID = vcount(gMST)
            newVertexID = currentVC
            gMST[from = rep(newVertexID, length(nbVIDToSplit)), 
                 to = nbVIDToSplit] = TRUE
            gMST[from = rep(vertexToSplit, length(nbVIDToSplit)), 
                 to = nbVIDToSplit] = FALSE
        }
        gMSTComp = components(gMST)
        totalComm = gMSTComp$no
        gMSTComp = gMSTComp$membership
        CovPrime = replicate(vc, rep(0, totalComm), simplify = FALSE)
        for (vidx in seq_along(gMSTComp)){
            realID = V(gMST)$realID[vidx]
            CovPrime[[realID]][gMSTComp[vidx]] = CovPrime[[realID]][gMSTComp[vidx]] + 1
        }
        CovPrime = lapply(CovPrime, function(belongingVect)belongingVect / sum(belongingVect))
        QovPrime = overlapping_modularity(g, CovPrime, edgeBelongingCoeffFunc)
        if (debugVerboseLevel >= 1){
            print(paste(QovPrime, Qov))
            if (debugVerboseLevel >= 2){
                plot_overlapComm(g, belongCoeffMatrixFromVectList(CovPrime), layout = computedLayout)
            }
        }
        if (QovPrime > Qov){
            Qov = QovPrime
            Cov = CovPrime
        }
    }
    return(list(modularity = Qov, 
                belongingCoeff = belongCoeffMatrixFromVectList(Cov)))
}

#'
#' @description compute the split betweenness of vertices and split by greedy heuristic
#'
#' @param g igraph graph object. Assumed to be undirected unweighted simple
#'
#' @param vs igraph vertex sequence of g. vertices to compute
#'           default: V(g)
#'
#' @return a list of length same as v of lists that each contains
#'             splitBetweenness: a numeric that representing the split betweenness
#'             splitting: a list of length 2 that contains the vertex IDs of the split
#'
#' @references S. Gregory
#'             An Algorithm to find Overlapping Community Structure in Networks
#'             doi: 10.1007/978-3-540-74976-9_12
#' 
#' @references https://github.com/GiulioRossetti/cdlib/blob/master/cdlib/algorithms/internal/CONGA.py
#'
#' @note this function is computed by definition without the edge betweenness
#'           overhead and so is slower
#' 
#' @note when the relevant part of the graph is a forest, use split_betweenness_forest instead
#'
split_betweenness_greedy = function(g, vs = V(g)){
    # compute pair betweenness dict by brute force all shortest path
    vcg = vcount(g)
    # overhead
    print("finding relevent vertices")
    pairBetweennessDict = replicate(vcg, 
                                    Matrix::Matrix(0, vcg, vcg, 
                                                   sparse = TRUE))
    compoMembership = components(g)
    compoMembers = replicate(compoMembership$no, NULL)
    compoMembership = compoMembership$membership
    for (compID in unique(compoMembership[vs])){
        compoMembers[[compID]] = which(compoMembership == compID)
    }
    # use *_forest better performance
    if (is.forest(induced.subgraph(g, unlist(compoMembers)))){
        print("relevent vertices form forest")
        res = split_betweenness_forest(g, vs, TRUE)
        # post-process: split_betweenness_forest returns only size of branches
        return(lapply(seq_along(vs), function(vsIdx){
            x = res[[vsIdx]]
            v = vs[[vsIdx]]
            nei = neighbors(g, v)
            puncturedG = delete.vertices(g, v)
            branchSizes = sapply(as.integer(nei), 
                                 function(nVID)getComponentSize(puncturedG, 
                                                                nVID - (nVID > v)))
            partitionIdx = rep(NA, length(x$partition))
            for (ptr in seq_along(partitionIdx)){
                partitionIdx[ptr] = match(x$partition[ptr], branchSizes)
                branchSizes[partitionIdx[ptr]] = NA
            }
            return(list(splitBetweenness = x$val, 
                        splitting = list(as.integer(nei[partitionIdx]), 
                                         as.integer(nei[-partitionIdx]))))
        }))
    }
    print("computing pairDict")
    for (comp in compoMembers[sapply(compoMembers, length) >= 3]){
        for (idx in seq_along(comp[-1])){
            shortestPathList = Filter(function(p)length(p) >= 3, 
                                      all_shortest_paths(g, 
                                                         from = comp[idx], 
                                                         to = comp[-seq_len(idx)])$res)
            for (p in shortestPathList){
                for (ptr in 2:(length(p) - 1)){
                    uu = min(p[ptr + c(-1, 1)])
                    ww = max(p[ptr + c(-1, 1)])
                    pairBetweennessDict[[p[ptr]]][uu, ww] = pairBetweennessDict[[p[ptr]]][uu, ww] + 1
                }
            }
        }
    }
    gTemplate = make_empty_graph(vcg, directed = FALSE)
    V(gTemplate)$realName = seq_len(vcg)
    # estimate split betweeenness and split by greedy
    print("computing split")
    return(lapply(vs, function(vid){
        # special case: less than 2 neighbours
        if (all(pairBetweennessDict[[vid]] == 0)){
            # return(list(splitBetweenness = length(na.exclude(dfs(g, 
            #                                                      vid, 
            #                                                      unreachable = FALSE)$order)), 
            #             splitting = list(as.integer(neighbors(g, vid)), 
            #                              integer(0))))
            return(list(splitBetweenness = getComponentSize(g, vid), 
                        splitting = list(as.integer(neighbors(g, vid)), 
                                         integer(0))))
        }
        gCopy = gTemplate # should be deep copy
        # init score
        pairBetInd = Matrix::which(pairBetweennessDict[[vid]] != 0, 
                                   arr.ind = TRUE)
        gCopy[from = pairBetInd[, "row"], 
              to = pairBetInd[, "col"], 
              attr = "score"] = pairBetweennessDict[[vid]][pairBetInd]
        gCopy = delete.vertices(gCopy, degree(gCopy) == 0) # rm irrelevent vertices
        # TODO optimize gCopy construction
        # loop to contract vertex
        while (ecount(gCopy) > 1){
            edgeIDToContract = which.min(E(gCopy)$score)
            endPts = as.vector(ends(gCopy, 
                                    edgeIDToContract, 
                                    names = FALSE))
            vcgCopy = vcount(gCopy)
            gCopy = add.vertices(gCopy, 
                                 1, 
                                 realName = list(sort(unlist(V(gCopy)$realName[endPts]))))
            gCopy[seq_len(vcgCopy), 
                  vcount(gCopy), 
                  attr = "score"] = Matrix::rowSums(gCopy[seq_len(vcgCopy), endPts]) # could be sparse
            gCopy = delete.vertices(gCopy, endPts)
        }
        return(list(splitBetweenness = E(gCopy)$score, 
                    splitting = V(gCopy)$realName))
    }))
}

#'
#' @description find overlapping communities with Cluster-Overlap Newman Girvan Algorithm (CONGA)
#'
#' @param g igraph graph object. Assumed to be undirected unweighted simple
#' 
#' @param edgeBelongingCoeffFunc a function that takes two numerics and return a numeric
#'                               the function to compute the belonging coefficient of an edge
#'                               the inputs are the belonging coefficients of the endpoints 
#'                                   in a fixed community
#'                               default: prod
#' 
#' @param removeMultipleEdges boolean. determine in edge removal stage 
#'                                if all edges with max edge betweenness should be remove
#'                                simultaneously
#'                            default: FALSE
#' 
#' @return a matrix of belonging coefficients representing how the communities are defined, 
#'         along with the overlapping modularity
#'         entry at [vertexID, communityID] is the belonging coefficient of vertexID in communityID
#' 
#' @note the complexity should be worse than what it supposed to be due to some overhead and lack of optimization, 
#'       but the performance is somehow still decent
#'
#' @references S. Gregory
#'             An Algorithm to find Overlapping Community Structure in Networks
#'             doi: 10.1007/978-3-540-74976-9_12
#'
#' @references https://github.com/GiulioRossetti/cdlib/blob/master/cdlib/algorithms/internal/CONGA.py
#' 
#' @note use split_betweenness_greedy, which sometimes use split_betweenness_forest
#'
CONGA = function(g, edgeBelongingCoeffFunc = prod, removeMultipleEdges = FALSE, debugVerbose = 0){
    computedLayout = layout.auto(g)
    # check if g is connected?
    gOrig = g
    vcg = vcount(g)
    E(g)$eb = edge.betweenness(g)
    maxeb = max(E(g)$eb)
    V(g)$vb = sapply(V(g), 
                     function(vid)
                         sum(incident(g, vid)$eb) / 2 - (getComponentSize(g, vid) - 1)) # formula from paper
    V(g)$realName = seq_len(vcg)
    maxQ = 0
    maxComm = as.list(rep(1, vcg))
    iterCounter = 0
    while (ecount(g) != 0){
        iterCounter = iterCounter + 1
        if (debugVerbose >= 1){
            print(iterCounter)
            print(ecount(g))
            if (debugVerbose >= 2){
                plot(g)
            }
        }
        V(g)$needRecompute = FALSE
        candidateSet = which(V(g)$vb > maxeb)
        affectedVertices = NULL
        if (length(candidateSet) != 0){
            if (debugVerbose >= 1){
                print("split vertex")
            }
            # split vertex with max split betweenness
            splitBetweennessReturn = split_betweenness_greedy(g, candidateSet)
            if (debugVerbose >= 1){
                print("split betweenness computed")
            }
            vertexIdxInCandSet = which.max(sapply(splitBetweennessReturn, 
                                                  function(x)x$splitBetweenness))
            vertexToSplit = candidateSet[vertexIdxInCandSet]
            if (debugVerbose >= 1){
                print(paste("splitting", vertexToSplit))
            }
            splitMethod = splitBetweennessReturn[[vertexIdxInCandSet]]$splitting
            if (debugVerbose >= 1){
                print(splitMethod)
            }
            vcg = vcount(g)
            affectedVertices = c(sapply(getComponentMembers(g, 
                                                            vertexToSplit), 
                                        function(x) if (x > vertexToSplit) x-1 else x), 
                                 vcg, 
                                 vcg + 1)
            # V(g)$needRecompute[affectedVertices] = TRUE
            g = add.vertices(g, 2, 
                             # needRecompute = TRUE, 
                             realName = V(g)$realName[vertexToSplit]) # ID should be vcg + 1, vcg + 2
            g[vcg + 1, splitMethod[[1]]] = 1
            g[vcg + 2, splitMethod[[2]]] = 1
            g = delete.vertices(g, vertexToSplit)
        } else {
            if (debugVerbose >= 1){
                print("remove edge")
            }
            # remove edge with max edge betweenness
            if (debugVerbose >= 1){
                print(paste("num of edge candidate", length(which(E(g)$eb == max(E(g)$eb)))))
            }
            edgesToRemove = E(g)[if (removeMultipleEdges) which(E(g)$eb == max(E(g)$eb)) else which.max(E(g)$eb)]
            if (debugVerbose >= 1){
                print(paste("removing", 
                            paste(V(g)[ends(g, edgesToRemove, names = F)]$realName, collapse = ' ')))
            }
            affectedVertices = unique(unlist(getComponentMembers(g, 
                                                                 head_of(g, edgesToRemove))))
            # V(g)$needRecompute[affectedVertices] = TRUE
            g = delete.edges(g, edgesToRemove)
        }
        # recompute
        # affectedVertices = which(V(g)$needRecompute)
        affectedEdges = unlist(g[[affectedVertices, , edges = TRUE]])
        E(g)$eb[affectedEdges] = edge.betweenness(g, affectedEdges)
        V(g)$vb[affectedVertices] = sapply(affectedVertices, 
                                           function(vid)
                                               sum(incident(g, vid)$eb) / 2 - (getComponentSize(g, vid) - 1))
        # compute partition
        currentComm = belongCoeffVectFromCommList(lapply(decompose(g), 
                                                         function(subG)V(subG)$realName))
        currentQ = overlapping_modularity(gOrig, currentComm, edgeBelongingCoeffFunc)
        if (debugVerbose >= 1){
            print(paste(maxQ, currentQ))
            if (debugVerbose >= 2 && currentQ > maxQ){
                plot_overlapComm(gOrig, belongCoeffMatrixFromVectList(currentComm), layout = computedLayout)
            }
        }
        if (currentQ > maxQ){
            maxQ = currentQ
            maxComm = currentComm
        }
    }
    return(list(modularity = maxQ, 
                belongingCoeff = belongCoeffMatrixFromVectList(maxComm)))
}


# #' 
# #' @description comprehensive network feature value of a vertex
# #' 
# #' @param g igraph graph object. the graph to look at. assumed simple undirected
# #' 
# #' @param v integer vector. the id of the vertices to compute. 
# #'          default: all vertices in g
# #' 
# #' @param beta numeric. the coupling coefficient
# #'             default: 0.3
# #' 
# #' @return a numeric vector with the same length as v, representing the CNFV
# #' 
# #' @references Z. Ding, X. Zhang, D. Sun, B. Luo 
# #'             Overlapping Community Detection based on Network Decomposition
# #'             doi: 10.1038/srep24115
# #' 
# CNFV = function(g, v = V(g), beta = 0.3){
#     nbhdSize = degree(g, v)
#     clusteringCoeff = ifelse(nbhdSize <= 1, 
#                              1, 
#                              2 * count_triangles(g, v) / (nbhdSize - 1) / nbhdSize)
#     return(beta * clusteringCoeff + (1 - beta) * nbhdSize / vcount(g))
# }
# 
# #' 
# #' @description find the centered clique contained a given vertex
# #' 
# #' @param g igraph graph object. the graph to look at. assumed simple undirected
# #' 
# #' @param v integer. the id of the vertice to compute
# #' 
# #' @return a vertex sequence containing the id of the vertices in the clique
# #' 
# #' @references E. Becker, B. Robisson, C. E. Chapple, A. Guenoche, C. Brun
# #'             Multifunctional proteins revealed by overlapping clustering in protein interaction network
# #'             doi: 10.1093/bioinformatics/btr621
# #' 
# #' @references Z. Ding, X. Zhang, D. Sun, B. Luo 
# #'             Overlapping Community Detection based on Network Decomposition
# #'             doi: 10.1038/srep24115
# #' 
# centered_clique = function(g, v){
#     vertexList = c(v)
#     L = neighbors(g, v)
#     degVect = sapply(L, function(neiVID)length(g[[neiVID, L]]))
#     for (neiVID in L[order(degVect, decreasing = TRUE)]){
#         if (all(g[from = rep(neiVID, length(vertexList)), 
#                   to = vertexList] != 0)){
#             vertexList = c(vertexList, neiVID)
#         }
#     }
#     return(vertexList)
# }
# 
# #' 
# #' @description overlapping community detection with NDOCD
# #' 
# #' @param g igraph graph object. the graph to cluster. assumed undirected unweighted simple
# #' 
# #' @return ?
# #' 
# #' @references Z. Ding, X. Zhang, D. Sun, B. Luo 
# #'             Overlapping Community Detection based on Network Decomposition
# #'             doi: 10.1038/srep24115
# #' 
# NDOCD = function(g, jsThreshold, mdThreshold){
#     degreeVect = degree(g)
#     while (TRUE){
#         # step 1: seed selection 
#         seed = centered_clique(g, which.max(CNFV(g)))
#         # break in step 4? 
#         if (vcount(g) == 0){
#             break
#         }
#         # step 2: seed expansion
#         hasAdded = TRUE
#         while (hasAdded){
#             hasAdded = FALSE
#             candidatesToAdd = setdiff(Reduce(union, 
#                                              neighborhood(g, 1, seed)), 
#                                       seed)
#             candidateLink = Matrix::rowSums(g[candidatesToAdd, seed] != 0)
#             candidateJS = candidateLink / length(seed)
#             candidateMemDeg = candidateLink / degree(g, candidatesToAdd)
#             candidatesToAdd = candidatesToAdd[which((candidateJS >= jsThreshold) | (candidateMemDeg >= mdThreshold))]
#             if (length(candidatesToAdd) != 0){
#                 seed = c(seed, candidatesToAdd)
#                 hasAdded = TRUE
#             }
#         }
#         # step 3: network decomposition
#         
#         
#     }
#     # step 5: eliminate nodes
# }
# 
