# this script provides the following functions:
# 
# is_planar_graph_DMP
# 
# Please goto the corresponding function definition for detail description

if (!require(igraph)){
    stop('these functions requires igraph')
}

# DMP algorithm (for a biconnected graph):
# 1.  select a loop in the graph as the subgraph. the subgraph divides plane into 2 faces
# 2.  if all edges are in the subgraph, the graph is planar
# 3.  look at all components divided by the subgraph ("bridges")
# 4.      if some bridge cannot be embedded in a face, the graph is nonplanar
# 5.      if some bridge can only be embedded in one face
# 6.          select the bridge and the face
# 7.      else select a random bridge and an embedable face of the bridge
# 8.  find a path in the bridge that connects 2 points of the subgraph
# 9.  add the path in the subgraph by dividing the face with the path
# 10. start again from step 2
# If the graph is not biconnected, check each biconnected component

# todo optimize (with Rcpp?)
# ! on Erdos-Renyi graphs, performance seems better than others
# ! on actural large (almost) planar graph, the test may take ~13 seconds
# Erdos-Renyi gives ~ 1/6 planar graph only, most (have bicomps that) can be 
#     determined by fast degree/order condition
# todo check against large planar graph
# ? need method to generate random large (V > 20) planar graph
# todo put it in another file

# note
# output match RBGL::boyerMyrvoldPlanarityTest
# checked with random Erdos-Renyi model with small edge probability
# code used:
#     for (i in 1:1000){
#         print(i)
#         g = erdos.renyi.game(sample(20:200, 1), runif(1, max = 1/3))
#         RBGLRes = RBGL::boyerMyrvoldPlanarityTest(as_graphnel(g))
#         DMPRes = is_planar_graph_DMP(g)
#         if (RBGLRes != DMPRes){
#             plot(g)
#             browser()
#         }
#     }

