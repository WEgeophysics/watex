# -*- coding: utf-8 -*-
# Copyright (c) 2021 Kouadio K. Laurent, zju-ufhb
# This module is part of the WATex core package, which is released under a
# MIT- licence.

"""
 .. Synopsis: Module features collects geo-electricals features compute from 
     :class:`watex.core.erp.ERP` and :class:`watex.core.ves.VES` and keeps 
     on a new data frame for analysis and modeling. 
     
Created on Mon Jul  5 16:51:14 2021

@author: @Daniel03

"""
import os 
import pandas as pd 
# import json 
# import numpy as np 
import pandas as pd 
import  watex.utils.exceptions as Wex
import watex.utils.wmathandtricks as wfunc
import watex.utils.gis_tools as gis

import xml.etree.ElementTree as ET

from watex.utils._watexlog import watexlog 

class Features: 
    """
    Features class. Deals  with Electrical Resistivity profile (VES) and
    Vertical electrical Sounding (VES). Set all features values of sites area 
    Features class is  composed of `features_labels` for ``ML`` appliactions 
    Once parameters are computed , the class uses each features for ML purposes 
   
    """
    
    dataType ={
                ".csv":pd.read_csv, 
                 ".xlsx":pd.read_excel,
                 ".json":pd.read_json,
                 ".html":pd.read_json,
                 ".sql" : pd.read_sql
                 }  
    feature_labels = [
                        'boreh', 
                        'x_m',
                        "y_m",
                        'pa',
                        "ma",
                        "shape",
                        "type",
                        "sfi",
                        'ohms',
                        'wi', 
                        'geol',
                        'flow'
            ]
    

    def __init__(self, erpData=None, horizonDis=None , rhoApp=None,**kwargs):
        self._logging = watexlog.get_watex_logger(self.__class__.__name__)
        
        self.erp_data=erpData
        
        self.utmX =kwargs.pop('utmX', None)
        self.utmY =kwargs.pop('utmY', None)
        
        for key in list(kwargs.keys()):
            setattr(self, key, kwargs[key])
            

    def from_csv(self, erp_fn):
        """
        Method essentially created to read file from csv , collected 
        horizontal distance value and apparent resistivy values. 
        then send to the class for computation purposes. 
        
        :param erp_fn: path_like string of CSV file 
        :type erp_fn: str 
        
        :return: horizontal distance im meters 
        :rtype: np.array of all data
        """
        if not os.path.isfile(erp_fn):
            raise Wex.WATexError_file_handling('{} is not a file. '
                                               'Please provide a right file !'
                                               .format(erp_fn))
        with open(erp_fn, 'r') as fcsv: 
            csvData = fcsv.readlines()
            
        # retrieve ;locations,  coordinates values for each pk, 
        # horizontal distance in meter and apparent resistivity values 
        

    def from_xml (self, xml_fn, columns=None):
        """
        collected data from xml  and build dataFrame 
        :param xxlm_fn: full path to xml file 
        :type xml: str 
        
        :param columns: list of columns of dataset 
        :type columns: list 
        
        """
        tree = ET.parse(xml_fn)

        root = tree.getroot()
        dataframe = pd.DataFrame(columns = columns)
        # loop the node and collect files from loop 
        seriesList =[]
        for ii, node in enumerate(root): 
            seriesList.append(node.find(columns[ii]).text)
            
        # after loop , use series to create pandas dataframes 
        #create dataframe but ignore index 
    
        dataframe=dataframe.append(pd.Series(seriesList, index=columns ), 
                                   ignore_index=True )
        

    def from_json (self, json_fn , indent =4):
        """
        Collected data from json files and retrieve the most insights contents 
        
        :param json_fn: json file 
        :type json_fn: str 
        
        """
    
    def data_to_numpy(self, data_fn): 
        """
        Method to get datatype and set different features into nympy array
        
        """
        if data_fn is not None : 
            self.erp_data =data_fn 
        
        if not os.path.isfile(self.erp_data): 
            raise Wex.WATexError_file_handling('{} is not a file. '
                                               'Please provide a right file !'
                                               .format(self.erp_data))
        ex_file = os.path.splitext(self.erp_data)[1] 
        if not ex_file in self.dataType.keys(): 
            pass 