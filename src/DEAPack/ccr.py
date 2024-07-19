
import pandas as pd
from .dea import DEA

class CCR(DEA):
    '''
    The CCR model.

    Parameters
    ----------
    DMUs : pandas.Series
        The column of DMUs.
    x_vars : pandas.DataFrame
        The data frame of input variables, where the rows are the DMUs and the columns are the input variables.
    y_vars : pandas.DataFrame
        The data frame of desirable variables, where the rows are the DMUs and the columns are the output variables.
    return_to_scale : str, optional
        The type of return to scale, either 'CRS' (constant return to scale) or 'VRS' (variable return to scale). The default is 'CRS'.
    orientation : str, optional
        The orientation of the CCR model, either 'input' or 'output'. The default is 'input'.
    radial : bool, optional
        The type of DEA model, either radial or non-radial. The default is True.
    time : pandas.Series, optional
        The series of time index for panel data.
    ref_type : str, optional
        The type of reference set, either 'Contemporaneous', 'Global', 'Sequential', 'Window', or 'Biennial'. The default is 'Contemporaneous'.
    window : int, optional
        The window size for the 'Window' reference set. The default is 1.

    Attributes
    ----------
    distance : list
        The list of objective values from the linear programming problems.
    
    all prameters is also stored as attributes.

    Methods
    -------
    solve(parallel=True, n_jobs=None)
        Solve the DEA model, calculate the distance to the frontier.
    get_efficiency()
        Calculate the efficiency score, based on the distance to the frontier.
    '''
    def __init__(self, 
                 DMUs=None, 
                 x_vars=None, y_vars=None,
                 orientation=None,
                 time=None, 
                 ref_type=None,
                 window=None
                 ):
        super().__init__(DMUs=DMUs, 
                         x_vars=x_vars, 
                         y_vars=y_vars, 
                         b_vars=None,
                         return_to_scale="CRS", 
                         g_x=None, 
                         g_y=None, 
                         g_b=None, 
                         radial=True, 
                         weight_x=None,
                         weight_y=None, 
                         weight_b=None, 
                         time=time, 
                         ref_type=ref_type, 
                         window=window)
        self.orientation = orientation
        

    # patch the parameters
    def patch_parameters(self):
        super().patch_parameters()
        if self.orientation == None:
            self.orientation = 'input'
        if self.orientation == 'input':
            self.g_y = self.y_vars*0
        else:
            self.g_x = self.x_vars*0


    # get the efficiency
    def get_efficiency(self):
        '''
        Calculate the CCR efficiency of the DMUs.
        '''
        if self.orientation == 'input':
            return pd.Series(self.distance)
        else:
            return 1/(pd.Series(self.distance)+1)