#' 
#' @description test if a graph can be embedded into a plane with 
#'              Demoucron-Malgrange-Pertuiset (DMP) algorithm. 
#' 
#' @param graph igraph graph object
#' 
#' @return boolean indicating if the input graph is planar
#' 
#' @note Although DMP algorithm should be O(V^2), the actual complexity of this
#'       implementation could be much worse (possibly O(V^3) or worse) due to 
#'       bad implementations and unnecessary operations
#' 
#' @note This implementation is only meant as a fallback when no other 
#'       options is available. Use other library (e.g. Boost-based) if possible. 
#' 
#' @note I could not find the original paper by Demoucron, Malgrange and Pertuiset. 
#'       The algorithm is adapted from Bondy & Murty. 
#' 
#' @references J. A. Bondy, U. S. R. Murty, "Graph Theory with Application"
#' 
is_planar_graph_DMP = function(graph){
    E = ecount(graph)
    V = vcount(graph)
    # early break
    if (V <= 4 || E <= 8){
        return(TRUE)
    }
    if (E > 3 * V - 6){
        return(FALSE)
    }
    # find bicomps as DMP works on bicomps only
    compList = components(graph)
    compList = lapply(seq_len(compList$no), 
                      function(compIdx)induced_subgraph(graph, 
                                                        which(compList$membership == compIdx))) 
    biCompList = unlist(lapply(compList, 
                               function(g)lapply(biconnected_components(g)$components, 
                                                 function(biCompVertices)induced_subgraph(g, biCompVertices))), 
                        recursive = FALSE)
    DMP_find_loop = function(biComp){
        # find a loop in biComp
        # @param biComp igraph graph object. should be biconnected. 
        # @return a vector of vertices in loop in order
        #         if no loop found, return NULL (should not happed if biComp is biconnected)
        dfsRoot = sample.int(vcount(biComp), 1)
        dfsParent = rep(NA, vcount(biComp))
        dfsStack = c(dfsRoot)
        dfsPtr = 1
        dfsParent[dfsRoot] = dfsRoot
        while (dfsPtr != 0){
            thisV = dfsStack[dfsPtr]
            dfsPtr = dfsPtr - 1
            for (neiV in neighbors(biComp, thisV)){
                if (neiV == dfsParent[thisV]){
                    next
                }
                if (is.na(dfsParent[neiV])){
                    dfsParent[neiV] = thisV
                    dfsPtr = dfsPtr + 1
                    dfsStack[dfsPtr] = neiV
                } else {
                    # cycle found
                    # ! this method is stupid
                    # ! ~4V time, 2V spaces (ignore space reallocate)
                    # todo use better method
                    ptr = thisV
                    path1 = c(thisV)
                    while (ptr != dfsRoot){
                        ptr = dfsParent[ptr]
                        path1 = c(path1, ptr)
                    }
                    ptr = neiV
                    path2 = c(neiV)
                    while (ptr != dfsRoot){
                        ptr = dfsParent[ptr]
                        path2 = c(path2, ptr)
                    }
                    l1 = length(path1)
                    l2 = length(path2)
                    counter = 1
                    while (counter < min(l1, l2) && path1[l1 - counter] == path2[l2 - counter]){
                        counter = counter + 1
                    }
                    if (counter != 0){
                        return(c(path1[1:(l1 - counter + 1)], rev(path2[1:(l2 - counter)])))
                    } else if (l1 < l2){
                        return(path2[1:(l2 - l1 + 1)])
                    } else {
                        return(path1[1:(l1 - l2 + 1)])
                    }
                    
                }
            }
        }
        # probably will never reach this
        return(NULL)
    }
    DMP_find_all_bridges = function(biComp, subgraphVertices, subgraphEdgeId){
        # find all bridges of a subgraph
        # the definition of "bridge (of a subgraph)" is adapted from Bondy & Murty
        #     i.e. equivalent classes of edges that can be walked through on a path that has no internal point from the subgraph
        # instead of edge ids, only the vertices involved are returned
        # @param biComp igraph graph object. should be biconnected. 
        # @param subgraphVertices vector of vertex ids. vertices of forbidden vertices
        # @param subgraphEdgeId vector of edge ids. edges of forbidden vertices
        # @return a list of vectors, each vector records the vertices in a bridge
        returnList = list()
        returnListWPtr = 1
        visited = rep(FALSE, vcount(biComp))
        visited[subgraphVertices] = NA
        for (initialPoint in subgraphVertices){
            for (initialNei in neighbors(biComp, initialPoint)){
                if (isFALSE(visited[initialNei])){
                    thisBridge = c(initialPoint, initialNei)
                    inBridge = rep(FALSE, vcount(biComp))
                    inBridge[thisBridge] = TRUE
                    dfsStack = c(initialNei)
                    dfsPtr = 1
                    while (dfsPtr != 0){
                        thisV = dfsStack[dfsPtr]
                        dfsPtr = dfsPtr - 1
                        for (neiV in neighbors(biComp, thisV)){
                            if (isFALSE(visited[neiV])){
                                thisBridge[length(thisBridge) + 1] = neiV
                                inBridge[neiV] = TRUE
                                visited[neiV] = TRUE
                                dfsPtr = dfsPtr + 1
                                dfsStack[dfsPtr] = neiV
                            } else if (is.na(visited[neiV]) && !inBridge[neiV]){
                                # neiV in subgraphVertices
                                thisBridge[length(thisBridge) + 1] = neiV
                                inBridge[neiV] = TRUE
                            }
                        }
                    }
                    returnList[[returnListWPtr]] = thisBridge
                    returnListWPtr = returnListWPtr + 1
                } else if (is.na(visited[initialNei]) && !get.edge.ids(biComp, c(initialPoint, initialNei)) %in% subgraphEdgeId){
                    returnList[[returnListWPtr]] = c(initialPoint, initialNei)
                    returnListWPtr = returnListWPtr + 1
                }
            }
        }
        return(returnList)
    }
    DMP_find_bridge_path = function(bridgeVertices, attachmentPoints, biComp, forbiddenEdges){
        # find a path in a bridge between attachment points
        # the definition of "bridge (of a subgraph)" is adapted from Bondy & Murty
        # @param bridgeVertices vector of vertex ids of the bridge
        # @param attachmentPoints vector of vertex ids of the attachment points
        # @param biComp igraph graph object. should be biconnected. 
        # @param forbiddenEdges vector of edge ids between attachment points that are not in bridge
        # @return a vector of vertex ids of the path, begins and ends at attachment points
        # ! only return path with distinct endpoints
        # ? should loop be accepted?
        dfsRoot = sample(attachmentPoints, 1)
        dfsPtr = 1
        dfsStack = c(dfsRoot)
        dfsParent = rep(NA, vcount(biComp))
        dfsParent[dfsRoot] = dfsRoot
        while (dfsPtr != 0){
            thisV = dfsStack[dfsPtr]
            dfsPtr = dfsPtr - 1
            for (neiV in intersect(neighbors(biComp, thisV), bridgeVertices)){
                if (neiV == dfsParent[thisV]){
                    next
                }
                neiInAP = neiV %in% attachmentPoints
                if (neiInAP && thisV %in% attachmentPoints && get.edge.ids(biComp, c(thisV, neiV)) %in% forbiddenEdges){
                    # edge in subGraph
                    next
                }
                if (is.na(dfsParent[neiV])){
                    dfsParent[neiV] = thisV
                    dfsPtr = dfsPtr + 1
                    dfsStack[dfsPtr] = neiV
                }
                if (neiInAP && neiV != dfsRoot){
                    # path found
                    returnPath = c(neiV)
                    while (neiV != dfsRoot){
                        neiV = dfsParent[neiV]
                        returnPath = c(returnPath, neiV)
                    }
                    return(returnPath)
                }
            }
        }
        stop('In DMP_find_bridge_path, \n\tbiComp traversed without finding a path in bridge connecting attachment points. \n\tThis should not happen. ')
    }
    DMP_internal = function(biComp){
        # actural work of DMP algo
        # @param biComp igraph graph object. should be biconnected. 
        # @return boolean indicating if biComp is planar
        Eg = ecount(biComp)
        Vg = vcount(biComp)
        if (Vg <= 4 || Eg <= 8){
            return(TRUE)
        }
        if (Eg > 3 * Vg - 6){
            return(FALSE)
        }
        subGraph.vertex = DMP_find_loop(biComp)
        if (is.null(subGraph.vertex)){ # is tree
            return(TRUE)
        }
        subGraph.edgeId = sapply(seq_along(subGraph.vertex), 
                                 function(sIdx)
                                     get.edge.ids(biComp, 
                                                  c(subGraph.vertex[sIdx], 
                                                    subGraph.vertex[sIdx %% length(subGraph.vertex) + 1])))
        faceListByBdyVertex = list(subGraph.vertex, rev(subGraph.vertex)) # inner and outer
        # ! ensure loop end
        # should end as subGraph.edgeId monotone increase
        while (TRUE){
            if (Eg == length(subGraph.edgeId)){
                return(TRUE)
            }
            bridgeVertexList = DMP_find_all_bridges(biComp, subGraph.vertex, subGraph.edgeId)
            attachPoint = lapply(bridgeVertexList, 
                                 function(bVList)intersect(bVList, subGraph.vertex))
            FBG = lapply(attachPoint, 
                         function(aPList)seq_along(faceListByBdyVertex)[sapply(faceListByBdyVertex, 
                                                                               function(fVList)all(aPList %in% fVList))])
            FBGCount = sapply(FBG, length)
            if (any(FBGCount == 0)){
                return(FALSE)
            }
            targetBridgeIdx = match(1, FBGCount)
            targetFaceIdx = NA
            if (is.na(targetBridgeIdx)){
                targetBridgeIdx = sample.int(length(FBGCount), 1)
                targetFaceIdx = sample(FBG[[targetBridgeIdx]], 1)
            } else {
                # deal with sample(c(n), 1) == sample.int(n, 1)
                targetFaceIdx = FBG[[targetBridgeIdx]]
            }
            targetFace = faceListByBdyVertex[[targetFaceIdx]]
            # ! will go into problem if attachPoint[[targetBridgeIdx]] has only one element
            # ? will it happen? 
            pathToAdd = DMP_find_bridge_path(bridgeVertexList[[targetBridgeIdx]], 
                                             attachPoint[[targetBridgeIdx]], 
                                             biComp, subGraph.edgeId)
            pathLength = length(pathToAdd)
            pathBeginPt = pathToAdd[1]
            pathEndPt = pathToAdd[pathLength]
            if (pathLength != 2){
                subGraph.vertex = c(subGraph.vertex, pathToAdd[2:(pathLength - 1)]) # exclude attach points
            }
            subGraph.edgeId = c(subGraph.edgeId, 
                                sapply(seq_len(pathLength - 1), 
                                       function(sIdx)
                                           get.edge.ids(biComp, 
                                                        c(pathToAdd[sIdx], 
                                                          pathToAdd[sIdx + 1]))))
            # reorder targetFace for easy slicing
            if (targetFace[1] != pathEndPt){
                ptr = 1
                while (targetFace[ptr] != pathEndPt){
                    ptr = ptr + 1
                }
                targetFace = c(targetFace[ptr:length(targetFace)], targetFace[1:(ptr - 1)])
            }
            ptr = 2
            while (targetFace[ptr] != pathBeginPt){
                ptr = ptr + 1
            }
            faceListByBdyVertex[[targetFaceIdx]] = c(targetFace[1:(ptr - 1)], pathToAdd[1:(pathLength - 1)])
            faceListByBdyVertex[[length(faceListByBdyVertex) + 1]] = c(targetFace[ptr:length(targetFace)], rev(pathToAdd[2:pathLength]))
        }
    }
    # graph planar iff all bicomp planar
    for (biComp in biCompList){
        if (!DMP_internal(biComp)){
            return(FALSE)
        }
    }
    return(TRUE)
}   