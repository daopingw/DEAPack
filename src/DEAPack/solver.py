
import pulp

def solve_lp_prob(prob: pulp.LpProblem) -> float:
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    return prob.objective.value()
