
import pulp
from typing import Optional

def solve_lp_problem(lp_problem: pulp.LpProblem) -> Optional[float]:
    lp_problem.solve(pulp.PULP_CBC_CMD(msg=False))
    if lp_problem.status == 1:
        return lp_problem.objective.value()
    return None
