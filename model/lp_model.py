""" Mathematical model """
from optimizer import optimizer
from model import nrc_equations as nrc
import logging

ds = None

ingredients, h_ingredients, available_feed, h_available_feed, scenarios, h_scenarios = [None for i in range(6)]

cnem_lb, cnem_ub = 0.8, 3

bigM = 100000


class Model:
    p_id, p_breed, p_sbw, p_bcs, p_be, p_l, p_sex, p_a2, p_ph, p_selling_price, p_linearization_factor, \
        p_algorithm, p_identifier, p_lb, p_ub, p_tol, p_lca = [None for i in range(17)]

    _diet = None
    _p_mpm = None
    _p_dmi = None
    _p_nem = None
    _p_pe_ndf = None
    _p_cnem = None
    _var_names_x = None

    _print_model_lp = False
    _print_model_lp_infeasible = False
    _print_solution_xml = False

    opt_sol = None
    prefix_id = ""

    def __init__(self, out_ds, parameters):
        self.__cast_data(out_ds, parameters)
        pass

    def run(self, p_id, p_cnem):
        """Either build or update model, solve ir and return solution = {dict xor None}"""
        logging.info("Populating and running model")
        try:
            self.opt_sol = None
            self._p_cnem = p_cnem
            self.__compute_parameters()
            if self._diet is None:
                self.__build_model()
            else:
                self.__update_model()
            return self.__solve(p_id)
        except Exception as e:
            logging.error("An error occurred:\n{}".format(str(e)))
            return None

    def __solve(self, problem_id):
        """Return None if solution is infeasible or Solution dict otherwise"""
        diet = self._diet
        # diet.write_lp(name="CNEm_{}.lp".format(str(self._p_cnem)))
        diet.solve()
        status = diet.get_solution_status()
        logging.info("Solution status: {}".format(status))
        if status.__contains__("infeasible"):
            sol_id = {"Problem_ID": self.prefix_id + str(problem_id)}
            params = dict(zip(["CNEm", "MPm", "DMI", "NEm", "peNDF"],
                              [self._p_cnem, self._p_mpm * 0.001, self._p_dmi, self._p_nem, self._p_pe_ndf]))
            sol = {**sol_id, **params}
            self.opt_sol = None
            logging.warning("Infeasible parameters:{}".format(sol))
            return None

        sol_id = {"Problem_ID": problem_id}
        sol = dict(zip(diet.get_variable_names(), diet.get_solution_vec()))
        sol["obj_profit"] = diet.get_solution_obj()
        sol["obj_cost"] = 0
        sol["factor"] = (self._p_dmi - self._p_nem / self._p_cnem)
        sol["CNEg"] = 0
        for i in range(len(self.cost_vector)):
            sol["CNEg"] += self.neg_vector[i] * diet.get_solution_vec()[i]
            sol["obj_cost"] += diet.get_solution_vec()[i] * self.cost_vector[i]
        sol["obj_cost"] *= self._p_dmi

        p_swg = nrc.swg(sol["CNEg"], self._p_dmi, self._p_cnem, self._p_nem, self.p_sbw, self.p_linearization_factor)
        params = dict(zip(["CNEm", "MPm", "DMI", "NEm", "SWG", "peNDF"],
                          [self._p_cnem, self._p_mpm * 0.001, self._p_dmi, self._p_nem, p_swg, self._p_pe_ndf]))
        sol_activity = dict(zip(["{}_act".format(constraint) for constraint in self.constraints_names],
                                diet.get_solution_activity_levels(self.constraints_names)))
        sol_rhs = dict(zip(["{}_rhs".format(constraint) for constraint in self.constraints_names],
                           diet.get_constraints_rhs(self.constraints_names)))
        sol_red_cost = dict(zip(["{}_red_cost".format(var) for var in diet.get_variable_names()],
                                diet.get_dual_reduced_costs()))
        sol_dual = dict(zip(["{}_dual".format(const) for const in diet.get_constraints_names()],
                            diet.get_dual_values()))
        sol_slack = dict(zip(["{}_slack".format(const) for const in diet.get_constraints_names()],
                             diet.get_dual_linear_slacks()))
        sol_obj_cost = dict(zip(["{}_obj_cneg".format(var) for var in diet.get_variable_names()],
                                self.neg_vector))
        sol = {**sol_id, **params, **sol, **sol_rhs, **sol_activity,
               **sol, **sol_dual, **sol_red_cost, **sol_slack, **sol_obj_cost}
        self.opt_sol = diet.get_solution_obj()

        return sol

    # Parameters filled by inner method .__cast_data()
    n_ingredients = None
    cost_vector = None
    neg_vector = None
    cost_obj_vector = None
    constraints_names = None

    def __cast_data(self, out_ds, parameters):
        """Retrieve parameters data from table. See data_handler.py for more"""
        global ds
        global ingredients
        global h_ingredients
        global available_feed
        global h_available_feed
        global scenarios
        global h_scenarios

        ds = out_ds

        ingredients = ds.data_feed_scenario
        h_ingredients = ds.headers_data_feed
        available_feed = ds.data_available_feed
        h_available_feed = ds.headers_available_feed
        scenarios = ds.data_scenario
        h_scenarios = ds.headers_data_scenario

        self.n_ingredients = available_feed.last_valid_index()
        self.cost_vector = ds.get_column_data(available_feed, h_available_feed.s_feed_cost)
        self.neg_vector = ds.get_column_data(ingredients, h_ingredients.s_NEga)
        [self.p_id, self.p_breed, self.p_sbw, self.p_bcs, self.p_be, self.p_l, self.p_sex, self.p_a2, self.p_ph,
         self.p_selling_price, self.p_linearization_factor,
         self.p_algorithm, self.p_identifier, self.p_lb, self.p_ub, self.p_tol, self.p_lca] = parameters.values()

    def __compute_parameters(self):
        """Compute parameters variable with CNEm"""
        self._p_mpm, self._p_dmi, self._p_nem, self._p_pe_ndf = \
            nrc.get_all_parameters(self._p_cnem, self.p_sbw, self.p_bcs,
                                   self.p_be, self.p_l, self.p_sex, self.p_a2, self.p_ph)

        self.cost_obj_vector = self.cost_vector.copy()
        for i in range(len(self.cost_vector)):
            self.cost_obj_vector[i] = \
                self.p_selling_price * nrc.swg(self.neg_vector[i], self._p_dmi, self._p_cnem,
                                               self._p_nem, self.p_sbw, self.p_linearization_factor) \
                - self.cost_vector[i] * self._p_dmi

    def __build_model(self):
        """Build model (initially based on CPLEX 12.8.1)"""
        self._diet = optimizer.Optimizer()
        self._var_names_x = ["x" + str(j) for j in range(self.n_ingredients + 1)]

        diet = self._diet
        diet.set_sense(sense="max")

        x_vars = list(diet.add_variables(obj=self.cost_obj_vector,
                                         lb=[0] * len(self.cost_vector),
                                         ub=[1] * len(self.cost_vector),
                                         names=self._var_names_x))

        "Constraint: sum(x a) == CNEm"
        diet.add_constraint(names=["CNEm GE"],
                            lin_expr=[[x_vars, ds.get_column_data(ingredients, h_ingredients.s_NEma)]],
                            rhs=[self._p_cnem * 0.999],
                            senses=["G"]
                            )
        diet.add_constraint(names=["CNEm LE"],
                            lin_expr=[[x_vars, ds.get_column_data(ingredients, h_ingredients.s_NEma)]],
                            rhs=[self._p_cnem * 1.001],
                            senses=["L"]
                            )
        "Constraint: sum(x) == 1"
        diet.add_constraint(names=["SUM 1"],
                            lin_expr=[[x_vars, [1] * len(x_vars)]],
                            rhs=[1],
                            senses=["E"]
                            )
        "Constraint: sum(x a)>= MPm"
        mpm_list = [nrc.mp(*ds.get_column_data(ds.filter_column(ingredients, h_ingredients.s_ID, val_col),
                                               [h_ingredients.s_DM,
                                                h_ingredients.s_TDN,
                                                h_ingredients.s_CP,
                                                h_ingredients.s_RUP,
                                                h_ingredients.s_Forage,
                                                h_ingredients.s_Fat]))
                    for val_col in ds.get_column_data(ingredients, h_ingredients.s_ID, int)]

        for i, v in enumerate(mpm_list):
            mpm_list[i] = v - self.neg_vector[i] * (nrc.swg_const(self._p_dmi, self._p_cnem, self._p_nem,
                                                                  self.p_sbw, self.p_linearization_factor) * 268
                                                    - self.neg_vector[i] * 29.4) * 0.001 / self._p_dmi

        diet.add_constraint(names=["MPm"],
                            lin_expr=[[x_vars, mpm_list]],
                            rhs=[self._p_mpm * 0.001 / self._p_dmi],
                            senses=["G"]
                            )

        rdp_data = [(1 - ds.get_column_data(ingredients, h_ingredients.s_RUP)[x_index])
                    * ds.get_column_data(ingredients, h_ingredients.s_CP)[x_index]
                    for x_index in range(len(x_vars))]

        "Constraint: RUP: sum(x a) >= 0.125 CNEm"
        diet.add_constraint(names=["RDP"],
                            lin_expr=[[x_vars, rdp_data]],
                            rhs=[0.125 * self._p_cnem],
                            senses=["G"]
                            )

        "Constraint: Fat: sum(x a) <= 0.06 DMI"
        diet.add_constraint(names=["Fat"],
                            lin_expr=[[x_vars, ds.get_column_data(ingredients, h_ingredients.s_Fat)]],
                            rhs=[0.06],
                            senses=["L"]
                            )

        "Constraint: peNDF: sum(x a) <= peNDF DMI"
        pendf_data = [ds.get_column_data(ingredients, h_ingredients.s_NDF)[x_index]
                      * ds.get_column_data(ingredients, h_ingredients.s_pef)[x_index]
                      for x_index in range(len(x_vars))]
        diet.add_constraint(names=["peNDF"],
                            lin_expr=[[x_vars, pendf_data]],
                            rhs=[self._p_pe_ndf],
                            senses=["G"]
                            )

        # TODO: Put constraint to limit Urea in the diet: sum(x) * DMI <= up_limit

        self.constraints_names = diet.get_constraints_names()

    def __update_model(self):
        """Update RHS values on the model based on the new CNEm and updated parameters"""
        new_rhs = {
            "CNEm GE": self._p_cnem * 0.999,
            "CNEm LE": self._p_cnem * 1.001,
            "SUM 1": 1,
            "MPm": self._p_mpm * 0.001 / self._p_dmi,
            "RDP": 0.125 * self._p_cnem,
            "Fat": 0.06,
            "peNDF": self._p_pe_ndf}

        seq_of_pairs = tuple(zip(new_rhs.keys(), new_rhs.values()))
        self._diet.set_constraint_rhs(seq_of_pairs)
        self._diet.set_objective_function(list(zip(self._var_names_x, self.cost_obj_vector)))
