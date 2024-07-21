
import pulp

def solve_lp_prob(prob: pulp.LpProblem) -> float:
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if prob.status == 1:
        return prob.objective.value()
    else:
        return None
