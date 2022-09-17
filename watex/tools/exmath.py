# -*- coding: utf-8 -*-
#   Copyright (c) 2021 Kouadio K. Laurent, 
#   Created date: on Fri Sep 17 11:25:15 2021
#   Licence: MIT Licence 

from __future__ import annotations 

import copy 
import inspect 
import warnings 

from scipy.signal import argrelextrema 
import scipy.integrate as integrate
from scipy.optimize import curve_fit
import numpy as np
import pandas as pd 
import  matplotlib.pyplot as plt
 
from .._watexlog import watexlog
from ..documentation import __doc__
from ..decorators import ( 
    deprecated, 
    refAppender, 
    docSanitizer
)
from .. import exceptions as Wex 
from ..property import P
from ..typing import (
    T, 
    F,
    List, 
    Tuple,
    Dict, 
    Any, 
    Union,
    Array,
    DType,
    Optional,
    Sub, 
    SP, 
    Series, 
    DataFrame,
)

from .funcutils import (
    _assert_all_types, 
    drawn_boundaries, 
    fmt_text, 
    find_position_from_sa , 
    find_feature_positions,
    smart_format,
                         
)

_logger =watexlog.get_watex_logger(__name__)

#XXXTODO
def transmissibility (s, d, time, ): 
    """Transmissibility T represents the ability of aquifer's water conductivity.
    
    It is the numeric equivalent of the product of hydraulic conductivity times
    aquifer's thickness (T = KM), which means it is the seepage flow under the
    condition of unit hydraulic gradient, unit time, and unit width
    
    
    
    """
    
    
    
def dummy_basement_curve(
        func: F ,
        ks: float ,
        slope: float | int = 45, 
)-> Tuple[F, float]: 
    """ Compute the pseudodepth from the search zone. 
    
    :param f: callable - Polyfit1D function 
    :param mz: array-zone - Expected Zone for groundwater search 
    :param ks: float - The depth from which the expected fracture 
        zone must starting looking for groundwater. 
    :param slope: float - Degree angle for slope in linear function 
        of the dummy curve
    :returns: 
        - lambda function of basement curve `func45` 
        - beta is intercept value compute for keysearch `ks`
    """
    # Use kesearch (ks) to compute the beta value from the function f
    beta = func(ks)
    # note that 45 degree is used as the slope of the 
    # imaginary basement curve
    # fdummy (x) = slope (45degree) * x + intercept (beta)
    slope = np.sin(np.deg2rad(slope))
    func45 = lambda x: slope * x + beta 
    
    return func45, beta 


def find_limit_for_integration(
        ix_arr: Array[DType[int]],
        b0: List[T] =[]
)-> List[T]: 
    r""" Use the roots between f curve and basement curves to 
    detect the limit of integration.
    
    :param ix_arr: array-like - Indexes array from masked array where  
        the value are true i.e. where :math:` b-f > 0 \Rightarrow  b> f` . 
        
    :param b0: list - Empy list to hold the limit during entire loop 
    
    .. note::
        :math:`b > f \Longrightarrow` Curve b (basement) is above the fitting  
        curve :math:`f` . :math:`b < f` otherwise. The pseudoarea is the area 
        where :math:` b > f` .
    
    :return: list - integration bounds 
    
    """
    
    s = ix_arr.min() - 1 # 0 -1 =-1
    oc = ix_arr.min() 
    for jj,  v in enumerate(ix_arr): 
        s = v - s
        if s !=1: 
            b0.append(oc); b0.append(ix_arr[jj-1])
            oc= v
        s= v 
    if v ==ix_arr[-1]: 
        b0.append(oc); b0.append(v)
        
    return b0 


def find_bound_for_integration(
        ix_arr: Array[DType[int]],
        b0: List[T] =[]
)-> List[T]: 
    r""" Recursive function. Use the roots between f curve and basement 
    curves to detect the  integration bounds. The function use entirely 
    numpy for seaching integration bound. Since it is much faster than 
    `find_limit_for_integration` although both did the same tasks. 
    
    :param ix_arr: array-like - Indexes array from masked array where 
        the value are true i.e. where :math:`b-f > 0 \Rightarrow b > f` . 
        
    :param b0: list - Empy list to hold the limit during entire loop 
    
    :return: list - integration bounds
    
    .. note::
        :math:`b > f \Longrightarrow` Curve b (basement) is above the fitting curve 
        :math:`f` . :math:`b < f` otherwise. The pseudoarea is the area where 
        :math:`b > f` .
    
    """
    
    # get the first index and arange this thin the end 
    psdiff = np.arange(ix_arr.min(), len(ix_arr) + ix_arr.min(), 1) 
    # make the difference to find the zeros values 
    diff = ix_arr - psdiff 
    index, = np.where(diff ==0) ; 
    # take the min index and max index 
    b0.append(min(ix_arr[index]))
    b0.append(max(ix_arr[index]))
    #now take the max index and add +1 and start by this part 
    # retreived the values 
    array_init = ix_arr[int(max(index)) +1:]
    return b0 if len(
        array_init)==0 else find_bound_for_integration(array_init, b0)
 
    
def fitfunc(
        x: Array[T], 
        y: Array[T], 
        deg: float | int  =None,
        sample: int =1000
)-> Tuple[F, Array[T]]: 
    """ Create polyfit function from a specifc sample data points. 
    
    :param x: array-like of x-axis.
    
    :param y: array-like of y-axis.
    
    :param deg: polynomial degree. If ``None`` should compute using the 
        length of  extrema (local + global).
        
    :param sample: int - Number of data points should use for fitting 
        function. Default is ``1000``. 
    
    :returns: 
        - Polynomial function `f` 
        - new axis  `x_new` generated from the samples.
        - projected sample values got from `f`.
    """
    
    # generate a sample of values to cover the fit function 
    # thus compute ynew (yn) from the poly function f
    minl, = argrelextrema(y, np.less) 
    maxl, = argrelextrema(y,np.greater)
    # get the number of degrees
    degree = len(minl) + len(maxl)

    coeff = np.polyfit(x, y, deg if deg is not None else degree + 1 )
    f = np.poly1d(coeff)
    xn = np.linspace(min(x), max(x), sample)
    yp = f(xn)
    
    return f, xn, yp  
    
def vesDataOperator(
        AB : Array = None, 
        rhoa: Array= None ,
        data: DataFrame  =None,
        typeofop: str = None, 
        outdf: bool = False, 
)-> Tuple[Array] | DataFrame : 
    """ Check the data in the given deep measurement and set the suitable
    operations for duplicated spacing distance of current electrodes `AB`. 
    
    Sometimes at the potential electrodes (`MN`), the measurement of `AB` are 
    collected twice after modifying the distance of `MN` a bit. At this point, 
    two or many resistivity values are targetted to the same distance `AB`  
    (`AB` still remains unchangeable while while `MN` is changed). So the 
    operation consists whether to average (``mean``) the resistiviy values or 
    to take the ``median`` values or to ``leaveOneOut`` (i.e. keep one value
    of resistivity among the different values collected at the same point`AB`)
    at the same spacing `AB`. Note that for the `LeaveOneOut``, the selected 
    resistivity value is randomly chosen. 
    
    :param AB: array-like - Spacing of the current electrodes when exploring
        in deeper. Units are in meters. 
    
    :param rhoa: array-like - Apparent resistivity values collected in imaging 
        in depth. Units are in :math:`\Omega {.m}` not :math:`log10(\Omega {.m})`
    
    :param data: DataFrame - It is composed of spacing values `AB` and  the 
        apparent resistivity values `rhoa`. If `data` is given, params `AB` and 
        `rhoa` should be kept to ``None``.   
    
    :param typeofop: str - Type of operation to apply  to the resistivity 
        values `rhoa` of the duplicated spacing points `AB`. The default 
        operation is ``mean``. 
    
    :param outdf: bool - Outpout a new dataframe composed of `AB` and `rhoa` 
        data renewed. 
    
    :returns: 
        - Tuple of (AB, rhoa): New values computed from `typeofop` 
        - DataFrame: New dataframe outputed only if ``outdf`` is ``True``.
        
    :note: 
        By convention `AB` and `MN` are half-space dipole length which 
        correspond to `AB/2` and `MN/2` respectively. 
    
    :Example: 
        
        >>> from watex.tools.exmath import vesDataOperator
        >>> from watex.tools.coreutils import vesSelector 
        >>> data = vesSelector (f= 'data/ves/ves_gbalo.xlsx')
        >>> len(data)
        ... (32, 3) # include the potentiel electrode values `MN`
        >>> df= vesDataOperator(data.AB, data.resistivity,
                                typeofop='leaveOneOut', outdf =True)
        >>> df.shape 
        ... (26, 2) # exclude `MN` values and reduce(-6) the duplicated values. 
    """
    op = copy.deepcopy(typeofop) 
    typeofop= str(typeofop).lower()
    if typeofop not in ('none', 'mean', 'median', 'leaveoneout'):
        raise ValueError(
            f'Unacceptable argument {op!r}. Use one of the following '
            f'argument {smart_format([None,"mean", "median", "leaveOneOut"])}'
            ' instead.')

    typeofop ='mean' if typeofop =='none' else typeofop 
    
    if data is not None: 
        data = _assert_all_types(data, pd.DataFrame)
        rhoa = np.array(data.resistivity )
        AB= np.array(data.AB) 
    
    AB= np.array( _assert_all_types(
        AB, np.ndarray, list, tuple, pd.Series)) 
    rhoa = np.array( _assert_all_types(
        rhoa, np.ndarray, list, tuple, pd.Series))
 
    if len(AB)!= len(rhoa): 
        raise Wex.VESError(
            'Deep measurement `AB` must have the same size with '
            ' the collected apparent resistivity `rhoa`.'
            f' {len(AB)} and {len(rhoa)} were given.')
    
    #----> When exploring in deeper, after changing the distance 
    # of MN , measure are repeated at the same points. So, we will 
    # selected these points and take the mean values of tyhe resistivity 
    
    # make copies 
    AB_ = AB.copy() ; rhoa_= rhoa.copy() 
    # find the duplicated values 
    # with np.errstate(all='ignore'):
    mask = np.zeros_like (AB_, dtype =bool) 
    mask[np.unique(AB_, return_index =True)[1]]=True 
    dup_values = AB_[~mask]
    
    indexes, = np.where(AB_==dup_values)
    #make a copy of unique values and filled the duplicated
    # values by their corresponding mean resistivity values 
    X, rindex  = np.unique (AB_, return_index=True); Y = rhoa_[rindex]
    d0= np.zeros_like(dup_values)
    for ii, d in enumerate(dup_values): 
       index, =  np.where (AB_==d)
       if typeofop =='mean': 
           d0[ii] = rhoa_[index].mean() 
       elif typeofop =='median': 
           d0[ii] = np.median(rhoa_[index])
       elif typeofop =='leaveoneout': 
           d0[ii] = np.random.permutation(rhoa_[index])[0]
      
    maskr = np.isin(X, dup_values, assume_unique=True)
    Y[maskr] = d0
    
    return (X, Y) if not outdf else pd.DataFrame (
        {'AB': X,'resistivity':Y}, index =range(len(X)))

