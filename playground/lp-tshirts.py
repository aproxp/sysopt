# Solves the T-shirt example from Search Methodologies, section 2.2.2.1
from ortools.linear_solver import pywraplp


def lp_tshirts():
    solver = pywraplp.Solver.CreateSolver('GLOP')

    # add three t-shirt styles
    x1 = solver.NumVar(0, solver.infinity(), 'x1')
    x2 = solver.NumVar(0, solver.infinity(), 'x2')
    x3 = solver.NumVar(0, solver.infinity(), 'x3')

    # cutting time
    solver.Add(7.5 * x1 + 8 * x2 + 4 * x3 <= 10000)
    # sewing time
    solver.Add(12 * x1 + 9 * x2 + 8 * x3 <= 18000)
    # packaging time
    solver.Add(3 * x1 + 4 * x2 + 2 * x3 <= 9000)
    # existing order on t-shirt 1
    solver.Add(x1 >= 1000)

    solver.Maximize(3 * x1 + 5 * x2 + 4 * x3)

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print('Solution:')
        print('Value = ', solver.Objective().Value())
        print('x1 = ', x1.solution_value())
        print('x2 = ', x2.solution_value())
        print('x3 = ', x3.solution_value())
    else:
        print('No optimal solution.')


lp_tshirts()
