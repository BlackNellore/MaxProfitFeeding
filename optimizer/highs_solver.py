import ctypes
import logging
import numpy as np
from scipy.sparse import csc_matrix
import platform

# highs lib folder must be in "LD_LIBRARY_PATH" environment variable
highslib = None

def_status = {0: "optimal", None: "infeasible"}
epsilon = 0.0000001
infinite = 10000000


def config():
    global highslib
    if platform.system() in ('Windows', 'Microsoft'):
        highslib = ctypes.cdll.LoadLibrary("./optimizer/resources/highs.dll")
    else:
        # TODO: Implement call to LINUX .so solver
        raise SystemError("Only windows dll available")

    highslib.Highs_call.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_int),
                                    ctypes.POINTER(ctypes.c_int),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_int),
                                    ctypes.POINTER(ctypes.c_int),
                                    ctypes.POINTER(ctypes.c_int))
    highslib.Highs_call.restype = ctypes.c_int


def highs_call(colcost, collower, colupper, rowlower, rowupper, astart, aindex, avalue):
    """
    :param colcost: obj-fun coefficients [default minimize]
    :param collower: vector variables lower bound
    :param colupper: vector variables upper bound
    :param rowlower: vector with constraints lhs bounds
    :param rowupper: vector with constraints rhs bounds
    :param astart: column pointer vector (column compression matrix)
    :param aindex: row-index vector (column compression matrix)
    :param avalue: non-zero coefficients vector (column compression matrix)
    :returns retcode: status code
    :returns col_value: optimal variables' values
    :returns col_dual: optimal dual variables' values (shadow price)
    :returns row_value: Ax
    :returns row_dual: reduced costs of constraints
    :returns col_basis: check comment on Enum objetc below
    :returns row_basis: check comment on Enum objetc below

     enum class HighsBasisStatus {
       LOWER =
           0,  // (slack) variable is at its lower bound [including fixed variables]
       BASIC,  // (slack) variable is basic
       UPPER,  // (slack) variable is at its upper bound
       ZERO,   // free variable is non-basic and set to zero
       NONBASIC, // nonbasic with no specific bound information - useful for users and postsolve
       SUPER   // Super-basic variable: non-basic and either free and
               // nonzero or not at a bound. No SCIP equivalent
     };
    """

    global highslib
    n_col = len(colcost)
    n_row = len(rowlower)
    n_nz = len(aindex)

    dbl_array_type_col = ctypes.c_double * n_col
    dbl_array_type_row = ctypes.c_double * n_row
    int_array_type_astart = ctypes.c_int * (n_col + 1)
    int_array_type_aindex = ctypes.c_int * n_nz
    dbl_array_type_avalue = ctypes.c_double * n_nz

    int_array_type_col = ctypes.c_int * n_col
    int_array_type_row = ctypes.c_int * n_row

    col_value = [0] * n_col
    col_dual = [0] * n_col

    row_value = [0] * n_row
    row_dual = [0] * n_row

    col_basis = [0] * n_col
    row_basis = [0] * n_row

    return_val = 0

    col_value = dbl_array_type_col(*col_value)
    col_dual = dbl_array_type_col(*col_dual)
    row_value = dbl_array_type_row(*row_value)
    row_dual = dbl_array_type_row(*row_dual)
    col_basis = int_array_type_col(*col_basis)
    row_basis = int_array_type_row(*row_basis)
    logging.info(f"colcost=[{colcost}\n"
                 f"collower={collower}\n"
                 f"colupper={colupper}\n"
                 f"rowlower={rowlower}\n"
                 f"rowupper={rowupper}\n"
                 f"astart={astart}\n"
                 f"aindex={aindex}\n"
                 f"avalue={avalue}\n")
    try:
        retcode = highslib.Highs_call(
            ctypes.c_int(n_col), ctypes.c_int(n_row), ctypes.c_int(n_nz),
            dbl_array_type_col(*colcost), dbl_array_type_col(*collower), dbl_array_type_col(*colupper),
            dbl_array_type_row(*rowlower), dbl_array_type_row(*rowupper),
            int_array_type_astart(*astart), int_array_type_aindex(*aindex), dbl_array_type_avalue(*avalue),
            col_value, col_dual,
            row_value, row_dual,
            col_basis, row_basis, ctypes.byref(ctypes.c_int(return_val)))
        print(retcode)
    except Exception as e:
        if "writing" in e.args[0]:
            logging.error("A serious error occurred when executing HiGHS: {}".format(str(e)))
        else:
            logging.error("An error occurred when executing HiGHS, probably infeasible: {}".format(str(e)))
        return None
    return retcode, list(col_value), list(col_dual), list(row_value), list(row_dual), list(col_basis), list(row_basis)