# XXXTODO 
def invertVES (data: DataFrame[DType[float|int]] = None, 
               rho0: float = None , 
               h0 : float = None, 
               typeof : str = 'HMCMC', 
               
               **kwd)->Tuple [Array]: 
    """ Invert the |VES| data collected in the exporation area.
    
    :param data: Dataframe pandas - contains the depth measurement AB from 
        current electrodes, the potentials electrodes MN and the collected 
        apparents resistivities. 
    
    :param rho0: float - Value of the starting resistivity model. If ``None``, 
        `rho0` should be the half minumm value of the apparent resistivity  
        collected. Units is in Ω.m not log10(Ω.m)
        
    :param h0: float -  Thickness  in meter of the first layers in meters.
         If ``None``, it should be the minimum thickess as possible ``1.`` m. 
    
    :param typeof: str - Type of inversion scheme. The defaut is Hybrid Monte 
        Carlo (HMC) known as ``HMCMC`` . Another scheme is Bayesian neural network
        approach (``BNN``). 
    
    :param kws: dict - Additionnal keywords arguments from |VES| data operations. 
        See :func:`watex.utils.exmath.vesDataOperator` for futher details. 
    
    """
    
    X, Y = vesDataOperator(data =data, **kwd)
    
    pass 

    
def ohmicArea(
        data: DataFrame[DType[float|int]] = None, 
        ohmSkey: float = 45., 
        sum : bool = False, 
        objective: str = 'ohmS',
        **kws
) -> float: 
    r""" 
    Compute the ohmic-area from the |VES| data collected in exploration area. 
    
    Parameters 
    -----------
    * data: Dataframe pandas - contains the depth measurement AB from current 
        electrodes, the potentials electrodes MN and the collected apparents 
        resistivities. 
    
    * ohmSkey: float - The depth in meters from which one expects to find a 
        fracture zone outside of pollutions. Indeed, the `ohmSkey` parameter is 
        used to  speculate about the expected groundwater in the fractured rocks 
        under the average level of water inrush in a specific area. For instance 
        in `Bagoue region`_ , the average depth of water inrush
        is around ``45m``. So the `ohmSkey` can be specified via the water inrush 
        average value. 
        
    * objective: str - Type operation to outputs. By default, the function 
        outputs the value of pseudo-area in :math:`$ \Omega .m^2 $`. However, for 
        plotting purpose by setting the argument to ``view``, its gives an 
        alternatively outputs of X and Y, recomputed and projected as weel as 
        the X and Y values of the expected fractured zone. Where X is the AB dipole 
        spacing when imaging to the depth and Y is the apparent resistivity computed 
    
    kws: dict - Additionnal keywords arguments from |VES| data operations. 
        See :func:`watex.tools.exmath.vesDataOperator` for futher details. 
    
    Returns 
    --------
    List of twice tuples:
        
        - Tuple(ohmS, error, roots): 
            - `ohmS`is the pseudo-area computed expected to be a fractured zone 
            - `error` is the integration error 
            - `roots` is the integration  boundaries of the expected fractured 
                zone where the basement rocks is located above the resistivity  
                transform function. At these points both curves values equal 
                to null.
        - Tuple `(XY, fit XY,XYohmSarea)`: 
            - `XY` is the ndarray(nvalues, 2) of the operated  of `AB` dipole 
                spacing and resistivity `rhoa` values. 
            - `fit XY` is the fitting ndarray(nvalues, 2) uses to redraw the 
                dummy resistivity transform function.
            - `XYohmSarea` is `ndarray(nvalues, 2)` of the dipole spacing and  
                resistiviy values of the expected fracture zone. 
 
    Raises
    -------
    VESError 
        If the `ohmSkey` is greater or equal to the maximum investigation 
        depth in meters. 
    
    Examples 
    ---------
    >>> from watex.tools.exmath import ohmicArea 
    >>> from watex.tools.coreutils import vesSelector 
    >>> data = vesSelector (f= 'data/ves/ves_gbalo.xlsx') 
    >>> (ohmS, err, roots), *_ = ohmicArea(data = data, ohmSkey =45, sum =True ) 
    ... (13.46012197818152, array([5.8131967e-12]), array([45.        , 98.07307307]))
    # pseudo-area is computed between the spacing point AB =[45, 98] depth. 
    >>> _, (XY.shape, XYfit.shape, XYohms_area.shape) = ohmicArea(
                    AB= data.AB, rhoa =data.resistivity, ohmSkey =45, 
                    objective ='plot') 
    ... ((26, 2), (1000, 2), (8, 2))    
    
    
    See also
    ---------
    
    The `ohmS` value calculated from `pseudo-area` is a fully data-driven 
    parameter and is used to evaluate a pseudo-area of the fracture zone  
    from the depth where the basement rock is supposed to start. Usually, 
    when exploring deeper using the |VES|, we are looking for groundwater
    in thefractured rock that is outside the anthropic pollution (Biemi, 1992).  
    Since the VES is an indirect method, we cannot ascertain whether the 
    presumed fractured rock contains water inside. However, we assume that 
    the fracture zone could exist and should contain groundwater. Mathematically,
    based on the VES1D model proposed by `Koefoed, O. (1976)`_ , we consider
    a function :math:`$ \rho_T(l)$`, a set of reducing resistivity transform 
    function to lower the boundary plane at half the current electrode  
    spacing :math:`$(l)$`. From the sounding curve :math:`$\rho_T(l)$`,  
    curve an imaginary basement rock :math:`$b_r (l)$` of slope equal to ``45°`` 
    with the horizontal :math:`$h(l)$` was created. A pseudo-area :math:`$S(l)$`
    should be defined by extending from :math:`$h(l)$` the :math:`$b_r (l)$` 
    curve when the sounding curve :math:`$\rho_T(l)$`  is below :math:`$b_r(l)$`,
    otherwise :math:`$S(l)$` is equal to null. The computed area is called the 
    ohmic-area :math:`$ohmS$` expressed in :math:`$\Omega .m^2$` and constitutes
    the expected *fractured zone*. Thus :math:`$ohmS$` ≠ :math:`0` confirms the 
    existence of the fracture zone while of :math:`$Ohms=0$` raises doubts. 
    The equation to determine the parameter is given as:
    
    .. math::
    
        ohmS & = &\int_{ l_i}^{l_{i+1}} S(l)dl \quad {s.t.} 
        
        S(l) & = &  b_r (l)  - \rho_T (l) \quad \text{if} \quad  b_r (l)  > \rho_T (l) \\
             & = & 0.  \quad \text{if}  \quad b_r (l)  \leq \rho_T (l) 
        
        b_r(l) & = & l + h(l)  \quad ; \quad h(l) = \beta  
        
        \rho_T(l) & = & l^2 \int_{0}^{\infty} T_i( \lambda ) h_1( \lambda l) \lambda d\lambda 
       
    where :math:`l_i \quad \text{and} \quad l_{i+1}` solve the equation 
    :math:`S(l=0)`; :math:`$l$` is half the current electrode spacing :math:`$AB/2$`,
    and :math:`$h_1$` denotes the first-order of the Bessel function of the first 
    kind, :math:`$ \beta $` is the coordinate value on y-axis direction of the
    intercept term of the :math:`$b_r(l)$` and :math:`$h(l)$`, :math:`$T_i(\lambda )$`
    resistivity transform function,  :math:`$lamda$` denotes the integral variable,
    where n denotes the number of layers, :math:`$rho_i$` and :math:`$h_i$` are 
    the resistivity and thickness of the :math:`$i-th$` layer, respectively.
    Get more explanations and cleareance of formula  in the paper of 
    `Kouadio et al 2022`_. 
        
    References
    ----------
    *Kouadio, K.L., Nicolas, K.L., Binbin, M., Déguine, G.S.P. & Serge*, 
        *K.K. (2021, October)* Bagoue dataset-Cote d’Ivoire: Electrical profiling,
        electrical sounding and boreholes data, Zenodo. doi:10.5281/zenodo.5560937
    
    *Koefoed, O. (1970)*. A fast method for determining the layer distribution 
        from the raised kernel function in geoelectrical sounding. Geophysical
        Prospecting, 18(4), 564–570. https://doi.org/10.1111/j.1365-2478.1970.tb02129.x
         
    *Koefoed, O. (1976)*. Progress in the Direct Interpretation of Resistivity 
        Soundings: an Algorithm. Geophysical Prospecting, 24(2), 233–240.
        https://doi.org/10.1111/j.1365-2478.1976.tb00921.x
        
    *Biemi, J. (1992)*. Contribution à l’étude géologique, hydrogéologique et par télédétection
        de bassins versants subsaheliens du socle précambrien d’Afrique de l’Ouest:
        hydrostructurale hydrodynamique, hydrochimie et isotopie des aquifères discontinus
        de sillons et aires gran. In Thèse de Doctorat (IOS journa, p. 493). Abidjan, Cote d'Ivoire
        
    .. _Kouadio et al 2022: https://doi.org/10.1029/2021WR031623 or refer to 
        the paper `FlowRatePredictionWithSVMs <https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1029/2021WR031623>`_
    .. _Koefoed, O. (1970): https://doi.org/10.1111/j.1365-2478.1970.tb02129.x
    .. _Koefoed, O. (1976): https://doi.org/10.1111/j.1365-2478.1976.tb00921.x
    .. _Bagoue region: https://en.wikipedia.org/wiki/Bagou%C3%A9
    .. |VES| replace: Vertical Electrical Sounding 
    
    """
    
    objkeys = ( 'ohms','none','eval', 'area', 'ohmic','true',
               'plot', 'mpl', 'false', 'graph','visual', 'view')
    
    objr = copy.deepcopy(objective)
    objective = str(objective).lower()
    compout, viewout = np.split(np.array(objkeys), 2)
    for oo, pp in zip(compout, viewout): 
        if objective.find(oo)>=0 :
            objective ='ohms'; break 
        elif objective.find(pp)>=0: 
            objective ='graph'; break 
    
    if objective not in list(objkeys)+ ['full', 'coverall']: 
        raise ValueError(f"Unacceptable argument {str(objr)!r}. Objective"
                         " argument can only be 'ohmS' for pseudo-area"
                        " evaluation or 'graph' for visualization outputs."
                        )

    bound0=[]
    X, Y = vesDataOperator(data =data, **kws)
    
    try : 
       ohmSkey = str(ohmSkey).lower().replace('m', '')
       if ohmSkey.find('none')>=0 : 
           ohmSkey = X.max()/2 
       ohmSkey = float(ohmSkey)
    except: 
        raise ValueError (f'Could not convert value {ohmSkey!r} to float')
        
    if ohmSkey >= X.max(): 
        raise Wex.VESError(f"The startpoint 'ohmSkey={ohmSkey}m'is expected "
                           f"to be less than the 'maxdepth={X.max()}m'.")

    #-------> construct the fitting curves for 1000 points 
    # create the polyfit function fitting raw(f) from coefficents 
    # (coefs) of the initial function 
    f_rhotl, x_new, y_projected = fitfunc (X, Y)
    
    # Finding the intercepts between the fitting curve and the dummy 
    # basement curves 
    #--> e. g. start from 20m (oix) --> ... searching  and find the index 
    oIx = np.argmin (np.abs(X - ohmSkey)) 
    # from this index (oIx) , read the remain depth. 
    oB = X[int(oIx):] # from O-> end [OB]
    #--< construct the basement curve from the index of ohmSkey
    f_brl, beta = dummy_basement_curve( f_rhotl,  ohmSkey)
    # 1000 points from OB (xx)
    xx = np.linspace(oB.min(), oB.max(), 1000)
    b45_projected= f_brl(xx)
    
    # create a fit function for b45 and find the limits 
    # find the intersection between the b45_projected values and 
    # fpartial projected values are the solution of equations f45 -fpartials 
    diff_arr = b45_projected - f_rhotl(xx) #ypartial_projected 

    # # if f-y < 0 => f< y so fitting curve is under the basement curve 
    # # we keep the limit indexes for integral computation 
    # # we want to keep the 
    array_masked = np.ma.masked_where (diff_arr < 0 , diff_arr , copy =True)
    # get indexes of valid values 
    indexes, = array_masked.nonzero() 
 
    try : 
        ib_indexes = find_bound_for_integration(indexes, b0=bound0)
    except : 
        bound0=[] #initialize the bounds lists 
        ib_indexes =find_limit_for_integration(indexes, b0= bound0) 
    
    roots = xx[ib_indexes] 
    f45, *_ = fitfunc(oB, Y[oIx:])
    ff = f45 - f_rhotl 
    pairwise_r = np.split(roots, len(roots)//2 ) if len(
        roots) > 2 else [np.array(roots)]
    ohmS = np.zeros((len(pairwise_r,)))
    err_ohmS = np.zeros((len(pairwise_r,)))
    for ii, (inf, sup) in enumerate(pairwise_r): 
        values, err = integrate.quad(ff, a = inf, b = sup)
        ohmS[ii] = np.zeros((1,)) if values < 0 else values 
        err_ohmS[ii] = err
        

    if sum: 
        ohmS = ohmS.sum()  
    
    rv =[
        (ohmS, err_ohmS, roots),
         ( np.hstack((X[:, np.newaxis], Y[:, np.newaxis]) ), 
             np.hstack((x_new[:, np.newaxis], y_projected[:, np.newaxis])), 
             np.hstack((oB[:, np.newaxis], f_brl(oB)[:, np.newaxis]) )
         ) 
        ]    
        
    for ii, ( obj , ix) in enumerate( zip(('ohms', 'graph'), [1, -1])): 
        if objective ==obj : 
            rv[ii + ix ]= (None, None, None)
            break 

    return rv
 

