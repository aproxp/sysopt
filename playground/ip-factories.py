# solves problem 3.1.1 from Search Methodologies - Factories
from ortools.linear_solver import pywraplp


def create_data_model():
    data = {}
    data['num_vars'] = 12
    data['bool_vars'] = 3
    data['constraint_coeffs'] = [
        [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0],
        [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, -1500, 0, 0],
        [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, -1500, 0],
        [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, -1500]
    ]
    # upper and lower bounds equal
    data['upper_bounds'] = [1000, 1000, 500, 500, 0, 0, 0]
    data['lower_bounds'] = [1000, 1000, 500, 500, -1500, -1500, -1500]
    data['num_constraints'] = 7
    data['obj_coeffs'] = [
        52 * 25, 52 * 20, 52 * 15,
        52 * 15, 52 * 25, 52 * 20,
        52 * 20, 52 * 15, 52 * 25,
        52 * 25, 52 * 15, 52 * 15,
        500000, 500000, 500000
    ]
    return data


def main():
    data = create_data_model()
    solver = pywraplp.Solver.CreateSolver('SCIP')
    infinity = solver.infinity()

    x = {}
    for j in range(data['num_vars']):
        x[j] = solver.IntVar(0, infinity, 'x[%i]' % j)

    y = {}
    for j in range(data['bool_vars']):
        y[j] = solver.IntVar(0, 1, 'y[%i]' % j)
    print('Number of variables =', solver.NumVariables())

    for i in range(data['num_constraints']):
        constraint = solver.RowConstraint(data['lower_bounds'][i], data['upper_bounds'][i], '')
        for j in range(data['num_vars']):
            constraint.SetCoefficient(x[j], data['constraint_coeffs'][i][j])
        for j in range(data['bool_vars']):
            constraint.SetCoefficient(y[j], data['constraint_coeffs'][i][j+data['num_vars']])

    objective = solver.Objective()
    for j in range(data['num_vars']):
        objective.SetCoefficient(x[j], data['obj_coeffs'][j])
    for j in range(data['bool_vars']):
        objective.SetCoefficient(y[j], data['obj_coeffs'][j+data['num_vars']])

    objective.SetMinimization()
    status = solver.Solve()
    if status == pywraplp.Solver.OPTIMAL:
        print('Objective value =', solver.Objective().Value())
        for j in range(data['num_vars']):
            print(x[j].name(), ' = ', x[j].solution_value())
        for j in range(data['bool_vars']):
            print(y[j].name(), ' = ', y[j].solution_value())
        print()
        print('Problem solved in %f milliseconds' % solver.wall_time())
        print('Problem solved in %d iterations' % solver.iterations())
        print('Problem solved in %d branch-and-bound nodes' % solver.nodes())
    else:
        print('The problem does not have an optimal solution.')


if __name__ == '__main__':
    main()
