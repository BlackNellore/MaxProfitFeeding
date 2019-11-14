"""
This is a framework that allows you to call whatever solver you would like.
Just create the respective functions for your preferred library, since we cannot distribute CPLEX :(
Good luck!
"""
import cplex

opt = None
model = None


class Optimizer:
    optmizers = ["CPLEX"]

    def __init__(self, optimizer=None):
        global opt
        global model
        if optimizer in self.optmizers:
            opt = optimizer
        else:
            raise RuntimeError("Invalid optimizer chosen.")
        if opt is "CPLEX":
            model = cplex.Cplex()

    # MODEL CONSTRUCTION
    @staticmethod
    def set_sense(**kwargs):
        """
        :param kwargs : {"sense":["max", "min"]}
                Defines objective direction
        """
        if opt is "CPLEX":
            option = {"max": model.objective.sense.maximize,
                      "min": model.objective.sense.minimize}
            model.objective.set_sense(option[kwargs["sense"]])

    @staticmethod
    def add_variables(**kwargs):
        """
        :param kwargs : CPLEX{"obj":list, "lb": list, "ub": list, "names": list}
                Defines variables
        """
        if opt is "CPLEX":
            variables = model.variables.add(obj=kwargs["obj"],
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
        if opt is "CPLEX":
            model.linear_constraints.add(names=kwargs["names"],
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
        if opt is "CPLEX":
            model.linear_constraints.set_rhs(seq_of_pairs)

    @staticmethod
    def set_objective_function(objective_vector):
        """
        :param objective_vector: list with floats
        """
        if opt is "CPLEX":
            model.objective.set_linear(objective_vector)

    # AUXILIARY FUNCTIONS
    @staticmethod
    def get_constraints_names():
        """
        :return: list with constraint names
        """
        if opt is "CPLEX":
            return model.linear_constraints.get_names()

    @staticmethod
    def get_constraints_rhs(constraints):
        """
        :type constraints: list with constraint names
        :return: list with constraint names
        """
        if opt is "CPLEX":
            return model.linear_constraints.get_rhs(constraints)

    @staticmethod
    def get_variable_names():
        """
        :return: list with variable names
        """
        if opt is "CPLEX":
            return model.variables.get_names()

    # SOLVING AND RESULTS
    @staticmethod
    def solve():
        """Solve model"""
        if opt is "CPLEX":
            model.solve()

    @staticmethod
    def feasopt():
        """Relax the constraints"""
        if opt is "CPLEX":
            model.feasopt.linear_constraints()

    @staticmethod
    def get_solution_status():
        """Status Solution"""
        if opt is "CPLEX":
            return model.solution.get_status_string()

    @staticmethod
    def get_solution_vec():
        """Solution vector respective to the variables"""
        if opt is "CPLEX":
            return model.solution.get_values()

    @staticmethod
    def get_solution_obj():
        """
        :return: float, objective function value after solve
        """
        if opt is "CPLEX":
            return model.solution.get_objective_value()

    @staticmethod
    def get_solution_activity_levels(constraints):
        """
        :type constraints: list with constraint names
        :return: float, objective function value after solve
        """
        if opt is "CPLEX":
            return model.solution.get_activity_levels(constraints)

    # DUAL PROBLEM
    @staticmethod
    def get_dual_reduced_costs():
        """
        :return: list, reduced costs
        """
        if opt is "CPLEX":
            return model.solution.get_reduced_costs()

    @staticmethod
    def get_dual_values():
        """
        :return: list, dual variables values
        """
        if opt is "CPLEX":
            return model.solution.get_dual_values()

    @staticmethod
    def get_dual_linear_slacks():
        """
        :return: list, linear slacks of constraints
        """
        if opt is "CPLEX":
            return model.solution.get_linear_slacks()

    # DEBUGGING PURPOSES
    @staticmethod
    def write_lp(**kwargs):
        """
        :type name:str
        :type filetype: str
        :return: void, write lp model in txt file
        """
        if opt is "CPLEX":
            model.write(kwargs["name"], filetype=kwargs["filetype"])

    @staticmethod
    def write_solution(file_name):
        """
        :type file_name: str
        :return: void, write solution in xml file
        """
        if opt is "CPLEX":
            model.solution.write(file_name)