def _type_mechanism (
        cz: Array |List[float],
        dipolelength : float =10.
) -> Tuple[str, float]: 
    """ Using the type mechanism helps to not repeat several time the same 
    process during the `type` definition. 
    
    :param cz: array-like - conductive zone; is a subset of the whole |ERP| 
        survey line.
        
    .. note:: 
        Here, the position absolutely refer to the global minimum 
        resistivity value.
        
    :Example:
        >>> import numpy as np 
        >>> from watex.tools.exmath import _type_mechanism
        >>> rang = random.RandomState(42)
        >>> test_array2 = rang.randn (7)
        >>> _type_mechanism(np.abs(test_array2))
        ... ('yes', 60.0)
        
    """
    s_index  = np.argmin(cz)
    lc , rc = cz[:s_index +1] , cz[s_index :]
    lm , rm = lc.max() , rc.max() 
    # get the index of different values
    ixl, = np.where (lc ==lm) ; ixr, = np.where (rc ==rm) 
    # take the far away value if the index is more than one 
    ixl = ixl[0] if len(ixl) > 1 else ixl
    ixr =ixr [-1] + s_index  if len(ixr) > 1 else ixr  + s_index 
    
    wcz = dipolelength * abs (int(ixl) - int(ixr)) 
    status = 'yes' if wcz > 4 * dipolelength  else 'no'
    
    return status, wcz 

