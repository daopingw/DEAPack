
import pandas as pd
from typing import Optional, Literal
from .ddf import DDF
from .solver import solve_lp_prob

class DEA(DDF):
    '''
    The DEA class is used to calculate the efficiency score of Decision Making Units (DMUs) based on the Data Envelopment Analysis (DEA) method.

    Parameters
    ----------
    DMUs : pandas.Series
        The column of DMUs.
    x_vars : pandas.DataFrame
        The data frame of input variables, where the rows are the DMUs and the columns are the input variables.
    y_vars : pandas.DataFrame
        The data frame of desirable variables, where the rows are the DMUs and the columns are the output variables.
    b_vars : pandas.DataFrame, optional
        The data frame of undesirable variables, where the rows are the DMUs and the columns are the undesirable variables.
    return_to_scale : str, optional
        The type of return to scale, either 'CRS' (constant return to scale) or 'VRS' (variable return to scale). The default is 'CRS'.
    g_x : pandas.DataFrame, optional
        The data frame of direction components for input adjustment, where the rows are the DMUs and the columns are the input variables. The default is -x_vars.
    g_y : pandas.DataFrame, optional
        The data frame of direction components for desirable output adjustment, where the rows are the DMUs and the columns are the output variables. The default is y_vars.
    g_b : pandas.DataFrame, optional
        The data frame of direction components for undesirable output adjustment, where the rows are the DMUs and the columns are the undesirable variables. The default is -b_vars.
    radial : bool, optional
        The type of DEA model, either radial or non-radial. The default is True.
    weight_x : list, optional
        The list of weights for the input variables. The default is [1]*x_vars.shape[1].
    weight_y : list, optional
        The list of weights for the output variables. The default is [1]*y_vars.shape[1].
    weight_b : list, optional
        The list of weights for the non-discretionary variables. The default is [1]*b_vars.shape[1].
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
    efficiency : pandas.Series
        The estimated efficiency score, based on the distance to the frontier.
    
    all prameters is also stored as attributes.

    Methods
    -------
    solve(parallel=True, n_jobs=None)
        Solve the DEA model, calculate the distance to the frontier.
    get_efficiency()
        Calculate the efficiency score, based on the distance to the frontier.
    '''
    def __init__(self, 
                 DMUs: Optional[pd.Series] = None,
                 x_vars: Optional[pd.DataFrame] = None, 
                 y_vars: Optional[pd.DataFrame] = None, 
                 b_vars: Optional[pd.DataFrame] = None,
                 return_to_scale: Literal['CRS', 'VRS'] = None,
                 g_x: Optional[pd.DataFrame] = None, 
                 g_y: Optional[pd.DataFrame] = None, 
                 g_b: Optional[pd.DataFrame] = None,
                 radial: Optional[bool] = None,
                 weight_x: Optional[list] = None,
                 weight_y: Optional[list] = None,
                 weight_b: Optional[list] = None,
                 time: Optional[pd.Series] = None, 
                 ref_type: Literal['Contemporaneous', 'Global', 'Sequential', 'Window', 'Biennial'] = None,
                 window: int = None
                 ):
        super().__init__(DMUs=DMUs, 
                         x_vars=x_vars, 
                         y_vars=y_vars, 
                         b_vars=b_vars,
                         return_to_scale=return_to_scale, 
                         g_x=g_x, 
                         g_y=g_y, 
                         g_b=g_b, 
                         radial=radial, 
                         weight_x=weight_x,
                         weight_y=weight_y, 
                         weight_b=weight_b)
        self.time = time
        self.ref_type = ref_type
        self.window = window
        self.distance = None
        self.efficiency = None


    # patch the parameters
    def patch_parameters(self):
        super().patch_parameters()
        if self.time is not None and self.ref_type is None:
            self.ref_type = 'Contemporaneous'
        if self.ref_type == 'Window' and self.window is None:
            self.window = 1


    # create a list of LP problems
    def create_problem_list(self) -> list:
        problem_list = []

        # the reference index
        for i in range(self.DMUs.shape[0]):
            if self.time is None:
                ref_index = range(self.DMUs.shape[0])
            else:
                if self.ref_type == 'Contemporaneous':
                    ref_index = self.time.index[self.time == self.time[i]].tolist()
                elif self.ref_type == 'Global':
                    ref_index = range(self.DMUs.shape[0])
                elif self.ref_type == 'Sequential':
                    ref_index = self.time.index[self.time <= self.time[i]].tolist()
                elif self.ref_type == 'Window':
                    ref_index = self.time.index[(self.time <= (self.time[i]+self.window)) & (self.time >= (self.time[i]-self.window))].tolist()
                elif self.ref_type == 'Biennial':
                    ref_index = self.time.index[(self.time == self.time[i]) | (self.time == (self.time[i]+1))].tolist()
                else:
                    raise ValueError('The ref_type is not valid.')
                
            problem_list.append(self.define_lp_problem(i, ref_index))
        
        return problem_list


    # solve the DEA model, calculate the distance to the frontier
    def solve(self, parallel: bool = False, n_jobs: int = None):
        '''
        Solve the DEA model, calculate the distance to the frontier.

        Parameters
        ----------
        parallel : bool, optional
            Whether to use parallel computing. The default is False.

            !!! The multiprocessing may not work in some instances.

        n_jobs : int, optional
            The number of jobs to run in parallel. The default is (n_processors-2).
        '''
        self.patch_parameters()

        prob_list = self.create_problem_list()
            
        if parallel:
            import multiprocessing
            if n_jobs is None:
                n_jobs = multiprocessing.cpu_count()
            pool = multiprocessing.Pool(n_jobs)        
            self.distance = pool.map(solve_lp_prob, prob_list)
            pool.close()
            pool.join()
        else:
            self.distance = [solve_lp_prob(prob) for prob in prob_list]
    
        self.efficiency = self.get_efficiency()

        
    # calculate the efficiency score, based on the distance to the frontier
    def get_efficiency(self) -> pd.Series:
        '''
        Calculate the efficiency score, based on the distance to the frontier.
        
        Standardized the score to be between 0 and 1. The higher the score, the more efficient the DMU.
        '''
        if self.radial:
            return 1-pd.Series(self.distance)
        else:
            return 1/(pd.Series(self.distance)+1)
