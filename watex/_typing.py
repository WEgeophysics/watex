# -*- coding: utf-8 -*-

""" 
WATex Type variable definitions 
=============================== 

.. |erp| replace:: Electrical resistivity profiling 

Some type variables customized need to be explained for easy understanding 
in the whole package. Indeed, customized type hints is used to define the 
type of arguments. 

**M**: Suppose to be the interger variable `IntVar` to denote the num ber of 
    rows in the ``Array``. 
    
**N**: Like the ``M``, *N* means the number of column in the ``Array``. It 
    is bound with  integer variable. 
    
**T**: Is known as used name generic standing for `Any` type of  variable. 

**U**: Unlike `T`, `U` stands for nothing. Use to sepcify the one dimentional 
    array. For instance:: 
        
        >>> import numpy as np 
        >>> array = np.arange(4).shape 
        ... (4, )
        
**S**: Indicates the `Shape` status. It is bound by `M`, `U`, `N`. 'U' stands
    for nothing for one dimensional array. While, the common shape expects 
    for one of two dimensional arrays, it is possible to extend array for 
    more than one dimensional. The class object :class:`AddShape` is 
    created to grand all the remaining value of integers shape. 
    
**D**: Stands for  dtype object. It is bound with  :class:`DType`.

**Array**: Defined for  one dimensional array and `DType` can be specify. For 
    instance, we generated two arrays (`arr1`and `arr2`) for different types:: 
        
        >>> import numpy as np
        >>> from watex._typing import TypeVar, Array, DType
        >>> T = TypeVar ('T', float) 
        >>> A = TypeVar ('A', str, bytes )
        >>> arr1:Array[T, DType[T]] = np.arange(21) # dtype ='float'
        >>> arr2: Array[A, DType[A]] = arr1.astype ('str') # dtype ='str'
        
**NDArray**: Stands for multi-dimensional arrays i.e more than two. Here, the 
    difference between the one dimensional type variable ``Array`` is that 
    while the latter accepts the ``DType`` argument  as the second parameter. 
    It could be turn to the number of multidimentional rows including the 
    `Array as first argument and specify the DType as the second argument 
    like this:: 
        
        >>> import numpy as np 
        >>> from watex._typing import TypeVar, Array, NDarray, DType 
        >>> T =TypeVar ('T', int)
        >>> U = TypeVar ('U')
        >>> multidarray = np.arange(7, 7).astype (np.int32)
        >>> def accept_multid(
                arrays: NDArray[Array[T, U], DType [T]]= multidarray
                ):
            ''' asserted with MyPy and work-fine.'''
                ...
                
**Sub**: Stand for subset. Indeed, the class is created to define the 
    conductive zone. It is a subset ``Sub`` of ``Array``. For example, we first 
    build an array secondly extract the conductive zone from `erp` line.
    Finally, we checked the type hint to assert whether the extracted zone 
    is a subset of the whole `erp` line. The demo is given below:: 
        
        >>> import numpy as np 
        >>> from watex._typing import TypeVar, DType, Array , Sub
        >>> from watex.utils.exmath import _define_conductive_zone
        >>> T= TypeVar ('T', float)
        >>> erp_array: Array[T, DType[T]] = np.random.randn (21) # whole line 
        >>> select_zone, _ = _define_conductive_zone (erp = erp_array , auto =True)
        >>> select_zone: Array[T, DType[T]]
        >>> def check_cz (select_zone: Sub[Array]): 
                ''' assert with MyPy and return ``True`` as it works fine. '''
                ... 
                
**SP**: Stand for Station positions. The unit of position may vary, however, 
    we keep for :mod:`watex.method.electrical.ElectricalResistivityProfiling`
    the default unit in ``meters``by starting at position 0. Typically,
    positions are recording according to the dipole length. For the example, 
    we can generated a position values for ``121 stations`` with dipole 
    length equals to ``50m`` i.e the length of the survey line is ``6 km``. 
    Here we go:: 
        
        * Import required modules and generate the whole survey line::
            >>> import numpy as np 
            >>> from watex._typing import TypeVar, DType, SP, Sub 
            >>> T =TypeVar ('T', bound =int)
            >>> surveyL:SP = np.arange(0, 50 *121 , 50.).astype (np.int32)
            ... (work fine with MyPy )
            
        * Let's verify whether the extract data from surveyL is also a subset 
            of station positions::
                
            -  We use the following fonction to to extract the specific
                part of whole survey line `surveyL`:: 
                    
                    >>> from watex.utils.exmath import _define_conductive_zone
                    >>> subpos,_ = _define_conductive_zone (surveyL, s='S10') 
                    
            -  Now, we check the instance value `subpos` as subset array of 
                of `SP`. Note that the station 'S10' is included in the 
                extracted locations and is extented for seven points. For 
                further details, refer to `_define_conductive_zone.__doc__`:: 
                
                    >>> def checksup_type (sp: Sub[SP[T, DType[T]]] = subpos ): 
                            ''' SP is an array of positions argument `sp`  
                            shoud be asserted as a subestof the whole line.'''
                            ... 
                    ... (test verified. subpos is a subset of `SP`) 

---

Additional definition for common arguments 
=========================================== 

To better construct a hugue API, an explanation of some argument is useful 
to let the user aware when meeting such argument in a callable function. 

**erp** : Stand for Electrical Resistivity Profiling. Typically, the type hint 
    for `erp` is ``Array[float, DType [float]]`` or ``List[float]``. Its
    array is supposed to hold the apparent resistivy values  collected 
    during the survey. 
    
**p**: Typically mean position but by preference means station location
     positions. The type hint used to defined the `p` is ``
     ``Array[int, DType [int]]`` or ``List[int]``. Indeed, the position 
     supposed to be on integer array and the given values enven in float 
     should be casted to integers. 
     
**cz**: Stands for Conductive Zone. It is a subset of `erp` so they share the 
    same type hint. However, for better demarcation, ``Sub`` is convenient to 
    use to avoid any confusion about the full `erp` and the extracted  
    conductive as demontrated in the example above in ``Sub`` type hint
    definition.
        
"""