def type_ (erp: Array[DType[float]] ) -> str: 
    """ Compute the type of anomaly. 
    
    .. |ERP| replace: Electrical Resistivity Profiling 
    
    The type parameter is defined by the African Hydraulic Study 
    Committee report (CIEH, 2001). Later it was implemented by authors such as 
    (Adam et al., 2020; Michel et al., 2013; Nikiema, 2012). `Type` comes to 
    help the differenciation of two or several anomalies with the same `shape`.
    For instance, two anomalies with the same shape ``W`` will differ 
    from the order of priority of their types. The `type` depends on the lateral 
    resistivity distribution of underground (resulting from the pace of the 
    apparent resistivity curve) along with the whole |ERP| survey line. Indeed, 
    four types of anomalies were emphasized:
        
        **"EC"**, **"CB2P"**, **"NC"** and **"CP"**. 
        
    For more details refers to references. 
    
    :param erp: array-like - Array of |ERP| line composed of apparent 
        resistivity values. 
    
    :return: str -The `type` of anomaly. 
    
    :Example: 
        
        >>> import numpy as np 
        >>> from watex.tools.exmath import type_
        >>> rang = random.RandomState(42)
        >>> test_array2 = rang.randn (7)
        >>> type_(np.abs(test_array2))
        ... 'EC'
        >>> long_array = np.abs (rang.randn(71))
        >>> type(long_array)
        ... 'PC'
        
        
    References
    ----------- 
    
    *Adam, B. M., Abubakar, A. H., Dalibi, J. H., Khalil Mustapha,M., & Abubakar,*
        *A. H. (2020)*. Assessment of Gaseous Emissions and Socio-Economic Impacts
        From Diesel Generators used in GSM BTS in Kano Metropolis. African Journal 
        of Earth and Environmental Sciences, 2(1),517–523. https://doi.org/10.11113/ajees.v3.n1.104
    
    *CIEH. (2001)*. L’utilisation des méthodes géophysiques pour la recherche
        d’eaux dans les aquifères discontinus. Série Hydrogéologie, 169.
        
    *Michel, K. A., Drissa, C., Blaise, K. Y., & Jean, B. (2013)*. Application 
        de méthodes géophysiques à l ’ étude de la productivité des forages
        d ’eau en milieu cristallin : cas de la région de Toumodi 
        ( Centre de la Côte d ’Ivoire). International Journal of Innovation 
        and Applied Studies, 2(3), 324–334.
    
    *Nikiema, D. G. C. (2012)*. Essai d‘optimisation de l’implantation géophysique
        des forages en zone de socle : Cas de la province de Séno, Nord Est 
        du Burkina Faso (IRD). (I. / I. Ile-de-France, Ed.). IST / IRD 
        Ile-de-France, Ouagadougou, Burkina Faso, West-africa. Retrieved 
        from http://documentation.2ie-edu.org/cdi2ie/opac_css/doc_num.php?explnum_id=148
    
    """
    # split array
    type_ ='PC' # initialize type 
    
    erp = _assert_all_types(erp, tuple, list, np.ndarray, pd.Series)
    erp = np.array (erp)
    
    try : 
        ssets = np.split(erp, len(erp)//7)
    except ValueError: 
        # get_indices 
        if len(erp) < 7: ssets =[erp ]
        else :
            remains = len(erp) % 7 
            indices = np.arange(7 , len(erp) - remains , 7)
            ssets = np.split(erp , indices )
    
    status =list()
    for czx in ssets : 
        sta , _ = _type_mechanism(czx)
        status.append(sta)

    if len(set (status)) ==1: 
        if status [0] =='yes':
            type_= 'EC' 
        elif status [0] =='no':
            type_ ='NC' 
    elif len(set(status)) ==2: 
        yes_ix , = np.where (np.array(status) =='yes') 
        # take the remain index 
        no_ix = np.array (status)[len(yes_ix):]
        
        # check whether all indexes are sorted 
        sort_ix_yes = all(yes_ix[i] < yes_ix[i+1]
                      for i in range(len(yes_ix) - 1))
        sort_ix_no = all(no_ix[i] < no_ix[i+1]
                      for i in range(len(no_ix) - 1))
        
        # check whether their difference is 1 even sorted 
        if sort_ix_no == sort_ix_yes == True: 
            yes = set ([abs(yes_ix[i] -yes_ix[i+1])
                        for i in range(len(yes_ix)-1)])
            no = set ([abs(no_ix[i] -no_ix[i+1])
                        for i in range(len(no_ix)-1)])
            if yes == no == {1}: 
                type_= 'CB2P'
                
    return type_ 
        
def shape (
    cz : Array | List [float], 
    s : Optional [str, int] = ..., 
    p:  SP =  ...,     
) -> str: 
    """ Compute the shape of anomaly. 
    
    The `shape` parameter is mostly used in the basement medium to depict the
    better conductive zone for the drilling location. According to Sombo et
    al. (2011; 2012), various shapes of anomalies can be described such as: 
        
        **"V"**, **"U"**, **"W"**, **"M"**, **"K"**, **"C"**, and **"H"**
    
    The `shape` consists to feed the algorithm with the |ERP| resistivity 
    values by specifying the station :math:`$(S_{VES})$`. Indeed, 
    mostly, :math:`$S_{VES}$` is the station with a very low resistivity value
    expected to be the drilling location. 
    
    :param cz: array-like -  Conductive zone resistivity values 
    :param s: int, str - Station position index or name.
    :param p: Array-like - Should be the position of the conductive zone.
    
    .. note:: 
        If `s` is given, `p` should be provided. If `p` is missing an
        error will raises.
    
    :return: str - the shape of anomaly. 
    
    :Example: 
        >>> import numpy as np 
        >>> rang = random.RandomState(42)
        >>> from watex.tools.exmath import shape_ 
        >>> test_array1 = np.arange(10)
        >>> shape_ (test_array1)
        ...  'C'
        >>> test_array2 = rang.randn (7)
        >>> _shape(test_array2)
        ... 'K'
        >>> test_array3 = np.power(10, test_array2 , dtype =np.float32) 
        >>> _shape (test_array3) 
        ... 'K'   # does not change whatever the resistivity values.
    
    References 
    ----------
    
    *Sombo, P. A., Williams, F., Loukou, K. N., & Kouassi, E. G. (2011)*.
        Contribution de la Prospection Électrique à L’identification et à la 
        Caractérisation des Aquifères de Socle du Département de Sikensi 
        (Sud de la Côte d’Ivoire). European Journal of Scientific Research,
        64(2), 206–219.
    
    *Sombo, P. A. (2012)*. Application des methodes de resistivites electriques
        dans la determination et la caracterisation des aquiferes de socle
        en Cote d’Ivoire. Cas des departements de Sikensi et de Tiassale 
        (Sud de la Cote d’Ivoire). Universite Felix Houphouet Boigny.
    
    .. |ERP| replace:: Electrical Resistivity Profiling
    
    """
    shape = 'V' # initialize the shape with the most common 
    
    cz = _assert_all_types( cz , tuple, list, np.ndarray, pd.Series) 
    cz = np.array(cz)
    # detect the staion position index
    if s is (None or ... ):
        s_index = np.argmin(cz)
    elif s is not None: 
        if isinstance(s, str): 
            try: 
                s= int(s.lower().replace('s', '')) 
            except: 
                if p is ( None or ...): 
                    raise Wex.StationError(
                        "Need the positions `p` of the conductive zone "
                        "to be supplied.'NoneType' is given.")
                    
                s_index,*_ = detect_station_position(s,p)  
            else : s_index = s 
        else : 
            s_index= _assert_all_types(s, int)
            
    if s_index >= len(cz): 
        raise Wex.StationError(
            f"Position should be less than '7': got '{s_index}'")
    lbound , rbound = cz[:s_index +1] , cz[s_index :]
    ls , rs = lbound[0] , rbound [-1] # left side and right side (s) 
    lminls, = argrelextrema(lbound, np.less)
    lminrs, = argrelextrema(rbound, np.less)
    lmaxls, = argrelextrema(lbound, np.greater)
    lmaxrs, = argrelextrema(rbound, np.greater)
    # median helps to keep the same shape whatever 
    # the resistivity values 
    med = np.median(cz)   
 
    if (ls >= med and rs < med ) or (ls < med and rs >= med ): 
        if len(lminls)  == 0 and len(lminrs) ==0 : 
            shape =  'C' 
        elif (len(lminls) ==0 and len(lminrs) !=0) or (
                len(lminls) !=0 and len(lminrs)==0) :
            shape = 'K'
        
    elif (ls and rs) > med : 
        if len(lminls) ==0 and len(lminrs) ==0 :
            shape = 'U'
        elif (len(lminls) ==0 and len(lminrs) ==1 ) or  (
                len(lminrs) ==0 and len(lminls) ==1): 
            shape = 'H'
        elif len(lminls) >=1 and len(lminrs) >= 1 : 
            return 'W'
    elif (ls < med ) and rs < med : 
        if (len(lmaxls) >=1  and len(lmaxrs) >= 0 ) or (
                len(lmaxls) <=0  and len(lmaxrs) >=1): 
            shape = 'M'
    
    return shape
 
@refAppender(__doc__)
@docSanitizer()    
def scalePosition(
        ydata: Array | SP | Series | DataFrame ,
        xdata: Array| Series = None, 
        func : Optional [F] = None ,
        c_order: Optional[int|str] = 0,
        show: bool =False, 
        **kws): 
    """ Correct data location or position and return new corrected location 
    
    Parameters 
    ----------
    ydata: array_like, series or dataframe
        The dependent data, a length M array - nominally ``f(xdata, ...)``.
        
    xdata: array_like or object
        The independent variable where the data is measured. Should usually 
        be an M-length sequence or an (k,M)-shaped array for functions with
        k predictors, but can actually be any object. If ``None``, `xdata` is 
        generated by default using the length of the given `ydata`.
        
    func: callable 
        The model function, ``f(x, ...)``. It must take the independent variable 
        as the first argument and the parameters to fit as separate remaining
        arguments. The default `func` is ``linear`` function i.e  for ``f(x)= ax +b``. 
        where `a` is slope and `b` is the intercept value. Setting your own 
        function for better fitting is recommended. 
        
    c_order: int or str
        The index or the column name if ``ydata`` is given as a dataframe to 
        select the right column for scaling.
    show: bool 
        Quick visualization of data distribution. 

    kws: dict 
        Additional keyword argument from  `scipy.optimize_curvefit` parameters. 
        Refer to `scipy.optimize.curve_fit`_.  
        
    Returns 
    --------
    - ydata - array -like - Data scaled 
    - popt - array-like Optimal values for the parameters so that the sum of 
        the squared residuals of ``f(xdata, *popt) - ydata`` is minimized.
    - pcov - array like The estimated covariance of popt. The diagonals provide
        the variance of the parameter estimate. To compute one standard deviation 
        errors on the parameters use ``perr = np.sqrt(np.diag(pcov))``. How the
        sigma parameter affects the estimated covariance depends on absolute_sigma 
        argument, as described above. If the Jacobian matrix at the solution
        doesn’t have a full rank, then ‘lm’ method returns a matrix filled with
        np.inf, on the other hand 'trf' and 'dogbox' methods use Moore-Penrose
        pseudoinverse to compute the covariance matrix.
        
    Examples
    --------
    >>> from watex.tools import erpSelector, scalePosition 
    >>> df = erpSelector('data/erp/l10_gbalo.xlsx') 
    >>> df.columns 
    ... Index(['station', 'resistivity', 'longitude', 'latitude', 'easting',
           'northing'],
          dtype='object')
    >>> # correcting northing coordinates from easting data 
    >>> northing_corrected, popt, pcov = scalePosition(ydata =df.northing , 
                                               xdata = df.easting, show=True)
    >>> len(df.northing.values) , len(northing_corrected)
    ... (20, 20)
    >>> popt  # by default popt =(slope:a ,intercept: b)
    ...  array([1.01151734e+00, 2.93731377e+05])
    >>> # corrected easting coordinates using the default x.
    >>> easting_corrected, *_= scalePosition(ydata =df.easting , show=True)
    >>> df.easting.values 
    ... array([790284, 790281, 790277, 790270, 790265, 790260, 790254, 790248,
    ...       790243, 790237, 790231, 790224, 790218, 790211, 790206, 790200,
    ...       790194, 790187, 790181, 790175], dtype=int64)
    >>> easting_corrected
    ... array([790288.18571705, 790282.30300999, 790276.42030293, 790270.53759587,
    ...       790264.6548888 , 790258.77218174, 790252.88947468, 790247.00676762,
    ...       790241.12406056, 790235.2413535 , 790229.35864644, 790223.47593938,
    ...       790217.59323232, 790211.71052526, 790205.8278182 , 790199.94511114,
    ...       790194.06240407, 790188.17969701, 790182.29698995, 790176.41428289])
    
    """
    def linfunc (x, a, b): 
        """ Set the simple linear function"""
        return a * x + b 
        
    if str(func).lower() in ('none' , 'linear'): 
        func = linfunc 
    elif not hasattr(func, '__call__') or not inspect.isfunction (func): 
        raise TypeError(
            f'`func` argument is a callable not {type(func).__name__!r}')
        
    ydata = _assert_all_types(ydata, list, tuple, np.ndarray,
                              pd.Series, pd.DataFrame  )
    c_order = _assert_all_types(c_order, int, float, str)
    try : c_order = int(c_order) 
    except: pass 

    if isinstance(ydata, pd.DataFrame): 
        if c_order ==0: 
            warnings.warn("The first column of the data should be considered"
                          " as the `y` target.")
        if c_order is None: 
            raise TypeError('Dataframe is given. The `c_order` argument should '
                            'be defined for column selection. Use column name'
                            ' instead')
        if isinstance(c_order, str): 
            # check whether the value is on the column name
            if c_order.lower() not in list(map( 
                    lambda x :x.lower(), ydata.columns)): 
                raise ValueError (
                    f'c_order {c_order!r} not found in {list(ydata.columns)}'
                    ' Use the index instead.')
                # if c_order exists find the index and get the 
                # right column name 
            ix_c = list(map( lambda x :x.lower(), ydata.columns)
                        ).index(c_order.lower())
            ydata = ydata.iloc [:, ix_c] # series 
        elif isinstance (c_order, (int, float)): 
            c_order =int(c_order) 
            if c_order >= len(ydata.columns): 
                raise ValueError(
                    f"`c_order`'{c_order}' should be less than the number of " 
                    f"given columns '{len(ydata.columns)}'. Use column name instead.")
            ydata= ydata.iloc[:, c_order]
            
    ydata = np.array(ydata)
    if xdata is None: 
        xdata = np.linspace(0, 4, len(ydata))
    if len(xdata) != len(ydata): 
        raise ValueError(" `x` and `y` arrays must have the same length."
                        "'{len(xdata)}' and '{len(ydata)}' are given.")
        
    popt, pcov = curve_fit(func, xdata, ydata, **kws)
    ydata_new = func(xdata, *popt)
    
    if show:
        plt.plot(xdata, ydata, 'b-', label='data')
        plt.plot(xdata, func(xdata, *popt), 'r-',
             label='fit: a=%5.3f, b=%5.3f' % tuple(popt))
        plt.xlabel('x')
        plt.ylabel('y')
        plt.legend()
        plt.show()
        
    return ydata_new, popt, pcov 


def __sves__ (
        s_index: int  , 
        cz: Array | List[float], 
) -> Tuple[Array, Array]: 
    """ Divide the conductive zone in leftzone and rightzone from 
    the drilling location index . 

    :param s_index - station location index expected for dilling location. 
        It refers to the position of |VES|. 
        
    :param cz: array-like - Conductive zone . 
    
    :returns: 
        - <--Sves: Left side of conductive zone from |VES| location. 
        - --> Sves: Right side of conductive zone from |VES| location. 
        
    .. note:: Both sides included the  |VES| `Sves` position.
    .. |VES| replace:: Vertical Electrical Sounding 
    """
    try:  s_index = int(s_index)
    except: raise TypeError(
        f'Expected integer value not {type(s_index).__name__}')
    
    s_index = _assert_all_types( s_index , int)
    cz = _assert_all_types(cz, np.ndarray, pd.Series, list, tuple )

    rmax_ls , rmax_rs = max(cz[:s_index  + 1]), max(cz[s_index  :]) 
    # detect the value of rho max  (rmax_...) 
    # from lower side bound of the anomaly.
    rho_ls= rmax_ls if rmax_ls  <  rmax_rs else rmax_rs 
    
    side =... 
    # find with positions 
    for _, sid  in zip((rmax_ls , rmax_rs ) , ('leftside', 'rightside')) : 
            side = sid ; break 
        
    return (rho_ls, side), (rmax_ls , rmax_rs )


def detect_station_position (
        s : Union[str, int] ,
        p: SP, 
) -> Tuple [int, float]: 
    """ Detect station position and return the index in positions
    
    :param s: str, int - Station location  in the position array. It should 
        be the positionning of the drilling location. If the value given
        is type string. It should be match the exact position to 
        locate the drilling. Otherwise, if the value given is in float or 
        integer type, it should be match the index of the position array. 
         
    :param p: Array-like - Should be the  conductive zone as array of 
        station location values. 
            
    :returns: 
        - `s_index`- the position index location in the conductive zone.  
        - `s`- the station position in distance. 
        
    :Example: 
        
        >>> import numpy as np 
        >>> from watex.utils.exmath import detect_station_position 
        >>> pos = np.arange(0 , 50 , 10 )
        >>> detect_station_position (s ='S30', p = pos)
        ... (3, 30.0)
        >>> detect_station_position (s ='40', p = pos)
        ... (4, 40.0)
        >>> detect_station_position (s =2, p = pos)
        ... (2, 20)
        >>> detect_station_position (s ='sta200', p = pos)
        ... WATexError_station: Station sta200 \
            is out of the range; max position = 40
    """
    s = _assert_all_types( s, float, int, str)
    p = _assert_all_types( p, tuple, list, np.ndarray, pd.Series) 
    
    S=copy.deepcopy(s)
    if isinstance(s, str): 
        s =s.lower().replace('s', '').replace('pk', '').replace('ta', '')
        try : 
            s=int(s)
        except : 
            raise ValueError (f'could not convert string to float: {S}')
            
    p = np.array(p, dtype = np.int32)
    dl = (p.max() - p.min() ) / (len(p) -1) 
    if isinstance(s, (int, float)): 
        if s > len(p): # consider this as the dipole length position: 
            # now let check whether the given value is module of the station 
            if s % dl !=0 : 
                raise Wex.WATexError_station  (
                    f'Unable to detect the station position {S}')
            elif s % dl == 0 and s <= p.max(): 
                # take the index 
                s_index = s//dl
                return int(s_index), s_index * dl 
            else : 
                raise Wex.StationError (
                    f'Station {S} is out of the range; max position = {max(p)}'
                )
        else : 
            if s >= len(p): 
                raise Wex.WATexError_station (
                    'Location index must be less than the number of'
                    f' stations = {len(p)}. {s} is gotten.')
            # consider it as integer index 
            # erase the last variable
            # s_index = s 
            # s = S * dl   # find 
            return s , p[s ]
       
    # check whether the s value is in the p 
    if True in np.isin (p, s): 
        s_index ,  = np.where (p ==s ) 
        s = p [s_index]
        
    return int(s_index) , s 
    
def sfi (
        cz: Sub[Array[T, DType[T]]] | List[float] ,
        p: Sub[SP[Array, DType [int]]] | List [int] = None, 
        s: Optional [str] =None, 
        dipolelength: Optional [float] = None, 
        plot: bool = False,
        raw : bool = False,
        **plotkws
) -> float: 
    r""" 
    Compute  the pseudo-fracturing index known as *sfi*. 
    
    The sfi parameter does not indicate the rock fracturing degree in 
    the underground but it is used to speculate about the apparent resistivity 
    dispersion ratio around the cumulated sum of the  resistivity values of 
    the selected anomaly. It uses a similar approach of  IF parameter proposed 
    by `Dieng et al`_ (2004).  Furthermore, its threshold is set to
    :math:`$sqrt{2}$`  for symmetrical anomaly characterized by a perfect 
    distribution of resistivity in a homogenous medium. The formula is
    given by:
    
    .. math::
        
        sfi=\sqrt{(P_a^{*}/P_a )^2+(M_a^{*}/M_a )^2}
    
    where :math:`$P_a$` and :math:`$M_a$` are the anomaly power and the magnitude 
    respectively. :math:`$P_a^{*}$`  is and :math:`$M_a^{*}$` are the projected 
    power and magnitude of the lower point of the selected anomaly.
    
    :param cz: array-like. Selected conductive zone 
    :param p: array-like. Station positions of the conductive zone.
    :param dipolelength: float. If `p` is not given, it will be set 
        automatically using the default value to match the ``cz`` size. 
        The **default** value is ``10.``.
    :param plot: bool. Visualize the fitting curve. *Default* is ``False``. 
    :param raw: bool. Overlaining the fitting curve with the raw curve from `cz`. 
    :param plotkws: dict. `Matplotlib plot`_ keyword arguments. 
    
    
    :Example:
        
        >>> from numpy as np 
        >>> from watex.properties import P 
        >>> from watex.tools.exmath import sfi 
        >>> rang = np.random.RandomState (42) 
        >>> condzone = np.abs(rang.randn (7)) 
        >>> # no visualization and default value `s` with gloabl minimal rho
        >>> pfi = sfi (condzone)
        ... 3.35110143
        >>> # visualize fitting curve 
        >>> plotkws  = dict (rlabel = 'Conductive zone (cz)', 
                             label = 'fitting model',
                             color=f'{P().frcolortags.get("fr3")}', 
                             )
        >>> sfi (condzone, plot= True , s= 5, figsize =(7, 7), 
                  **plotkws )
        ... Out[598]: (array([ 0., 10., 20., 30.]), 1)
        
    References
    ----------
    - See `Numpy Polyfit <https://numpy.org/doc/stable/reference/generated/numpy.polyfit.html>`_
    - See `Stackoverflow <https://stackoverflow.com/questions/10457240/solving-polynomial-equations-in-python>`_
        the answer of AkaRem edited by Tobu and Migilson. 
    - See `Numpy Errorstate <https://numpy.org/devdocs/reference/generated/numpy.errstate.html>`_ and 
        how to implement the context manager. 
    
    """
 
    # Determine the number of curve inflection 
    # to find the number of degree to compose 
    # cz fonction 
    if p is None :
        dipolelength = 10. if dipolelength is  None else dipolelength  
        p = np.arange (0, len(cz) * dipolelength, dipolelength)
   
    if len(p) != len(cz): 
        raise Wex.StationError (
            'Array of position and conductive zone must have the same length:'
            f' `{len(p)}` and `{len(cz)}` were given.')
        
    minl, = argrelextrema(cz, np.less)
    maxl, = argrelextrema(cz,np.greater)
    ixf = len(minl) + len(maxl)
    
    # create the polyfit function f from coefficents (coefs)
    coefs  = np.polyfit(x=p, y=cz, deg =ixf + 1 ) 
    f = np.poly1d(coefs )
    # generate a sample of values to cover the fit function 
    # for degree 2: eq => f(x) =ax2 +bx + c or c + bx + ax2 as 
    # the coefs are aranged.
    # coefs are ranged for index0  =c, index1 =b and index 2=a 
    # for instance for degree =2 
    # model (f)= [coefs[2] + coefs[1] * x  +   coefs [0]* x**2  for x in xmod]
    # where x_new(xn ) = 1000 points generated 
    # thus compute ynew (yn) from the poly function f
    xn  = np.linspace (min(p), max(p), 1000) 
    yn = f(xn)
    
    # solve the system to find the different root 
    # from the min resistivity value bound. 
    # -> Get from each anomaly bounds (leftside and right side ) 
    # the maximum resistivity and selected the minumum 
    # value to project to the other side in order to get 
    # its positions on the station location p.
    if s is not None : 
        # explicity giving s 
        s_ix , spos = detect_station_position(s , p )
        (rho_side, side ), (rho_ls_max  , rho_rs_max) = __sves__(s_ix , cz )
        
    elif s is None: 
        # take the index of min value of cz 
        s_ix  = np.argmin(cz) ; spos = p[s_ix]
        (rho_side, side ), (rho_ls_max  , rho_rs_max) = __sves__(s_ix , cz )
       
    # find the roots from rhoa_side:
    #  f(x) =y => f (x) = rho_side 
    fn = f  - rho_side  
    roots = np.abs(fn.r )
    # detect the rho_side positions 
    ppow = roots [np.where (roots > spos )] if side =='leftside' else roots[
        np.where (roots < spos)]
    ppow = ppow [0] if len (ppow) > 1 else ppow 
    
    # compute sfi 
    pw = power(p) 
    ma= magnitude(cz)
    pw_star = np.abs (p.min() - ppow)
    ma_star = np.abs(cz.min() - rho_side)
    
    with np.errstate(all='ignore'):
        # $\sqrt2# is the threshold 
        sfi = np.sqrt ( (pw_star/pw)**2 + (ma_star / ma )**2 ) % np.sqrt(2)
        if sfi == np.inf : 
            sfi = np.sqrt ( (pw/pw_star)**2 + (ma / ma_star )**2 ) % np.sqrt(2)
 
    if plot: 
        plot_(p,cz,'-ok', xn, yn, raw = raw , **plotkws)
  
    
    return sfi 

@refAppender(__doc__)
def plot_ (
    *args : List [Union [str, Array, ...]],
    figsize: Tuple[int] = None,
    raw : bool = False, 
    style : str = 'seaborn',   
    dtype: str  ='erp',
    kind: Optional[str] = None , 
    **kws
    ) -> None : 
    """ Quick visualization for fitting model, |ERP| and |VES| curves.
    
    :param x: array-like - array of data for x-axis representation 
    :param y: array-like - array of data for plot y-axis  representation
    :param figsize: tuple - Mtplotlib (MPL) figure size; should be a tuple 
         value of integers e.g. `figsize =(10, 5)`.
    :param raw: bool- Originally the `plot_` function is intended for the 
        fitting |ERP| model i.e. the correct value of |ERP| data. However, 
        when the `raw` is set to ``True``, it plots the both curves: The 
        fitting model as well as the uncorrected model. So both curves are 
        overlaining or supperposed.
    :param style: str - Pyplot style. Default is ``seaborn``
    :param dtype: str - Kind of data provided. Can be |ERP| data or |VES| data. 
        When the |ERP| data are provided, the common plot is sufficient to 
        visualize all the data insignt i.e. the default value of `kind` is kept 
        to ``None``. However, when the data collected is |VES| data, the 
        convenient plot for visualization is the ``loglog`` for parameter
        `kind``  while the `dtype` can be set to `VES` to specify the labels 
        into the x-axis. The default value of `dtype` is ``erp`` for common 
        visualization. 
    :param kind:  str - Use to specify the kind of data provided. See the 
        explanation of `dtype` parameters. By default `kind` is set to ``None``
        i.e. its keep the normal plots. It can be ``loglog``, ``semilogx`` and 
        ``semilogy``.
        
    :param kws: dict - Additional `Matplotlib plot`_ keyword arguments. To cus-
        tomize the plot, one can provide a dictionnary of MPL keyword 
        additional arguments like the example below.
    
    :Example: 
        >>> import numpy as np 
        >>> from watex.tools.exmath import plot_ 
        >>> x, y = np.arange(0 , 60, 10) ,np.abs( np.random.randn (6)) 
        >>> KWS = dict (xlabel ='Stations positions', ylabel= 'resistivity(ohm.m)', 
                    rlabel = 'raw cuve', rotate = 45 ) 
        >>> plot_(x, y, '-ok', raw = True , style = 'seaborn-whitegrid', 
                  figsize = (7, 7) ,**KWS )
    
    """
    plt.style.use(style)
    # retrieve all the aggregated data from keywords arguments
    if (rlabel := kws.get('rlabel')) is not None : 
        del kws['rlabel']
    if (xlabel := kws.get('xlabel')) is not None : 
        del kws['xlabel']
    if (ylabel := kws.get('ylabel')) is not None : 
        del kws['ylabel']
    if (rotate:= kws.get ('rotate')) is not None: 
        del kws ['rotate']
        
    if (title:= kws.get ('title')) is not None: 
        del kws ['title']
    x , y, *args = args 
    fig = plt.figure(1, figsize =figsize)
    plt.plot (x, y,*args, 
              **kws)
    if raw: 
        kind = kind.lower(
            ) if isinstance(kind, str) else kind 
        if kind =='semilogx': 
            plt.semilogx (x, y, 
                      color = '{}'.format(P().frcolortags.get("fr1")),
                      label =rlabel, 
                      )
        elif kind =='semilogy': 
            plt.semilogy (x, y, 
                      color = '{}'.format(P().frcolortags.get("fr1")),
                      label =rlabel, 
                      )
        elif kind =='loglog': 
            print('yes')
            plt.loglog (x, y, 
                      color = '{}'.format(P().frcolortags.get("fr1")),
                      label =rlabel, 
                      )
        else: 
            plt.plot (x, y, 
                      color = '{}'.format(P().frcolortags.get("fr1")),
                      label =rlabel, 
                      )
            
    dtype = dtype.lower() if isinstance(dtype, str) else dtype
    
    if dtype is None:
        dtype ='erp'  
    if dtype not in ('erp', 'ves'): kind ='erp' 
    
    if dtype =='erp':
        plt.xticks (x,
                    labels = ['S{:02}'.format(int(i)) for i in x ],
                    rotation = 0. if rotate is None else rotate 
                    )
    elif dtype =='ves': 
        plt.xticks (x,
                    rotation = 0. if rotate is None else rotate 
                    )
        
    plt.xlabel ('Stations') if xlabel is  None  else plt.xlabel (xlabel)
    plt.ylabel ('Resistivity (Ω.m)'
                ) if ylabel is None else plt.ylabel (ylabel)
    
    fig_title_kws = dict (
        t = 'Plot fit model' if dtype =='erp' else title, 
        style ='italic', 
        bbox =dict(boxstyle='round',facecolor ='lightgrey'))
        
    plt.tight_layout()
    fig.suptitle(**fig_title_kws)
    plt.legend ()
    plt.show ()
        
    
def quickplot (arr: Array | List[float], dl:float  =10)-> None: 
    """Quick plot to see the anomaly"""
    
    plt.plot(np.arange(0, len(arr) * dl, dl), arr , ls ='-', c='k')
    plt.show() 
    
    

def magnitude (cz:Sub[Array[float, DType[float]]] ) -> float: 
    r""" 
    Compute the magnitude of selected conductive zone. 
    
    The magnitude parameter is the absolute resistivity value between
    the minimum :math:`\min \rho_a` and maximum :math:`\max \rho_a` 
    value of selected anomaly:
    
    .. math::
    
        magnitude=|\min\rho_a -\max\rho_a|

    :param cz: array-like. Array of apparent resistivity values composing 
        the conductive zone. 
    
    :return: Absolute value of anomaly magnitude in ohm.meters.
    """
    return np.abs (cz.max()- cz.min()) 

def power (p:Sub[SP[Array, DType [int]]] | List[int] ) -> float : 
    """ 
    Compute the power of the selected conductive zone. Anomaly `power` 
    is closely referred to the width of the conductive zone.
    
    The power parameter implicitly defines the width of the conductive zone
    and is evaluated from the difference between the abscissa 
    :math:`$X_{LB}$` and the end :math:`$X_{UB}$` points of 
    the selected anomaly:
    
    .. math::
        
        power=|X_{LB} - X_{UB} |
    
    :param p: array-like. Station position of conductive zone.
    
    :return: Absolute value of the width of conductive zone in meters. 
    
    """
    return np.abs(p.min()- p.max()) 


def _find_cz_bound_indexes (
    erp: Union[Array[float, DType[float]], List[float], pd.Series],
    cz: Union [Sub[Array], List[float]] 
)-> Tuple[int, int]: 
    """ 
    Fetch the limits 'LB' and 'UB' of the selected conductive zone.
    
    Indeed the 'LB' and 'UB' fit the lower and upper boundaries of the 
    conductive zone respectively. 
    
    :param erp: array-like. Apparent resistivities collected during the survey. 
    :param cz: array-like. Array of apparent resistivies composing the  
        conductive zone. 
    
    :return: The index of boundaries 'LB' and 'UB'. 
    
    .. note::
        
        `cz` must be self-containing of `erp`. If ``False`` should raise and error. 
        
    """
    # assert whether cz is a subset of erp. 
    if isinstance( erp, pd.Series): erp = erp.values 

    if not np.isin(True,  (np.isin (erp, cz))):
        raise ValueError ('Expected the conductive zone array being a '
                          'subset of the resistivity array.')
    # find the indexes using np.argwhere  
    cz_indexes = np.argwhere(np.isin(erp, cz)).ravel()
    
    return cz_indexes [0] , cz_indexes [-1] 


def convert_distance_to_m(
        value:T ,
        converter:float =1e3,
        unit:str ='km'
)-> float: 
    """ Convert distance from `km` to `m` or vice versa even a string 
    value is given.
    
    :param value: value to convert. 
    :paramm converter: Equivalent if given in ``km`` rather than ``m``.
    :param unit: unit to convert to.
    
    """
    
    if isinstance(value, str): 
        try:
            value = float(value.replace(unit, '')
                              )*converter if value.find(
                'km')>=0 else float(value.replace('m', ''))
        except: 
            raise TypeError(f"Expected float not {type(value)!r}."
               )
            
    return value
    
    
def get_station_number (
        dipole:float,
        distance:float , 
        from0:bool = False,
        **kws
)-> float: 
    """ Get the station number from dipole length and 
    the distance to the station.
    
    :param distance: Is the distance from the first station to `s` in 
        meter (m). If value is given, please specify the dipole length in 
        the same unit as `distance`.
    :param dipole: Is the distance of the dipole measurement. 
        By default the dipole length is in meter.
    :param kws: :func:`convert_distance_to_m` additional arguments
    
    """
    
    dipole=convert_distance_to_m(dipole, **kws)
    distance =convert_distance_to_m(distance, **kws)

    return  distance/dipole  if from0 else distance/dipole + 1 

@deprecated('Function is going to be removed for the next release ...')
def define_conductive_zone (
        erp: Array | List[float],
        stn: Optional [int] = None,
        sres:Optional [float] = None,
        *, 
        distance:float | None = None , 
        dipole_length:float | None = None,
        extent:int =7): 
    """ Detect the conductive zone from `s`ves point.
    
    :param erp: Resistivity values of electrical resistivity profiling(ERP).
    
    :param stn: Station number expected for VES and/or drilling location.
    
    :param sres: Resistivity value at station number `stn`. 
        If `sres` is given, the auto-search will be triggered to 
        find the station number that fits the resistivity value. 
    
    :param distance: Distance from the first station to `stn`. If given, 
        be sure to provide the `dipole_length`
    :param dipole_length: Length of the dipole. Comonly the distante between 
        two close stations. Since we use config AB/2 
    :param extent: Is the width to depict the anomaly. If provide, need to be 
        consistent along all ERP line. Should keep unchanged for other 
        parameters definitions. Default is ``7``.
    :returns: 
        - CZ:Conductive zone including the station position 
        - sres: Resistivity value of the station number
        - ix_stn: Station position in the CZ
            
    .. note:: 
        If many stations got the same `sres` value, the first station 
        is flagged. This may not correspond to the station number that is 
        searching. Use `sres` only if you are sure that the 
        resistivity value is unique on the whole ERP. Otherwise it's 
        not recommended.
        
    :Example: 
        >>> import numpy as np
        >>> from watex.tools.exmath import define_conductive_zone 
        >>> sample = np.random.randn(9)
        >>> cz, stn_res = define_conductive_zone(sample, 4, extent = 7)
        ... (array([ 0.32208638,  1.48349508,  0.6871188 , -0.96007639,
                    -1.08735204,0.79811492, -0.31216716]),
             -0.9600763919368086, 
             3)
    """
    try : 
        iter(erp)
    except : raise Wex.ArgumentError (
            f'`erp` must be a sequence of values not {type(erp)!r}')
    finally: erp = np.array(erp)
  
    # check the distance 
    if stn is None: 
        if (dipole_length and distance) is not None: 
            stn = get_station_number(dipole_length, distance)
        elif sres is not None: 
            snix, = np.where(erp==sres)
            if len(snix)==0: 
                raise Wex.ParameterNumberError(
                    "Could not  find the resistivity value of the VES "
                    "station. Please provide the right value instead.") 
                
            elif len(snix)==2: 
                stn = int(snix[0]) + 1
        else :
            raise Wex.ArgumentError (
                '`stn` is needed or at least provide the survey '
                'dipole length and the distance from the first '
                'station to the VES station. ')
            
    if erp.size < stn : 
        raise Wex.StationError(
            f"Wrong station number =`{stn}`. Is larger than the "
            f" number of ERP stations = `{erp.size}` ")
    
    # now defined the anomaly boundaries from sn
    stn =  1 if stn == 0 else stn  
    stn -=1 # start counting from 0.
    if extent %2 ==0: 
        if len(erp[:stn]) > len(erp[stn:])-1:
           ub = erp[stn:][:extent//2 +1]
           lb = erp[:stn][len(ub)-int(extent):]
        elif len(erp[:stn]) < len(erp[stn:])-1:
            lb = erp[:stn][stn-extent//2 +1:stn]
            ub= erp[stn:][:int(extent)- len(lb)]
     
    else : 
        lb = erp[:stn][-extent//2:] 
        ub = erp[stn:][:int(extent//2)+ 1]
    
    # read this part if extent anomaly is not reached
    if len(ub) +len(lb) < extent: 
        if len(erp[:stn]) > len(erp[stn:])-1:
            add = abs(len(ub)-len(lb)) # remain value to add 
            lb = erp[:stn][-add -len(lb) - 1:]
        elif len(erp[:stn]) < len(erp[stn:])-1:
            add = abs(len(ub)-len(lb)) # remain value to add 
            ub = erp[stn:][:len(ub)+ add -1] 
          
    conductive_zone = np.concatenate((lb, ub))
    # get the index of station number from the conductive zone.
    ix_stn, = np.where (conductive_zone == conductive_zone[stn])
    ix_stn = int(ix_stn[0]) if len(ix_stn)> 1 else  int(ix_stn)
    
    return  conductive_zone, conductive_zone[stn], ix_stn 
    

#FR0: CED9EF
#FR1: 9EB3DD
#FR2: 9EB3DD
#FR3: 0A4CEE
def shortPlot (sample, cz=None): 
    """ 
    Quick plot to visualize the `sample` line as well as the  selected 
    conductive zone if given.
    
    :param sample: array_like, the electrical profiling array 
    :param cz: array_like, the selected conductive zone. If ``None``, `cz` 
        should be plotted.
    
    :Example: 
        >>> import numpy as np 
        >>> from watex.tools.exmath import shortPlot, define_conductive_zone 
        >>> test_array = np.random.randn (10)
        >>> selected_cz ,*_ = define_conductive_zone(test_array, 7) 
        >>> shortPlot(test_array, selected_cz )
        
    """
    import matplotlib.pyplot as plt 
    fig, ax = plt.subplots(1,1, figsize =(10, 4))
    leg =[]
    ax.scatter (np.arange(len(sample)), sample, marker ='.', c='b')
    zl, = ax.plot(np.arange(len(sample)), sample, 
                  c='r', 
                  label ='Electrical resistivity profiling')
    leg.append(zl)
    if cz is not None: 
        # construct a mask array with np.isin to check whether 
        # `cz` is subset array
        z = np.ma.masked_values (sample, np.isin(sample, cz ))
        # a masked value is constructed so we need 
        # to get the attribute fill_value as a mask 
        # However, we need to use np.invert or tilde operator  
        # to specify that other value except the `CZ` values mus be 
        # masked. Note that the dtype must be changed to boolean
        sample_masked = np.ma.array(
            sample, mask = ~z.fill_value.astype('bool') )
    
        czl, = ax.plot(
            np.arange(len(sample)), sample_masked, 
            ls='-',
            c='#0A4CEE',
            lw =2, 
            label ='Conductive zone')
        leg.append(czl)

    ax.set_xticks(range(len(sample)))
    ax.set_xticklabels(
        ['S{0:02}'.format(i+1) for i in range(len(sample))])
    
    ax.set_xlabel('Stations')
    ax.set_ylabel('app.resistivity (ohm.m)')
    ax.legend( handles = leg, 
              loc ='best')
        
    plt.show()
    
@deprecated ('Expensive function; should be removed for the next realease.')
def compute_sfi (
        pk_min: float,
        pk_max: float, 
        rhoa_min: float,
        rhoa_max: float, 
        rhoa: Array | List[float], 
        pk: SP[int]
        ) -> float : 
    """
    SFI is introduced to evaluate the ratio of presumed existing fracture
    from anomaly extent. We use a similar approach as IF computation
    proposed by Dieng et al. (2004) to evaluate each selected anomaly 
    extent and the normal distribution of resistivity values along the 
    survey line. The SFI threshold is set at :math:`sqrt(2)`  for 
    symmetrical anomaly characterized by a perfect distribution of 
    resistivity in a homogenous medium. 
    
    :param pk_min: see :func:`compute_power` 
    :param pk_max: see :func:`compute_power` 
    
    :param rhoa_max: see :func:`compute_magnitude` 
    :param rhoa_min: see :func:`compute_magnitude`
    
    :param pk: 
        
        Station position of the selected anomaly in ``float`` value. 
        
    :param rhoa: 
        
        Selected anomaly apparent resistivity value in ohm.m 
        
    :return: standard fracture index (SFI)
    :rtype: float 
    
    :Example: 
        
        >>> from watex.tools.exmath import compute_sfi 
        >>> sfi = compute_sfi(pk_min = 90,
        ...                      pk_max=130,
        ...                      rhoa_min=175,
        ...                      rhoa_max=170,
        ...                      rhoa=132,
        ...                      pk=110)
        >>> sfi
    
    """  
    def deprecated_sfi_computation () : 
        """ Deprecated way for `sfi` computation"""
        try : 
            if  pk_min -pk  < pk_max - pk  : 
                sfi= np.sqrt((((rhoa_max -rhoa) / 
                                  (rhoa_min- rhoa)) **2 + 
                                 ((pk_max - pk)/(pk_min -pk))**2 ))
            elif pk_max -pk  < pk_min - pk : 
                sfi= np.sqrt((((rhoa_max -rhoa) / 
                                  (rhoa_min- rhoa)) **2 + 
                                 ((pk_min - pk)/(pk_max -pk))**2 ))
        except : 
            if sfi ==np.nan : 
                sfi = - np.sqrt(2)
            else :
                sfi = - np.sqrt(2)
       
    try : 
        
        if (rhoa == rhoa_min and pk == pk_min) or\
            (rhoa==rhoa_max and pk == pk_max): 
            ma= max([rhoa_min, rhoa_max])
            ma_star = min([rhoa_min, rhoa_max])
            pa= max([pk_min, pk_max])
            pa_star = min([pk_min, pk_max])
    
        else : 
       
            if  rhoa_min >= rhoa_max : 
                max_rho = rhoa_min
                min_rho = rhoa_max 
            elif rhoa_min < rhoa_max: 
                max_rho = rhoa_max 
                min_rho = rhoa_min 
            
            ma_star = abs(min_rho - rhoa)
            ma = abs(max_rho- rhoa )
            
            ratio = ma_star / ma 
            pa = abs(pk_min - pk_max)
            pa_star = ratio *pa
            
        sfi = np.sqrt((pa_star/ pa)**2 + (ma_star/ma)**2)
        
        if sfi ==np.nan : 
                sfi = - np.sqrt(2)
    except : 

        sfi = - np.sqrt(2)
  
    
    return sfi
    
def compute_anr (
        sfi: float , 
        rhoa_array: Array | List[float],
        pos_bound_indexes: Array[DType[int]] | List[int]
        )-> float:
    r"""
    Compute the select anomaly ratio (ANR) along with the whole profile from
    SFI. The standardized resistivity values`rhoa`  of is averaged from 
    :math:`X_{begin}` to :math:`X_{end}`. The ANR is a positive value and the 
    equation is given as:
        
    .. math:: 
     
        ANR= sfi * \frac{1}{N} * | \sum_{i=1}^{N} \frac{
            \rho_{a_i} - \bar \rho_a}{\sigma_{\rho_a}} |
       

    where :math:`$\sigma_{rho_a}$`  and :math:`\bar \rho_a` are the standard 
    deviation  and the mean of the resistivity values composing the selected
    anomaly. 
    
    :param sfi: 
        Is standard fracturation index. please refer to :func:`compute_sfi`.
        
    :param rhoa_array: Resistivity values of Electrical Resistivity Profiling
        line 
    :type rhoa_array: array_like 
    
    :param pos_bound_indexes: 
        Select anomaly station location boundaries indexes. Refer to  
        :func:`compute_power` of ``pos_bounds``. 
        
    :return: Anomaly ratio 
    :rtype: float 
    
    :Example: 
        
        >>> from watex.tools.exmath import compute_anr 
        >>> import pandas as pd
        >>> anr = compute_anr(sfi=sfi, 
        ...                  rhoa_array=data = pd.read_excel(
        ...                  'data/l10_gbalo.xlsx').to_numpy()[:, -1],
        ...              pk_bound_indexes  = [9, 13])
        >>> anr
    """
    
    stand = (rhoa_array - rhoa_array.mean())/np.std(rhoa_array)
    try: 
        stand_rhoa =stand[int(min(pos_bound_indexes)): 
                          int(max(pos_bound_indexes))+1]
    except: 
        stand_rhoa = np.array([0])
        
    return sfi * np.abs(stand_rhoa.mean())


@deprecated('Deprecated function to `:func:`watex.methods.erp.get_type`'
            ' more efficient using median and index computation. It will '
            'probably deprecate soon for neural network pattern recognition.')
def get_type (
        erp_array: Array | List [float], 
        posMinMax:Tuple[int] | List[int],
        pk: float | int,
        pos_array: SP[DType[float]],
        dl: float 
        )-> str: 
    """
    Find anomaly type from app. resistivity values and positions locations 
    
    :param erp_array: App.resistivty values of all `erp` lines 
    :type erp_array: array_like 
    
    :param posMinMax: Selected anomaly positions from startpoint and endpoint 
    :type posMinMax: list or tuple or nd.array(1,2)
    
    :param pk: Position of selected anomaly in meters 
    :type pk: float or int 
    
    :param pos_array: Stations locations or measurements positions 
    :type pos_array: array_like 
    
    :param dl: 
        
        Distance between two receiver electrodes measurement. The same 
        as dipole length in meters. 
    
    :returns: 
        - ``EC`` for Extensive conductive. 
        - ``NC`` for narrow conductive. 
        - ``CP`` for conductive plane 
        - ``CB2P`` for contact between two planes. 
        
    :Example: 
        
        >>> from watex.utils.exmath import get_type 
        >>> x = [60, 61, 62, 63, 68, 65, 80,  90, 100, 80, 100, 80]
        >>> pos= np.arange(0, len(x)*10, 10)
        >>> ano_type= get_type(erp_array= np.array(x),
        ...            posMinMax=(10,90), pk=50, pos_array=pos, dl=10)
        >>> ano_type
        ...CB2P

    """
    
    # Get position index 
    anom_type ='CP'
    index_pos = int(np.where(pos_array ==pk)[0])
    # if erp_array [:index_pos +1].mean() < np.median(erp_array) or\
    #     erp_array[index_pos:].mean() < np.median(erp_array) : 
    #         anom_type ='CB2P'
    if erp_array [:index_pos+1].mean() < np.median(erp_array) and \
        erp_array[index_pos:].mean() < np.median(erp_array) : 
            anom_type ='CB2P'
            
    elif erp_array [:index_pos +1].mean() >= np.median(erp_array) and \
        erp_array[index_pos:].mean() >= np.median(erp_array) : 
                
        if  dl <= (max(posMinMax)- min(posMinMax)) <= 5* dl: 
            anom_type = 'NC'

        elif (max(posMinMax)- min(posMinMax))> 5 *dl: 
            anom_type = 'EC'

    return anom_type   
    
@deprecated('`Deprecated function. Replaced by :meth:~core.erp.get_shape` ' 
            'more convenient to recognize anomaly shape using ``median line``'
            'rather than ``mean line`` below.')   
def get_shape (
        rhoa_range: Array | List [float]
        )-> str : 
    """
    Find anomaly `shape`  from apparent resistivity values framed to
    the best points using the mean line. 
 
    :param rhoa_range: The apparent resistivity from selected anomaly bounds
                        :attr:`~core.erp.ERP.anom_boundaries`
    :type rhoa_range: array_like or list 
    
    :returns: 
        - V
        - W
        - K 
        - C
        - M
        - U
    
    :Example: 
        
        >>> from watex.tools.exmath import get_shape 
        >>> x = [60, 70, 65, 40, 30, 31, 34, 40, 38, 50, 61, 90]
        >>> shape = get_shape (rhoa_range= np.array(x))
        ... U

    """
    minlocals = argrelextrema(rhoa_range, np.less)
    shape ='V'
    average_curve = rhoa_range.mean()
    if len (minlocals[0]) >1 : 
        shape ='W'
        average_curve = rhoa_range.mean()
        minlocals_slices = rhoa_range[
            int(minlocals[0][0]):int(minlocals[0][-1])+1]
        average_minlocals_slices  = minlocals_slices .mean()

        if average_curve >= 1.2 * average_minlocals_slices: 
            shape = 'U'
            if rhoa_range [-1] < average_curve and\
                rhoa_range [-1]> minlocals_slices[
                    int(argrelextrema(minlocals_slices, np.greater)[0][0])]: 
                shape ='K'
        elif rhoa_range [0] < average_curve and \
            rhoa_range [-1] < average_curve :
            shape ='M'
    elif len (minlocals[0]) ==1 : 
        if rhoa_range [0] < average_curve and \
            rhoa_range [-1] < average_curve :
            shape ='M'
        elif rhoa_range [-1] <= average_curve : 
            shape = 'C'
            
    return shape 


def compute_power (
        posMinMax:float =None,
        pk_min: Optional[float]=None ,
        pk_max: Optional[float]=None, 
        )-> float:
    """ 
    Compute the power Pa of anomaly.
    
    :param pk_min: 
        Min boundary value of anomaly. `pk_min` is min value (lower) 
        of measurement point. It's the position of the site in meter. 
    :type pk_min: float 
    
    :param pk_max: 
        Max boundary of the select anomaly. `pk_max` is the maximum value 
        the measurement point in meter. It's  the upper boundary position of 
        the anomaly in the site in m. 
    :type pk_max: float 
    
    :return: The absolute value between the `pk_min` and `pk_max`. 
    :rtype: float 
    
    :Example: 
        
        >>> from watex.tools.exmath import compute_power 
        >>> power= compute_power(80, 130)
    
    
    """
    if posMinMax is not None: 
        pk_min = np.array(posMinMax).min()     
        pk_max= np.array(posMinMax).max()
    
    if posMinMax is None and (pk_min is None or pk_max is None) : 
        raise Wex.WATexError_parameter_number(
            'Could not compute the anomaly power. Provide at least'
             'the anomaly position boundaries or the left(`pk_min`) '
             'and the right(`pk_max`) boundaries.')
    
    return np.abs(pk_max - pk_min)
    
def compute_magnitude(
        rhoa_max: float =None ,
        rhoa_min: Optional[float]=None,
        rhoaMinMax:Optional [float] =None
        )-> float:
    """
    Compute the magnitude `Ma` of  selected anomaly expressed in Ω.m.
    ano
    :param rhoa_min: resistivity value of selected anomaly 
    :type rhoa_min: float 
    
    :param rhoa_max: Max boundary of the resistivity value of select anomaly. 
    :type rhoa_max: float 
    
    :return: The absolute value between the `rhoa_min` and `rhoa_max`. 
    :rtype: float 
    
    :Example: 
        
        >>> from watex.utils.exmath import compute_power 
        >>> power= compute_power(80, 130)
    
    """
    if rhoaMinMax is not None : 
        rhoa_min = np.array(rhoaMinMax).min()     
        rhoa_max= np.array(rhoaMinMax).max()
        
    if rhoaMinMax is None and (rhoa_min  is None or rhoa_min is None) : 
        raise Wex.ParameterNumberError(
            'Could not compute the anomaly magnitude. Provide at least'
            'the anomaly resistivy value boundaries or the buttom(`rhoa_min`)'
             'and the top(`rhoa_max`) boundaries.')

    return np.abs(rhoa_max -rhoa_min)

def get_minVal(
        array: Array[T] | List [T]
        )->List[T] : 
    """
    Function to find the three minimum values on array and their 
    corresponding indexes. 
    
    :param array: array  of values 
    :type array: array_like 
    
    :returns: Three minimum values of rho, index in rho_array
    :rtype: tuple
    
    """

    holdList =[]
    if not isinstance(array, (list, tuple, np.ndarray)):
        if isinstance(array, float): 
            array=np.array([array])
        else : 
            try : 
                array =np.array([float(array)])
            except: 
                raise Wex.WATexError_float('Could not convert %s to float!')
    try : 
        # first option:find minimals locals values 
        minlocals = argrelextrema(array, np.less)[0]
        temp_array =np.array([array[int(index)] for index in minlocals])
        if len(minlocals) ==0: 
            ix = np.where(array ==array.min())
            if len(ix)>1: 
                ix =ix[0]
            temp_array = array[int(ix)]
            
    except : 
        # second option: use archaic computation.
        temp_array =np.sort(array)
    else : 
        temp_array= np.sort(temp_array)
        
    ss=0

    for ii, tem_ar in enumerate(temp_array) : 
        if ss >=3 : 
            holdList=holdList[:3]
            break 
        min_index = np.where(array==tem_ar)[0]
  
        if len(min_index)==1 : 
            holdList.append((array[int(min_index)], 
                             int(min_index)))
            ss +=ii
        elif len(min_index) > 1 :
            # loop the index array and find the min for consistency 
            for jj, indx in enumerate(min_index):  
                holdList.append((array[int(indx)], 
                                 int(indx)))
        ss =len(holdList)
        
    # for consistency keep the 3 best min values 
    if len(holdList)>3 : 
        holdList = holdList[:3]

    return holdList 
    
def compute_lower_anomaly(
    erp_array: Array |List [float],
    station_position: SP[float]=None, 
    step: Optional[int] =None, 
    **kws
    )-> Tuple[Dict[str, Any], Array, List[Array], List[Tuple[int, float]]]: 
    """
    Function to get the minimum value on the ERP array. 
    If `pk` is provided wil give the index of pk
    
    :param erp_array: array of apparent resistivity profile 
    :type erp_array: array_like
    
    :param station position: array of station position (survey), if not given 
                    and `step` is known , set the step value and 
                    `station_position` will compute automatically 
    :type station_position: array_like 
    
    :param step: The distance between measurement im meter. If given will 
        recompute the `station_position`
    
    :returns: 
        * `bestSelectedDict`: dict containing best anomalies  
                with the anomaly resistivities range.
        * `anpks`: Main positions of best select anomaly 
        * `collectanlyBounds`: list of arrays of select anomaly values
        * `min_pks`: list of tuples (pk, minVal of best anomalies points.)
    :rtype: tuple 
    
    :Example: 
        
        >>> from watex.tools.exmath import compute_lower_anolamy 
        >>> import pandas as pd 
        >>> path_to_= 'data/l10_gbalo.xlsx'
        >>> dataRes=pd.read_excel(erp_data).to_numpy()[:,-1]
        >>> anomaly, *_ =  compute_lower_anomaly(erp_array=data, step =10)
        >>> anomaly
                
    """
    display_infos= kws.pop('diplay_infos', False)
    # got minumum of erp data 
    collectanlyBounds=[]
    if step is not None: 
        station_position = np.arange(0, step * len(erp_array), step)

    min_pks= get_minVal(erp_array) # three min anomaly values 

    # compute new_pjk 
    # find differents anomlies boundaries 
    for ii, (rho, index) in enumerate(min_pks) :
        _, _, anlyBounds= drawn_boundaries(erp_data = erp_array,
                                 appRes = rho, index=index)
        
        collectanlyBounds.append(anlyBounds)

    if station_position is None :
        pks =np.array(['?' for ii in range(len(erp_array))])
    else : pks =station_position

    if pks.dtype in ['int', 'float']: 
        anpks =np.array([pks[skanIndex ] for
                         (_, skanIndex) in min_pks ])
    else : anpks ='?'
    
    bestSelectedDICT={}
    for ii, (pk, anb) in enumerate(zip(anpks, collectanlyBounds)): 
        bestSelectedDICT['{0}_pk{1}'.format(ii+1, pk)] = anb
    
    if display_infos:
        print('{0:+^100}'.format(
            ' *Best Conductive anomaly points (BCPts)* '))
        fmt_text(anFeatures=bestSelectedDICT)
    
    return bestSelectedDICT, anpks, collectanlyBounds, min_pks

@deprecated ('Autodetection is instable, it should be modified for '
             'the future realease.')
def select_anomaly ( 
        rhoa_array:Array,
        pos_array:SP =None,
        auto: bool =True,
        dipole_length =10., 
        **kws 
        )->Tuple[float]:
    """
    Select the anomaly value from `rhoa_array` and find its boundaries if 
    `auto` is set to ``True``. If `auto` is ``False``, it's usefull to 
    provide the anomaly boundaries from station position. Change  the argument 
    `dipole_length`  i.e. the distance between measurement electrode is not
    equal to ``10`` m else give the `pos_array`. If the `pos_array` is given,
    the `dipole_length` will be recomputed.
     
    
    :param rhoa_array: The apparent resistivity value of Electrical Resistivity
        Profiling. 
    :type rho_array: array_like 
    
    :param pos_array: The array of station position in meters 
    :type pos_array: array_like 
     
    :param auto: bool
        Automaticaly of manual computation to select the best anomaly point. 
        Be sure if `auto` is set to ``False`` to provide the anomaly boundary
        by setting `pos_bounds`: 
        
        .. math::
            
            pos_bounds=(90, 130)
            
       where ``90`` is the `pk_min` and ``130`` is the `pk_max` 
       If `pos_bounds` is not given an station error will probably occurs 
       from :class:`~.exceptions.StationError`. 
    
    :param dipole_length: 
        Is the distance between two closest measurement. If the value is known 
        it's better to provide it and don't need to provied a `pos_array`
        value. 
    :type dipole_length: float 
    
    :param pos_bounds: 
        Is the tuple value of anomaly boundaries  composed of `pk_min` and 
        `pk_max`. Please refer to :func:`compute_power`. When provided 
        the `pos_bounds` value, please set `the dipole_length` to accurate 
        the computation of :func:`compute_power`.
    :type pos_bounds:tuple
    
    :return: 
        
        - `rhoa` : The app. resistivity value of the selected anomaly 
        - `pk_min` and the `pk_max`: refer to :func:`compute_power`. 
        - `rhoa_max` and `rhoa_min`: refer to :func:`compute_magnitude`
        
    :note:  If the `auto` param is ``True``, the automatic computation will
             give at most three best animalies ranking according 
             to the resitivity value. 
             
    """
    
    pos_bounds =kws.pop("pos_bounds", (None, None))
    anom_pos = kws.pop('pos_anomaly', None)
    display_infos =kws.pop('display', False)
    
    if auto is False : 
        if None in pos_bounds  or pos_bounds is None : 
            raise Wex.ErrorSite('One position is missed' 
                                'Please provided it!')
        
        pos_bounds = np.array(pos_bounds)
        pos_min, pos_max  = pos_bounds.min(), pos_bounds.max()
        
        # get the res from array 
        dl_station_loc = np.arange(0, dipole_length * len(rhoa_array), 
                                   dipole_length)
        # then select rho range 
        ind_pk_min = int(np.where(dl_station_loc==pos_min)[0])
        ind_pk_max = int(np.where(dl_station_loc==pos_max)[0]) 
        rhoa_range = rhoa_array [ind_pk_min:ind_pk_max +1]
        pk, res= find_position_from_sa (an_res_range=rhoa_range, 
                                         pos=pos_bounds,
                                selectedPk= anom_pos) 
        pk = int(pk.replace('pk', ''))
        rhoa = rhoa_array[int(np.where(dl_station_loc == pk )[0])]
        rhoa_min = rhoa_array[int(np.where(dl_station_loc == pos_min )[0])]
        rhoa_max = rhoa_array[int(np.where(dl_station_loc == pos_max)[0])]
        
        rhoa_bounds = (rhoa_min, rhoa_max)
        
        return {'1_pk{}'.format(pk): 
                (pk, rhoa, pos_bounds, rhoa_bounds, res)} 
    
    if auto: 
        bestSelectedDICT, anpks, \
            collectanlyBounds, min_pks = compute_lower_anomaly(
                erp_array= rhoa_array, 
                station_position= pos_array, step= dipole_length,
                display_infos=display_infos ) 

            
        return {key: find_feature_positions (anom_infos= bestSelectedDICT, 
                                      anom_rank= ii+1, pks_rhoa_index=min_pks, 
                                      dl=dipole_length) 
                for ii, (key , rho_r) in enumerate(bestSelectedDICT.items())
                }
    
def define_anomaly(
        erp_data: Array | List [float],
        station_position: SP[DType[float|int]]=None,
        pks: Optional[int]=None, 
        dipole_length: float =10., 
        **kwargs
        )-> Dict[str, Tuple[int]]:
    """
    Function will select the different anomalies. If pk is not given, 
    the best three anomalies on the survey lines will be
    computed automatically
    
    :param erp_data: Electrical resistivity profiling 
    :type erp_data: array_like 
    
    :param pks: station positions anomaly boundaries (pk_begin, pk_end)
                If selected anomalies is more than one, set `pks` into dict
                where number of anomaly =keys and pks = values 
    :type pks: list or dict
    
    :param dipole_length: Distance between two measurements in meters
                        Change the `dipole lengh
    :type dipole_length: float
    
    :param station_position: station position array 
    :type statiion_position: array_like 
    
    :return: list of anomalies bounds 
    
    """
    selectedPk =kwargs.pop('selectedPk', None)
    bestSelectedDICT={}
    if station_position is not None : 
        dipole_length = (station_position.max()-
               station_position.min())/(len(station_position -1))
    if station_position is None : 
        station_position =np.arange(0, dipole_length * len(erp_data), 
                                    dipole_length)
                                        
  
    def get_bound(pksbounds): 
        """
        Get the bound from the given `pks`
        :param pksbounds: Anomaly boundaries
        :type pksbounds: list of array_like 
        
        :returns: * anomBounds- array of appRes values of anomaly
        :rtype: array_like 
        """
        # check if bound is on station positions
        for spk in pksbounds : 
            if not pksbounds.min() <= spk <= pksbounds.max(): 
                raise  Wex.ExtractionError(
                    'Bound <{0}> provided is out of range !'
                   'Dipole length is set to = {1} m.'
                   ' Please set a new bounds.')
            
        pkinf = np.where(station_position==pksbounds.min())[0]
        pksup = np.where(station_position==pksbounds.max())[0]
        anomBounds = erp_data[int(pkinf):int(pksup)+1]
        return anomBounds
    
    if pks is None : 
        bestSelectedDICT, *_= compute_lower_anomaly(
            erp_array=erp_data, step=dipole_length, 
            station_position =station_position)
        
    elif isinstance(pks, list):
        pks =np.array(sorted(pks))
        collectanlyBounds = get_bound(pksbounds= pks)
        # get the length of selected anomalies and computed the station 
        # location wich composed the bounds (Xbegin and Xend)
        pkb, *_= find_position_from_sa(
            an_res_range=collectanlyBounds, pos=pks, 
            selectedPk=selectedPk)
        bestSelectedDICT={ '1_{}'.format(pkb):collectanlyBounds}

    elif isinstance(pks, dict):
        for ii, (keys, values) in enumerate(pks.items()):
            if isinstance(values, list): 
                values =np.array(values)
            collectanlyBounds=  get_bound(pksbounds=values) 
            pkb, *_= find_position_from_sa(
            an_res_range=collectanlyBounds, pos=pks, 
            selectedPk=selectedPk)
            bestSelectedDICT['{0}_{1}'.format(ii+1, pkb)]=collectanlyBounds
           
    return bestSelectedDICT


   
    # if plot:
        
    #     (X, Y, x_new, y_projected, oB, f_brl(oB))
    #     plt.loglog(X, Y , label ='Raw Rhoa curve')
    #     plt.loglog(x_new, y_projected , label = 'Fitting Rhoa curve')
    #     plt.xlabel('AB/2'); plt.ylabel('Resistivity(ohm.m)')
    #     plt.loglog (oB, f_brl(oB), label= 'Dummy basement curve') 
    #     plt.legend()
