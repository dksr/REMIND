def k_fold_cross_validation(X, K, test_list=[], randomise = False):
    """
    Generates K (training, validation) pairs from the items in X.

    Each pair is a partition of X, where validation is an iterable
    of length len(X)/K. So each training iterable is of length (K-1)*len(X)/K.
    
    If test list is also given, then just return train and test lists.
    
    If randomise is true, a copy of X is shuffled before partitioning,
    otherwise its order is preserved in training and validation.
    
    TODO:
    Support stratified crossvalidation
    """
    if len(test_list) is not 0:
        # Test list is given. So just return train and test list
        yield X, test_list
    else:
        if randomise: from random import shuffle; X=list(X); shuffle(X)
        if K > len(X):
            # K can't be bigger than the number of cases
            K = len(X)
        elif K == 1:
            # If K == 1, thne just return the train and test as they are
            yield X, test_list
            return
        for k in xrange(K):
            training = [x for i, x in enumerate(X) if i % K != k]
            validation = [x for i, x in enumerate(X) if i % K == k]
            yield training, validation

if __name__ == '__main__':
    X = [2,5,8,9]
    T = [1,3]
    for training, validation in k_fold_cross_validation(X, 1):
        print training
        print validation