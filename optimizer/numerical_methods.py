import numpy as np
from aenum import Enum
import logging
from model.lp_model import Model

Status = Enum('Status', 'EMPTY READY SOLVED ERROR')


class Searcher:
    _model: Model = None
    _obj_func_key = None
    _prefix_id = None

    _status = Status.EMPTY
    _solutions = None

    def __init__(self, model, obj_func_key="obj_func", pre_id=""):
        # if isinstance(model, type(Model)):
        #     error_message = "The parsed model is not acceptable." \
        #                     " Item must be a lpmodel.Model() instance, type found: {0}".format(type(model))
        #     raise IOError(error_message)

        self._model = model
        self._obj_func_key = obj_func_key
        self._solutions = []
        self._status = Status.READY
        self._prefix_id = pre_id
        self._model.prefix_id = pre_id

    def refine_bounds(self, lb=0.0, ub=1.0, tol=0.01):
        new_lb = self.refine_bound(lb, ub, direction=1, tol=tol)
        if new_lb is None:
            return None, None
        new_ub = self.refine_bound(lb, ub, direction=-1, tol=tol)
        return new_lb, new_ub

    def refine_bound(self, v0=0.0, vf=1.0, direction=1, tol=0.01):
        """Return feasible parameter vi in S = [v0, vf] or solution dict of S """
        space = np.linspace(v0, vf, int(np.ceil((vf - v0) / tol)))
        if direction == -1:
            space = reversed(space)
        new_v = self.__brute_force(self._model.run, space, first_feasible=True)
        if new_v is None:
            return new_v
        else:
            return new_v['CNEm']

    def brute_force_search(self, lb, ub, p_tol, uncertain_bounds=False):
        """Executes brute force search algorithm"""
        if self._status != Status.READY:
            self.__clear_searcher()
        if uncertain_bounds:
            lb, ub = self.refine_bounds(lb, ub, 0.001)
            if lb is None:
                self._status = Status.ERROR
                return
        cnem_space = np.linspace(lb, ub, int(np.ceil((ub - lb) / p_tol)))
        bf_results = self.__brute_force(self._model.run, cnem_space)
        if len(bf_results) == 0:
            self._status = Status.ERROR
        else:
            self._status = Status.SOLVED
        return bf_results

    @staticmethod
    def __brute_force(f, search_space, first_feasible=False):
        """
        Run Brute Force algorithm in a function f. In this model f is lp_model.Model.run()
        """
        try:
            if first_feasible:
                for i, val in enumerate(search_space):
                    r = f(i, val)
                    logging.info("Brute force <iteration, cnem>: <{0}, {1}>".format(i, val))
                    if r is not None:
                        return r
            else:
                results = []
                for i, val in enumerate(search_space):
                    logging.info("ID: {}".format(i))
                    r = f(i, val)
                    if r is not None:
                        results.append(r)
                        logging.info("Solution Appended")
                    else:
                        logging.info("Infeasible")
                return results

        except TypeError as e:
            logging.error("An error occurred in numerical_method.Searcher.__brute_force method: {}".format(e))
            return None

    def golden_section_search(self, lb, ub, p_tol, uncertain_bounds=False):
        """Executes golden-section search algorithm"""
        if self._status != Status.READY:
            self.__clear_searcher()
        if uncertain_bounds: # TODO
            lb, ub = self.refine_bounds(lb, ub, 0.001)
            if lb is None:
                self._status = Status.ERROR
                return
        gss_results = []
        a, b = self.__golden_section_search_recursive(self._model.run, lb, ub, gss_results, tol=p_tol)
        if a is None:
            self._status = Status.ERROR
        else:
            self._status = Status.SOLVED
        return gss_results

    def __golden_section_search_recursive(
            self, f, a, b, results, p_id=0, tol=1e-3, h=None, c=None, d=None, fc=None, fd=None):
        """
        Run GSS algorithm in a function f. In this model f is lp_model.Model.run()
        To change evaluation function, rewrite _get_f(solution_element)
        _get_f must return a float or integer value to be compared with <, > operators
        """

        def _get_f(solution_element):
            """Extract evaluation value for method __golden_section_search_recursive"""
            return solution_element[self._obj_func_key]

        inv_phi = (np.sqrt(5) - 1) / 2
        inv_phi2 = (3 - np.sqrt(5)) / 2

        try:
            logging.info("\n{0}".format(p_id))
            (a, b) = (min(a, b), max(a, b))
            if h is None:
                h = b - a
            if h <= tol:
                if len(results) == 0:
                    solution = f(p_id, a)
                    results.append(solution)
                return a, b
            if c is None:
                c = a + inv_phi2 * h
            if d is None:
                d = a + inv_phi * h
            if fc is None:
                solution = f(p_id, c)
                fc = _get_f(solution)
                results.append(solution)
            if fd is None:
                solution = f(p_id, d)
                fd = _get_f(solution)
                results.append(solution)
            if fc > fd:
                return self.__golden_section_search_recursive(
                    f, a, d, results, p_id+1, tol, h * inv_phi, d=c, fd=fc)
            else:
                return self.__golden_section_search_recursive(
                    f, c, b, results, p_id+1, tol, h * inv_phi, c=d, fc=fd)
        except TypeError as e:
            logging.error("An error occurred in GSS method:\n{}".format(e))
            return None, None

    def single_objective(self, algorithm, lb, ub, tol):
        self.__clear_searcher()
        self._solutions = []
        self._solutions_multiobjective = []
        self._prefix_id = f"single objective lb={lb}, ub={ub}, algorithm={algorithm}"
        sol_vec = getattr(self, algorithm)(lb, ub, tol)
        status, solution = self.get_results(sol_vec, best=False)
        if status == Status.SOLVED:
            self._solutions = solution

    def multi_objective(self, algorithm, lb, ub, tol, lca_id=1): # Adapt to series
        self._solutions = []
        self._solutions_multiobjective = []
        if lca_id <= 0:
            logging.error(f"Multi-objective must have valid LCA ID. Check the input spreadsheet. LCA ID = {lca_id}")
        self._model: Model = self._model
        forage = ['G', 'L']
        for v in forage:
            self.__clear_searcher()
            self._model.set_obj_weights(1.0, 0.0)
            self._model.set_forage(v)
            self._prefix_id = f"multi objective lb={lb}, ub={ub}, algorithm={algorithm}, max f1"
            self._prefix_id += f", forage = {v}"

            sol_vec = getattr(self, algorithm)(lb, ub, tol, uncertain_bounds=True)  # max f1
            status, solution = self.get_results(sol_vec, best=True)  # get f1_ub, f2_lb
            if solution is None:
                logging.error(f"Model is infeasible for forage concentration {v} 20%")
                continue
            f1_ub, f2_ub = self._model.get_obj_sol(solution)  # get f1_ub, f2_lb

            self._model.set_obj_weights(0.0, 1.0)
            self.__clear_searcher()
            self._prefix_id = f"multi objective lb={lb}, ub={ub}, algorithm={algorithm}, max f2"
            self._prefix_id += f", forage = {v}"

            sol_vec = getattr(self, algorithm)(lb, ub, tol, uncertain_bounds=True)  # max f2
            status, solution = self.get_results(sol_vec, best=True)  # get f1_lb, f2_ub
            f1_lb, f2_lb = self._model.get_obj_sol(solution)  # get f1_l, f2_ub

            n_vals = int(np.ceil((1 + f2_ub - f2_lb) / tol))
            n_vals = 50  # TODO remove
            lca_rhs_space = np.linspace(f2_lb + 0.0001, f2_ub, n_vals)  # range[f2_lb, f2_ub]
            self._model.set_obj_weights(1.0, 0.0)
            for rhs in lca_rhs_space:
                self._model.set_LCA_rhs(rhs)
                self.__clear_searcher()
                self._prefix_id = f"multi objective lb={lb}, ub={ub}, algorithm={algorithm}, rhs={rhs}"
                self._prefix_id += f", forage = {v}"
                sol_vec = getattr(self, algorithm)(lb, ub, tol, uncertain_bounds=True)
                status, solution = self.get_results(sol_vec, best=True)
                # self._model.write_lp_inside(rhs)
                if status == Status.SOLVED:
                    self._solutions_multiobjective.append(solution)
                else:
                    raise Exception("Multi-objective failure: Something wrong is going on. numerical_methods.py l182")
            self._solutions += self._solutions_multiobjective

    def get_results(self, solution_vec = None, best=False):
        """
        Return list with results or optimal solution in a list
        return type is either list or float
        """
        if solution_vec is None:
            solution_vec = self._solutions
        if len(solution_vec) == 0 or self._status != Status.SOLVED:
            return self._status, None
        if best:
            result = self.__extract_optimal(solution_vec)
        else:
            result = solution_vec.copy()
        return self._status, result

    def __extract_optimal(self, results, direction=1):
        """Extract optimal solution from list, Max: direction = 1; Min: direction = -1"""
        if direction != 1 and direction != -1:
            error_message = "The parsed value for \"direction\" is not acceptable." \
                            " Value must be 1 or -1, value parsed: {0}".format(direction)
            raise IOError(error_message)
        if results is None:
            logging.info("Result vector is None..{0}, {1}".format(self._status, self._prefix_id))
            return None
        if len(results) <= 0:
            return None

        obj_vals = [p['obj_func']*direction for p in results]
        best_id = [i for i, j in enumerate(obj_vals) if j == max(obj_vals)]
        return results[best_id[0]]

    def __clear_searcher(self):
        self._solutions.clear()
        self._status = Status.READY
        self._model.prefix_id = self._prefix_id


Algorithms = {'BF': 'brute_force_search', 'GSS': 'golden_section_search'}

if __name__ == "__main__":
    print("hello numerical_methods")