class Model:
    class _Solution:
        status, variables, dual_variables, constraints, slacks, reduced_cost, basic_variables = \
            [None for i in range(7)]
        opt_objective = None

        def __init__(self, *args):
            [var_names, cstrs] = args
            self.variables = dict(zip(list(var_names), [None for i in range(len(var_names))]))
            self.basic_variables = dict(zip(list(var_names), [None for i in range(len(var_names))]))
            self.constraints = dict(zip(list(cstrs.keys()),[{} for i in range(len(cstrs))]))
            for constraint in cstrs.keys():
                self.constraints[constraint]["optimal"] = None
                self.constraints[constraint]["slack"] = cstrs[constraint]["rhs"]
                self.constraints[constraint]["active"] = None

        def get_solution(self, *args):
            if args[0] is None:
                self.status = args[0]
            else:
                [self.status,
                 aux_variables,
                 self.dual_variables,
                 aux_constraints,
                 self.reduced_cost,
                 aux_active_constraints,
                 aux_basic_variables] = args[0]
                var_names = list(self.variables.keys())
                for i in range(len(aux_variables)):
                    self.variables[var_names[i]] = aux_variables[i]
                    self.basic_variables[var_names[i]] = aux_basic_variables

                const_names = list(self.constraints.keys())
                for i in range(len(aux_constraints)):
                    self.constraints[const_names[i]]["optimal"] = aux_constraints[i]
                    slack = self.constraints[const_names[i]]["slack"]
                    self.constraints[const_names[i]]["slack"] = abs(aux_constraints[i] - slack)
                    self.constraints[const_names[i]]["active"] = aux_active_constraints[i]
            self.status = def_status[self.status]

        def comp_objective(self, variables_coef):
            if not self.status.__contains__("infeasible"):
                self.opt_objective = float(np.dot(list(variables_coef.values()), list(self.variables.values())))

    colcost, collower, colupper, rowlower, rowupper, astart, aindex, avalue = [[] for i in range(8)]
    var_map = {}
    rev_var_map = {}
    cs_map = {}
    rev_cs_map = {}
    solution = None
    sense, variables, constraints, var_lb, var_ub = [None for j in range(5)]
    objective_offset = 0

    def __init__(self):
        self.variables = {}
        self.constraints = {}
        self.var_lb = {}
        self.var_ub = {}

    def _solve(self):
        if self.solution is None:
            self.solution = self._Solution(self.variables.keys(), self.constraints)

        sol_highs = highs_call(
            self.colcost,
            self.collower,
            self.colupper,
            self.rowlower,
            self.rowupper,
            self.astart,
            self.aindex,
            self.avalue)
        self.solution.get_solution(sol_highs)

        self.solution.comp_objective(self.variables)

    def _model_check(self):
        self.colcost, self.collower, self.colupper, self.rowlower,\
        self.rowupper, self.astart, self.aindex, self.avalue = [[] for i in range(8)]

    def _model_compress(self):
        self.var_map = dict(zip(range(len(self.variables)), self.variables.keys()))
        self.rev_var_map = dict(zip(self.variables.keys(), range(len(self.variables))))
        for var in range(len(self.variables)):
            self.colcost.append(self.variables[self.var_map[var]])
            self.collower.append(self.var_lb[self.var_map[var]])
            self.colupper.append(self.var_ub[self.var_map[var]])
        self.cs_map = dict(zip(range(len(self.constraints)), self.constraints.keys()))
        self.rev_cs_map = dict(zip(self.constraints.keys(), range(len(self.constraints))))
        row = []
        col = []
        data = []
        for cs in range(len(self.constraints)):
            self.rowlower.append(self.constraints[self.cs_map[cs]]["lhs"])
            self.rowupper.append(self.constraints[self.cs_map[cs]]["rhs"])
            # print(self.constraints[self.cs_map[cs]]["coefficients"])
            for j in range(len(self.constraints[self.cs_map[cs]]["variables"])):
                col.append(self.rev_var_map[self.constraints[self.cs_map[cs]]["variables"][j]])
                row.append(cs)
                data.append(self.constraints[self.cs_map[cs]]["coefficients"][j])

        # print("Max: {0}\n\nst:\nrhs:{1}\n\nlhs:{2}\n\nx lb: {3}\n\nx ub: {4}\n\n".format(
        #     self.colcost, self.rowlower, self.rowupper, self.collower, self.colupper))

        sparse_matrix = csc_matrix((data, (row, col)), shape=(len(self.constraints), len(self.variables)))
        self.aindex = list(sparse_matrix.indices)
        self.astart = list(sparse_matrix.indptr)
        self.avalue = list(sparse_matrix.data)

    def set_sense(self, direction="max"):
        if direction == "max":
            self.sense = -1
        elif direction == "min":
            self.sense = 1

    def add_variables(self, obj=None, lb=None, ub=None, names=None):
        """
        :param obj: variables' coefficients on the objective function
        :type obj: list
        :param lb: variables' lower bound
        :type lb: list
        :param ub: variables' upper bound
        :type ub: list
        :param names: variables' names
        :type names: list
        :return:
        """
        if len(obj) != len(ub) or len(obj) != len(lb):
            raise IndexError("lp_model > add_variables, vector's length don't match")
        if len(names) == 0:
            names = list(range(len(obj)))
        for i in range(len(names)):
            self.variables[names[i]] = obj[i] * self.sense
            self.var_lb[names[i]] = lb[i]
            self.var_ub[names[i]] = ub[i]
        return self.variables

    def add_constraint(self, names=None, lin_expr=None, rhs=None, senses=None):
        """
        Default a*x >= b
        :param names: constraint names
        :type names: list
        :param lin_expr: coefficients
        :type names: list(list) [[var_names][coef]]
        :param rhs: right-hand side coefficient
        :type names: list
        :param senses: {E: equal, G: greater-equal, L: lower-equal}
        :type names: list
        """
        for i in range(len(names)):
            if senses[i] == "E":
                # self.equality_constraints.append(names[i])
                self.constraints[names[i]] = {}
                self.constraints[names[i]]["variables"] = lin_expr[i][0]
                self.constraints[names[i]]["coefficients"] = lin_expr[i][1]
                self.constraints[names[i]]["lhs"] = rhs[i] - epsilon
                self.constraints[names[i]]["rhs"] = rhs[i] + epsilon
                self.constraints[names[i]]["sense"] = "E"

            elif senses[i] == "G":
                self.constraints[names[i]] = {}
                self.constraints[names[i]]["variables"] = lin_expr[i][0]
                self.constraints[names[i]]["coefficients"] = lin_expr[i][1]
                self.constraints[names[i]]["lhs"] = rhs[i]
                self.constraints[names[i]]["rhs"] = infinite
                self.constraints[names[i]]["sense"] = "G"
            elif senses[i] == "L":
                self.constraints[names[i]] = {}
                self.constraints[names[i]]["variables"] = lin_expr[i][0]
                self.constraints[names[i]]["coefficients"] = lin_expr[i][1]
                self.constraints[names[i]]["lhs"] = -infinite
                self.constraints[names[i]]["rhs"] = rhs[i]
                self.constraints[names[i]]["sense"] = "L"

    def set_constraint_rhs(self, seq_of_pairs):
        for cons_tuple in seq_of_pairs:
            if self.constraints[cons_tuple[0]]["sense"] == "E":
                self.constraints[cons_tuple[0]]["lhs"] = cons_tuple[1] - epsilon
                self.constraints[cons_tuple[0]]["rhs"] = cons_tuple[1] + epsilon
            if self.constraints[cons_tuple[0]]["sense"] == "L":
                self.constraints[cons_tuple[0]]["rhs"] = cons_tuple[1]
            if self.constraints[cons_tuple[0]]["sense"] == "G":
                self.constraints[cons_tuple[0]]["lhs"] = cons_tuple[1]

    def set_constraint_sense(self, cst_name, sense):
        if sense in ["L", "G"]:
            self.constraints[cst_name]["sense"] = sense
        else:
            raise Exception(f"sense {sense} not supported")

    def set_constraint_coefficients(self, seq_of_triplets):
        for triplet in seq_of_triplets:
            cst = triplet[0]
            var = triplet[1]
            index = list(self.constraints[cst]['variables']).index(var)
            val = triplet[2]
            self.constraints[cst]["coefficients"][index] = val

    def set_objective_offset(self, val):
        self.objective_offset = val

    def get_objective_offset(self):
        return self.objective_offset

    def set_objective_function(self, obj_vec):
        names = list(self.variables.keys())
        for i in range(len(self.variables)):
            if names[i] == obj_vec[i][0]:
                self.variables[names[i]] = obj_vec[i][1] * self.sense
            else:
                logging.error("Variables' names don't match:\n{0}\n{1}\n\n".format(names, obj_vec))
                raise IndexError

    def get_constraints_names(self):
        cs_names = self.constraints.keys()
        return list(dict.fromkeys(cs_names))

    def get_constraints_rhs(self, constraints):
        rhs = []
        for cs_name in constraints:
            if self.constraints[cs_name]["sense"] == "E":
                rhs.append(self.constraints[cs_name]["rhs"] - epsilon)
            if self.constraints[cs_name]["sense"] == "L":
                rhs.append(self.constraints[cs_name]["rhs"])
            if self.constraints[cs_name]["sense"] == "G":
                rhs.append(self.constraints[cs_name]["lhs"])

        return rhs

    def get_variable_names(self):
        return self.variables.keys()

    def solve(self):
        try:
            self._model_check()
            self._model_compress()
            self._solve()
        except Exception as e:
            logging.error("An error occurred:\n{}".format(str(e)))

    def get_solution_status(self):
        return self.solution.status

    def get_solution_vec(self):
        return list(self.solution.variables.values())

    def get_solution_obj(self):
        return self.solution.opt_objective * self.sense + self.objective_offset

    def get_solution_activity_levels(self, constraints):
        activity = []
        for cs_name in constraints:
            activity.append(self.solution.constraints[cs_name]["active"])
        return activity

    def get_dual_reduced_costs(self):
        #return list(self.solution.dual_variables) #list(self.solution.reduced_cost)
        red_costs = []
        for i in range(len(self.solution.dual_variables)):
            red_costs.append(- self.solution.dual_variables[i])
        return red_costs
        
    def get_dual_values(self):
        return list(self.solution.reduced_cost) #list(self.solution.dual_variables)

    def get_dual_linear_slacks(self):
        slacks = []
        for cs_name in self.solution.constraints.keys():
            slacks.append(self.solution.constraints[cs_name]["slack"])
        return slacks

    def write(self, filename):
        # Pffffffffff, no way I am implementing that
        pass

    def write_solution(self, filename):
        # Pffffffffff, no way I am implementing that
        pass
