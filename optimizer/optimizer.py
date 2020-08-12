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


def config(slv):
    global SOLVER
    if slv in optimizers:
        SOLVER = slv
    else:
        raise NotImplementedError("Invalid optimizer chosen.")


class Optimizer:
    model = None

    def __init__(self, optimizer=None):
        if SOLVER == "CPLEX":
            self.model = cplex.Cplex()
        if SOLVER == "HiGHS":
            highs_solver.config()
            self.model = highs_solver.Model()
        obj_methods = [method_name for method_name in dir(self.model) if callable(getattr(self.model, method_name))]
        print()

    def set_solver(self, solver):
        if not optimizers.__contains__(solver):
            logging.error("The solver {} is not implemented.".format(solver))
            raise ModuleNotFoundError
        global SOLVER
        SOLVER = solver

    # self.model CONSTRUCTION

    def set_sense(self, **kwargs):
        """
        :param kwargs : {"sense":["max", "min"]}
                Defines objective direction
        """
        
        if SOLVER == "CPLEX":
            option = {"max": self.model.objective.sense.maximize,
                      "min": self.model.objective.sense.minimize}
            self.model.objective.set_sense(option[kwargs["sense"]])
        elif SOLVER == "HiGHS":
            self.model.set_sense(kwargs["sense"])


    def add_variables(self, **kwargs):
        """
        :param kwargs : CPLEX{"obj":list, "lb": list, "ub": list, "names": list}
                Defines variables
        """
        
        if SOLVER == "CPLEX":
            variables = self.model.variables.add(obj=kwargs["obj"],
                                                 lb=kwargs["lb"],
                                                 ub=kwargs["ub"],
                                                 names=kwargs["names"])
            return variables
        elif SOLVER == "HiGHS":
            variables = self.model.add_variables(obj=kwargs["obj"],
                                                 lb=kwargs["lb"],
                                                 ub=kwargs["ub"],
                                                 names=kwargs["names"])
            return variables


    def add_constraint(self, **kwargs):
        """
        :param kwargs : CPLEX{"names":list, "lin_expr": list, "rhs": list, "senses": list}
                Create constraint
        """
        
        if SOLVER == "CPLEX":
            self.model.linear_constraints.add(names=kwargs["names"],
                                              lin_expr=kwargs["lin_expr"],
                                              rhs=kwargs["rhs"],
                                              senses=kwargs["senses"]
                                              )
        elif SOLVER == "HiGHS":
            self.model.add_constraint(names=kwargs["names"],
                                      lin_expr=kwargs["lin_expr"],
                                      rhs=kwargs["rhs"],
                                      senses=kwargs["senses"]
                                      )

    # CHANGING CURRENT self.model
    def set_obj_offset(self, val):
        if SOLVER == "CPLEX":
            self.model.objective.set_offset(val)
        elif SOLVER == "HiGHS":
            self.model.set_objective_offset(val)

    def set_constraint_sense(self, cst_name, sense):
        """
         constraint name and new sense (L or G)
        """
        if SOLVER == "CPLEX":
            self.model.linear_constraints.set_senses(cst_name, sense)
        elif SOLVER == "HiGHS":
            self.model.set_constraint_sense(cst_name, sense)

    def set_constraint_rhs(self, seq_of_pairs):
        """
        :param seq_of_pairs: tuple with constraint names and values
        """
        
        if SOLVER == "CPLEX":
            self.model.linear_constraints.set_rhs(seq_of_pairs)
        elif SOLVER == "HiGHS":
            self.model.set_constraint_rhs(seq_of_pairs)

    def set_constraint_coefficients(self, seq_of_triplets):
        """
        [(constraint, var_name, value)]
        """
        if SOLVER == "CPLEX":
            self.model.linear_constraints.set_coefficients(seq_of_triplets)
        elif SOLVER == "HiGHS":
            self.model.set_constraint_coefficients(seq_of_triplets)

    def set_objective_function(self, objective_vector, offset=0):
        """
        :param objective_vector: list with floats
        """
        
        if SOLVER == "CPLEX":
            self.model.objective.set_linear(objective_vector)
        elif SOLVER == "HiGHS":
            self.model.set_objective_function(objective_vector)

        self.set_obj_offset(offset)

    # AUXILIARY FUNCTIONS

    def get_constraints_names(self):
        """
        :return: list with constraint names
        """
        if SOLVER == "CPLEX":
            return self.model.linear_constraints.get_names()
        elif SOLVER == "HiGHS":
            return self.model.get_constraints_names()


    def get_constraints_rhs(self, constraints):
        """
        :type constraints: list with constraint names
        :return: list with constraint rhs
        """
        if SOLVER == "CPLEX":
            return self.model.linear_constraints.get_rhs(constraints)
        elif SOLVER == "HiGHS":
            return self.model.get_constraints_rhs(constraints)


    def get_variable_names(self):
        """
        :return: list with variable names
        """
        if SOLVER == "CPLEX":
            return self.model.variables.get_names()
        elif SOLVER == "HiGHS":
            return self.model.get_variable_names()

    # SOLVING AND RESULTS

    def solve(self):
        """Solve self.model"""
        
        if SOLVER == "CPLEX":
            self.model.solve()
        elif SOLVER == "HiGHS":
            self.model.solve()


    def feasopt(self):
        """Relax the constraints"""
        
        if SOLVER == "CPLEX":
            self.model.feasopt.linear_constraints()
        elif SOLVER == "HiGHS":
            raise RuntimeError("Chosen solver <{0}> has no method to execute {1}.".format(
                SOLVER, "feasopt"
            ))


    def get_solution_status(self):
        """Status Solution"""
        
        if SOLVER == "CPLEX":
            return self.model.solution.get_status_string()
        elif SOLVER == "HiGHS":
            return self.model.get_solution_status()


    def get_solution_vec(self):
        """Solution vector respective to the variables
        :rtype: list
        """
        
        if SOLVER == "CPLEX":
            return self.model.solution.get_values()
        elif SOLVER == "HiGHS":
            return self.model.get_solution_vec()


    def get_solution_obj(self):
        """
        :return: objective function value after solve
        :rtype: float
        """
        
        if SOLVER == "CPLEX":
            return self.model.solution.get_objective_value()
        elif SOLVER == "HiGHS":
            return self.model.get_solution_obj()


    def get_solution_activity_levels(self, constraints):
        """
        :type constraints: list with constraint names
        :return: float, objective function value after solve
        """
        
        if SOLVER == "CPLEX":
            return self.model.solution.get_activity_levels(constraints)
        elif SOLVER == "HiGHS":
            return self.model.get_solution_activity_levels(constraints)

    # DUAL PROBLEM

    def get_dual_reduced_costs(self):
        """
        :return: list, reduced costs
        """
        
        if SOLVER == "CPLEX":
            return self.model.solution.get_reduced_costs()
        elif SOLVER == "HiGHS":
            return self.model.get_dual_reduced_costs()


    def get_dual_values(self):
        """
        :return: list, dual variables values
        """
        
        if SOLVER == "CPLEX":
            return self.model.solution.get_dual_values()
        elif SOLVER == "HiGHS":
            return self.model.get_dual_values()


    def get_dual_linear_slacks(self):
        """
        :return: list, linear slacks of constraints
        """
        
        if SOLVER == "CPLEX":
            return self.model.solution.get_linear_slacks()
        elif SOLVER == "HiGHS":
            return self.model.get_dual_linear_slacks()

    # DEBUGGING PURPOSES

    def write_lp(self, **kwargs):
        """
        :param kwargs: name and filetype (extension)
        :type kwargs:[str, str]
        :return: void, write lp self.model in txt file
        """
        
        if SOLVER == "CPLEX":
            self.model.write(kwargs["name"])
        elif SOLVER == "HiGHS":
            self.model.write(kwargs["name"])


    def write_solution(self, file_name):
        """
        :type file_name: str
        :return: void, write solution in xml file
        """
        
        if SOLVER == "CPLEX":
            self.model.solution.write(file_name)
        elif SOLVER == "HiGHS":
            self.model.write_solution(file_name)
