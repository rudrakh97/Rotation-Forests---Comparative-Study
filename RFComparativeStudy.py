import os
import random
import sys
import numpy as np
from scipy.stats import mode
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import AdaBoostClassifier, BaggingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score

"""
Rotation forest:
Reference - http://ieeexplore.ieee.org/ielx5/34/35279/01677518.pdf
n denotes the ID of the *.data file
Eg: "python3/python RFComparativeStudy.py 5" takes input from 5.data file in uci-datasets
"""

n = int(sys.argv[1])
n_classifiers = int(sys.argv[2])
classifiers = []
rotmat = []
std = []
med = []
noise = []
selected_subsets = []
outFile = open("compare.txt", "awr+")

def takeInput(n):
    path = './uci-datasets/' + str(n) + '.data'
    data = np.genfromtxt(path, delimiter=",")
    rows, cols = data.shape
    Y = data[:,0]
    X = data[:,1:rows]
    return X,Y

X, Y = takeInput(n)
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=0)
n_samps, n_features = X.shape
n_classes = len(np.unique(Y))

def train(X,Y):
        n_samps, n_features = X.shape
        std = np.std(X,axis=0)
        med = np.mean(X,axis=0)
        # noise = [random.uniform(-0.000005, 0.000005) for p in range(0,X.shape[1])]
        # X_z = (X-med)/(std+noise)
        X_z = (X-med)/std
        for i in range(n_classifiers):
            K = int(round(1 + n_features/4*random.random()))
            # K random subsets of the feature set
            k_features = np.zeros((K,n_features))
            for j in range(K):
                # select random number of features
                n_selected_features = int(1 + round((n_features-1)*random.random()))
                rp = np.random.permutation(n_features)
                v = [rp[k] for k in range(0, n_selected_features)]
                # set k_features[i,j] to select jth feature in the ith subset
                k_features[j,v] = 1
            R = np.zeros((n_features,n_features))
            for l in range(K):
                # return indices of k_features that are non-zero
                pos = np.nonzero(k_features[l,:])[0]
                # print pos
                # selected features
                vpos = [pos[m] for m in range(0, len(pos))]
                # print vpos
                # input modified according to selected features
                X_zij = X_z[:, vpos]
                # apply PCA
                pca = PCA(n_components=len(pos), whiten=False, copy=True)
                pca.fit(X_zij)
                for indI in range(0,len(pca.components_)):
                    for indJ in range(0,len(pca.components_)):
                        R[pos[indI], pos[indJ]] = pca.components_[indI,indJ]            
            rotmat.append(R)
            Xrot = X_z.dot(R)
            cl = DecisionTreeClassifier()
            cl.fit(Xrot, Y)
            # print Xrot.shape[1]
            classifiers.append(cl)
            # selected_subsets.append(v);
        return classifiers, rotmat, std, med, noise

def test(X):
    dim = len(classifiers)
    out = np.zeros((X.shape[0], n_classes))    
    X = (X-med)/std
    # print X.shape
    for i in range(0,dim):
        xrot_z = X.dot(rotmat[i])
        mat = classifiers[i].predict_proba(xrot_z)
        out = out + mat
    # print out
    y_pred = np.zeros(X.shape[0])
    for i in range(X.shape[0]):
        y_pred[i] = 1 + int(out[i].argmax())
    # y_pred = mode(out, axis=1)[0]
    return y_pred

classifiers, rotmat, std, med, noise = train(X_train, Y_train)
pred = test(X_test)
pred = pred.flatten()
pred = pred.astype(int)
Y_test = Y_test.astype(int)
# print ("Accuracy (Rotation Forest): " + str(100*accuracy_score(Y_test, pred)) + " %")
outFile.write(str(100*accuracy_score(Y_test, pred))+" ")

"""
Boosting algorithm:
Reference - http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.AdaBoostClassifier.html#sklearn.ensemble.AdaBoostClassifier
"""
boost = AdaBoostClassifier(base_estimator=DecisionTreeClassifier(), n_estimators=n_classifiers, learning_rate=0.1, algorithm='SAMME.R', random_state=None)
boost.fit(X_train, Y_train)
#print ("Accuracy (Boosting Algorithm): " + str(100*accuracy_score(Y_test, boost.predict(X_test))) + " %")
outFile.write(str(100*accuracy_score(Y_test, boost.predict(X_test)))+" ")

"""
Bagging algorithm:
Reference - http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.BaggingClassifier.html#sklearn.ensemble.BaggingClassifier
"""
bag = BaggingClassifier(base_estimator=DecisionTreeClassifier(), n_estimators=n_classifiers, max_samples=1.0, max_features=1.0, bootstrap=True, bootstrap_features=False, oob_score=False, warm_start=False, n_jobs=1, random_state=None, verbose=0)
bag.fit(X_train, Y_train)
# print ("Accuracy (Bagging Algorithm): " + str(100*accuracy_score(Y_test, bag.predict(X_test))) + " %")
outFile.write(str(100*accuracy_score(Y_test, bag.predict(X_test)))+" ")

"""
Random Forest
Reference - http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
"""
rf = RandomForestClassifier(n_estimators=n_classifiers, criterion='gini', max_depth=None, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_features='auto', max_leaf_nodes=None, min_impurity_decrease=0.0, min_impurity_split=None, bootstrap=True, oob_score=False, n_jobs=1, random_state=None, verbose=0, warm_start=False, class_weight=None)
rf.fit(X_train, Y_train)
# print ("Accuracy (Random Forest): " + str(100*accuracy_score(Y_test, rf.predict(X_test))) + " %")
outFile.write(str(100*accuracy_score(Y_test, rf.predict(X_test)))+"\n")