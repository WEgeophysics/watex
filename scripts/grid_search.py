# -*- coding: utf-8 -*-
# @author: Kouadio K. Laurent alias Daniel03
"""
..synopsis:: 
     `Search Grid will be able to  fiddle with the hyperparameters until to 
    find the great combination for model predictions. 
    
Created on Tue Sep 21 19:45:40 2021

@author: @Daniel03
"""
from pprint import pprint  

from sklearn.svm import SVC

# from watex.utils.ml_utils import BaseEvaluation
from watex.utils.ml_utils import SearchedGrid 
# modules below are imported for testing scripts.
# Not usefull to import at least you provided your own dataset.
from watex.datasets import  X_prepared, y_prepared

# set the SVM grid parameters 
grid_params = [
        {'C':[1e-2, 1e-1, 1, 10, 100],
         'gamma':[5, 2, 1, 1e-1, 1e-2, 1e-3],
         'kernel':['rbf', 'poly'],
         'degree':[1, 3,5, 7],
         'coef0':[1, 2, 3]}, 
        ]
  
# forest_clf = RandomForestClassifier(random_state =42)
# grid_search = SearchedGrid(forest_clf, grid_params, kind='RandomizedSearchCV')
# grid_search.fit(X= X_prepared , y = y_prepared)

cv =4

# kind of search : can be `RandomizedSearch CV
kindOfSearch = 'GridSearchCV'

# =============================================================================
#Grid search section. Comment this section if your want to evaluate your 
# best parameters found after search.
#==============================================================================
svc_clf = SVC(random_state=42,
                # C=10, gamma=1e-2, kernel ='poly', degree=7, coef0=2
              )
# grid_ keywords arguments 
grid_kws =dict()
grid_searchObj= SearchedGrid(svc_clf,
                           grid_params,
                           cv =cv, 
                           kind=kindOfSearch, 
                           **grid_kws)

grid_searchObj.fit(X= X_prepared , y = y_prepared)

pprint(grid_searchObj.best_params_ )
# pprint(grid_search.cv_results_)
# if your estimator has a `feature_importances_`attributes, call it by 
# uncomment the section below. If return None, mean the estimator doesnt have 
#a `feature_importances_` attributes. 

#pprint(grid_searchObj.feature_importances_ )


# =============================================================================
#Uncomment the section  below and evalaute your model with the 
# best configuration after drid search 
# =============================================================================
# from sklearn.model_selection import cross_val_score 

# svc_clf = SVC(random_state=42,
#                 **grid_searchObj.best_params_
#               )
# svc_clf_scores = cross_val_score(svc_clf, X_prepared ,
#                                   y_prepared, cv =cv ,
#                                   scoring = 'accuracy')
# print(svc_clf_scores)