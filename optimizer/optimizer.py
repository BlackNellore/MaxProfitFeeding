"""
This is a framework that allows you to call whatever solver you would like.
Just create the respective functions for your preferred library, since we cannot distribute CPLEX :(
Good luck!
"""
#
import logging

try:
    import cplex
except ModuleNotFoundError as e:
    pass
try:
    from optimizer import highs_solver
except ModuleNotFoundError as e:
    pass

optimizers = ["CPLEX", "HiGHS"]
SOLVER = None
model = None


def config(slv):
    global SOLVER
    if slv in optimizers:
        SOLVER = slv
    else:
        raise NotImplementedError("Invalid optimizer chosen.")


class Optimizer:

    def __init__(self, optimizer=None):
        global model
        if SOLVER == "CPLEX":
            model = cplex.Cplex()
        if SOLVER == "HiGHS":
            highs_solver.config()
            model = highs_solver.Model()
        obj_methods = [method_name for method_name in dir(model) if callable(getattr(model, method_name))]
        print()

    def set_solver(self, solver):
        if not optimizers.__contains__(solver):
            logging.error("The solver {} is not implemented.".format(solver))
            raise ModuleNotFoundError
        global SOLVER
        SOLVER = solver

    # MODEL CONSTRUCTION
    @staticmethod
    def set_sense(**kwargs):
        """
        :param kwargs : {"sense":["max", "min"]}
                Defines objective direction
        """
        global model
        if SOLVER == "CPLEX":
            option = {"max": model.objective.sense.maximize,
                      "min": model.objective.sense.minimize}
            model.objective.set_sense(option[kwargs["sense"]])
        elif SOLVER == "HiGHS":
            model.set_sense(kwargs["sense"])

    @staticmethod
    def add_variables(**kwargs):
        """
        :param kwargs : CPLEX{"obj":list, "lb": list, "ub": list, "names": list}
                Defines variables
        """
        global model
        if SOLVER == "CPLEX":
            variables = model.variables.add(obj=kwargs["obj"],
                                            lb=kwargs["lb"],
                                            ub=kwargs["ub"],
                                            names=kwargs["names"])
            return variables
        elif SOLVER == "HiGHS":
            variables = model.add_variables(obj=kwargs["obj"],
                                            lb=kwargs["lb"],
                                            ub=kwargs["ub"],
                                            names=kwargs["names"])
            return variables

    @staticmethod
    def add_constraint(**kwargs):
        """
        :param kwargs : CPLEX{"names":list, "lin_expr": list, "rhs": list, "senses": list}
                Create constraint
        """
        global model
        if SOLVER == "CPLEX":
            model.linear_constraints.add(names=kwargs["names"],
                                         lin_expr=kwargs["lin_expr"],
                                         rhs=kwargs["rhs"],
                                         senses=kwargs["senses"]
                                         )
        elif SOLVER == "HiGHS":
            model.add_constraint(names=kwargs["names"],
                                 lin_expr=kwargs["lin_expr"],
                                 rhs=kwargs["rhs"],
                                 senses=kwargs["senses"]
                                 )

    # CHANGING CURRENT MODEL
    @staticmethod
    def set_constraint_rhs(seq_of_pairs):
        """
        :param seq_of_pairs: tuple with constraint names and values
        """
        global model
        if SOLVER == "CPLEX":
            model.linear_constraints.set_rhs(seq_of_pairs)
        elif SOLVER == "HiGHS":
            model.set_constraint_rhs(seq_of_pairs)

    @staticmethod
    def set_objective_function(objective_vector):
        """
        :param objective_vector: list with floats
        """
        global model
        if SOLVER == "CPLEX":
            model.objective.set_linear(objective_vector)
        elif SOLVER == "HiGHS":
            model.set_objective_function(objective_vector)

    # AUXILIARY FUNCTIONS
    @staticmethod
    def get_constraints_names():
        """
        :return: list with constraint names
        """
        if SOLVER == "CPLEX":
            return model.linear_constraints.get_names()
        elif SOLVER == "HiGHS":
            return model.get_constraints_names()

    @staticmethod
    def get_constraints_rhs(constraints):
        """
        :type constraints: list with constraint names
        :return: list with constraint rhs
        """
        if SOLVER == "CPLEX":
            return model.linear_constraints.get_rhs(constraints)
        elif SOLVER == "HiGHS":
            return model.get_constraints_rhs(constraints)

    @staticmethod
    def get_variable_names():
        """
        :return: list with variable names
        """
        if SOLVER == "CPLEX":
            return model.variables.get_names()
        elif SOLVER == "HiGHS":
            return model.get_variable_names()

    # SOLVING AND RESULTS
    @staticmethod
    def solve():
        """Solve model"""
        global model
        if SOLVER == "CPLEX":
            model.solve()
        elif SOLVER == "HiGHS":
            model.solve()

    @staticmethod
    def feasopt():
        """Relax the constraints"""
        global model
        if SOLVER == "CPLEX":
            model.feasopt.linear_constraints()
        elif SOLVER == "HiGHS":
            raise RuntimeError("Chosen solver <{0}> has no method to execute {1}.".format(
                SOLVER, "feasopt"
            ))

    @staticmethod
    def get_solution_status():
        """Status Solution"""
        global model
        if SOLVER == "CPLEX":
            return model.solution.get_status_string()
        elif SOLVER == "HiGHS":
            return model.get_solution_status()

    @staticmethod
    def get_solution_vec():
        """Solution vector respective to the variables
        :rtype: list
        """
        global model
        if SOLVER == "CPLEX":
            return model.solution.get_values()
        elif SOLVER == "HiGHS":
            return model.get_solution_vec()

    @staticmethod
    def get_solution_obj():
        """
        :return: objective function value after solve
        :rtype: float
        """
        global model
        if SOLVER == "CPLEX":
            return model.solution.get_objective_value()
        elif SOLVER == "HiGHS":
            return model.get_solution_obj()

    @staticmethod
    def get_solution_activity_levels(constraints):
        """
        :type constraints: list with constraint names
        :return: float, objective function value after solve
        """
        global model
        if SOLVER == "CPLEX":
            return model.solution.get_activity_levels(constraints)
        elif SOLVER == "HiGHS":
            return model.get_solution_activity_levels(constraints)

    # DUAL PROBLEM
    @staticmethod
    def get_dual_reduced_costs():
        """
        :return: list, reduced costs
        """
        global model
        if SOLVER == "CPLEX":
            return model.solution.get_reduced_costs()
        elif SOLVER == "HiGHS":
            return model.get_dual_reduced_costs()

    @staticmethod
    def get_dual_values():
        """
        :return: list, dual variables values
        """
        global model
        if SOLVER == "CPLEX":
            return model.solution.get_dual_values()
        elif SOLVER == "HiGHS":
            return model.get_dual_values()

    @staticmethod
    def get_dual_linear_slacks():
        """
        :return: list, linear slacks of constraints
        """
        global model
        if SOLVER == "CPLEX":
            return model.solution.get_linear_slacks()
        elif SOLVER == "HiGHS":
            return model.get_dual_linear_slacks()

    # DEBUGGING PURPOSES
    @staticmethod
    def write_lp(**kwargs):
        """
        :param kwargs: name and filetype (extension)
        :type kwargs:[str, str]
        :return: void, write lp model in txt file
        """
        global model
        if SOLVER == "CPLEX":
            model.write(kwargs["name"])
        elif SOLVER == "HiGHS":
            model.write(kwargs["name"])

    @staticmethod
    def write_solution(file_name):
        """
        :type file_name: str
        :return: void, write solution in xml file
        """
        global model
        if SOLVER == "CPLEX":
            model.solution.write(file_name)
        elif SOLVER == "HiGHS":
            model.write_solution(file_name)
