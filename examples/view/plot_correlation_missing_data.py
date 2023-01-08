"""
=================================
Plot correlation missing data  
=================================

Plots helps vizualizing patterns in the missing data using the dendrogram 
"""
# Author: L.Kouadio 
# Licence: BSD-3-clause

#%%
from watex.datasets import fetch_data 
from watex.view import ExPlot
data = fetch_data("bagoue original").get('data=df') # num flow 
p = ExPlot().fit(data)
p.fig_size = (7, 5)
p.plotmissing(kind ='corr')