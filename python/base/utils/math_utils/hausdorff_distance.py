def hausdorff_distance(clust1, clust2, forward):
    """
    Function measures distance between 2 sets. (Some kind of non-similarity between 2 sets if you like).
    """
    if forward == None:
        return max(hausdorff_distance(clust1,clust2,True), hausdorff_distance(clust1,clust2,False))
    else:
        clstart, clend = (clust1,clust2) if forward else (clust2,clust1)
        return max([min([Dist(p1,p2) for p2 in clend]) for p1 in clstart])

def Dist(p1,p2):
    """
    Distance between 2 elements
    """
    return abs(p1 - p2)

if __name__ == "__main__":
    print hausdorff_distance([2,4,5],[1,2,5,8],None)
    
    