from typing import (
    TypeVar, 
    List,
    Tuple,
    Sequence, 
    Dict, 
    Iterable, 
    Callable, 
    Union, 
    Any , 
    Generic,
    Optional,
    Union,
    Type , 
    Mapping, 
    # ParamSpec

)

T = TypeVar('T')
M =TypeVar ('M', bound= int ) 
N= TypeVar('N',  bound =int )
U= TypeVar('U')
D =TypeVar ('D', bound ='DType')
S = TypeVar('S', bound='Shape')


class AddShape (Generic [S]): 
    """ Suppose to be an extra bound to top the `Shape` for dimensional 
    more than two. 
    
    Example 
    ------- 
    >>> import numpy as np 
    >>> np.random.randn(7, 3, 3) 
    >>> def check_valid_type (
        array: NDArray [Array[float], Shape[M, AddShape[N]]]): 
        ... 
    
    """
class Shape (Generic[M, S], AddShape[S]): 
    """ Generic to construct a tuple shape for NDarray. `Shape has is 
    written wait for two dimensional arrays with M-row and N-columns. However 
    for three dimensional,`Optional` Type could be: 
        
    :Example: 
        >>> import numpy as np 
        >>> # For 1D array 
        >>> np
        >>> np.random.rand(7)
        >>> def check_array1d( 
            array: Array[float, Shape[M, None]])
        >>> np.random.rand (7, 7).astype('>U12'):
        >>> def check_array2d_type (
            array: NDArray[Array[str], Shape [M, N], DType ['>U12']])
        
    """
    def __getitem__ (self, M, N) -> S: 
        """ Get the type of rown and type of columns 
        and return Tuple of ``M`` and ``N``. """
        ... 
    
class DType (Generic [T]): 
    """ DType can be Any Type so it holds 'T' type variable. """
    def __getitem__  (self, T) -> T: 
        """ Get Generic Type object and return Type Variable"""
        ...  
       
class Array(Generic[T, D]): 
    """ Arry Type here means the 1D array i.e singular column. """
    
    def __getitem__ (self, T) -> T: 
        """ Return Type of the given Type variable. """ 
        ... 
    
    
class NDArray(Array[T, DType [T]], Generic [T, D ]) :
    """ NDarray has ``M``rows, ``N``-columns, `Shape` and `DType` object. 
    and Dtype. `Shape` is unbound for this class since it does not make since
    to sepecify more integers. However, `DType` seems useful to provide. 
    
    :Example: 
        >>> import numpy as np 
        >>> T= TypeVar (T, str , float) # Dtype here is gone to be "str" 
        >>> array = np.c_[np.arange(7), np.arange(7).astype ('str')]
        >>> def test_array (array: NDArray[T, DType [T]]):...
    """
    def __getitem__ (self,T ) -> T: 
        """ Return type variable. Truly the ``NDArray``"""
        ... 
    
class F (Generic [T]): 
    """ Generic class dedicated for functions, methods and class and 
    return the given types i.e callable object with arguments or `Any`. 
    
    :Example: 
        >>> import functools 
        >>> def decorator (appender ='get only the documention and pass.'):
                @functools.wraps(func):
                def wrapper(*args, **kwds)
                    func.__doc__ = appender + func.__doc__
                    return func (*args, **kwds) 
                return wrapper 
        >>> @decorator  # do_nothing = decorator (anyway)
            def anyway(*args, **kwds):
                ''' Im here to '''
                ...
        >>> def check_F(anyway:F): 
                pass 
    """
    def __getitem__ (self, T) -> Callable [..., Union[T, Callable[..., T]] ]:
        """ Accept any type of variable supposing to be a callable object 
        functions, methods or even classes and returnthe given type 
        object or another callable object with its own or different specific 
        parameters."""
        ... 
    
class Sub (Generic [T]): 
    """ Return subset of Array"""
    ... 
     
class SP(Generic [T, D]): 
    """ Station position arrays hold integer values of the survey location.
    Most likely, the station position is given according to the dipole length.
    Assume the dipole length is ``10 meters`` and survey is carried out on 
    21 stations. The station position array  should be an array of interger 
    values from 0. to 200 meters. as like:: 
        
        >>> from 
        >>> import numpy as np 
        >>> positions: SP= np.arange(0, 21 * 10, 10.
                                     ).astype (np.int32) # integer values 
        >>> 
    """
    ... 
    

if __name__=='__main__': 
    def test (array:Sub[SP[Array[int, DType[int]], DType [int]]]):... 
    def test2 (array:Sub[SP[Array, DType [int]]]):... 
    



























