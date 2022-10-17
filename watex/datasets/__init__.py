# -*- coding: utf-8 -*-
#   Licence:BSD 3-Clause
#   Author: LKouadio <etanoyau@gmail.com>.
""" 
Dataset 
==========
Fetch data from the local machine. If data does not exist, retrieve it 
from online (repository or zenodo record ) 

"""
try:
    from ._config import _fetch_data
    from .dload import (
        load_bagoue , 
        load_gbalo, 
        load_iris, 
        load_semien, 
        load_tankesse , 
        load_boundiali, 
        )
    
    __all__=["fetch_data", "load_bagoue" , "load_gbalo", 
             "load_iris", "load_semien", "load_tankesse", 
             "load_boundiali"
             ]

except ImportError : 
    from warnings import warn 
    from .._watexlog import watexlog
    
    m= ("None config file detected. Auto-data preparation process is aborted."
            "Be aware, the basics examples won't be implemented. Fetch data "
            " manually from remote (repository or zenodo record) using the "
            " module 'rload' via < :mod:`watex.datasets.rload` >"
            )
    watexlog().get_watex_logger(__name__).debug(m); warn(m, UserWarning)


def fetch_data (tag, **kws): 
    func= _fetch_data 
    funcs= (load_bagoue , load_gbalo, load_iris, load_semien, load_tankesse , 
            load_boundiali)
    funcns = tuple (map(lambda f: f.__name__.replace('load_', ''), funcs))
    if tag in (funcns): 
        func = funcs[funcns.index (tag)] 
    return func (tag=tag, **kws)


fetch_data.__doc__ ="""\
Fetch dataset from 'tag'. A tag corresponds to the name area of data  
collection or each level of data processing. 

An example of retrieving Bagoue dataset can experiment.

Parameters 
------------
tag: str, ['bagoue', 'tankesse', 'semien', 'iris', 'boundiali', 'gbalo']
    name of the area of data to fetch. For instance set the tag to ``bagoue`` 
    will load the bagoue datasets. If the `tag` name is following by a suffix, 
    the later specifies the stage of the data processing. As an example, 
    `bagoue original` or `bagoue prepared` will retrieve the original data and 
    the transformed data after applying default transformers respectively. 
    
    There are different options to retrieve data such as:
        
    * ['original'] => original or raw data -& returns a dict of details 
        contex combine with get method to get the dataframe like::
            
            >>> fetch_data ('bagoue original').get ('data=df')
            
    * ['stratified'] => stratification data
    * ['mid' |'semi'|'preprocess'|'fit']=> data cleaned with 
        attributes experience combinaisons.
    * ['pipe']=>  default pipeline created during the data preparing.
    * ['analyses'|'pca'|'reduce dimension']=> data with text attributes
        only encoded using the ordinal encoder +  attributes  combinaisons. 
    * ['test'] => stratified test set data

Returns
-------
dict, X, y : frame of :class:`~watex.utils.box.Boxspace` object 
    If tag is following by suffix in the case of 'bagoue' area, it returns:
        - `data`: Original data 
        - `X`, `y` : Stratified train set and training target 
        - `X0`, `y0`: data cleaned after dropping useless features and combined 
            numerical attributes combinaisons if ``True``
        - `X_prepared`, `y_prepared`: Data prepared after applying  all the 
            transformation via the transformer (pipeline). 
        - `XT`, `yT` : stratified test set and test label  
        - `_X`: Stratified training set for data analysis. So None sparse
            matrix is contained. The text attributes (categorical) are 
            converted using Ordianal Encoder.  
        - `_pipeline`: the default pipeline. 
Examples 
---------
>>> from watex.datasets import fetch_data 
>>> b = fetch_data('bagoue' ) # no prefix return 'Boxspace' object
>>> b.tnames 
... array(['flow'], dtype='<U4')
>>> b.feature_names 
... ['num',
     'name',
     'east',
     'north',
     'power',
     'magnitude',
     'shape',
     'type',
     'sfi',
     'ohmS',
     'lwi',
     'geol']
>>> X, y = fetch_data('bagoue prepared' )
>>> X # is transformed  # ready for prediction 
>>> X[0] 
... <1x18 sparse matrix of type '<class 'numpy.float64'>'
	with 8 stored elements in Compressed Sparse Row format>
>>> y
... array([2, 1, 2, 2, 1, 0, ... , 3, 2, 3, 3, 2], dtype=int64)

"""    





    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    