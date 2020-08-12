""" Mathematical model """
from optimizer import optimizer
import pandas
from model import data_handler
from model.nrc_equations import NRC_eq as nrc
import logging
import math

cnem_lb, cnem_ub = 0.8, 3

bigM = 100000


def model_factory(ds, parameters):
    return Model(ds, parameters)


class Model:
    ds: data_handler.Data = None
    headers_feed_lib: data_handler.Data.IngredientProperties = None  # Feed Library
    data_feed_lib: pandas.DataFrame = None  # Feed Library
    data_feed_scenario: pandas.DataFrame = None  # Feeds
    headers_feed_scenario: data_handler.Data.ScenarioFeedProperties = None  # Feeds
    data_scenario: pandas.DataFrame = None  # Scenario
    headers_scenario: data_handler.Data.ScenarioParameters = None  # Scenario

    p_id, p_feed_scenario, p_breed, p_sbw, p_feed_time, p_target_weight, \
    p_bcs, p_be, p_l, p_sex, p_a2, p_ph, p_selling_price, \
    p_algorithm, p_identifier, p_lb, p_ub, p_tol, p_dmi_eq, p_obj = [None for i in range(20)]

    _diet = None
    _p_mpm = None
    _p_dmi = None
    _p_nem = None
    _p_neg = None
    _p_pe_ndf = None
    _p_cnem = None
    _p_cneg = None
    _var_names_x = None
    _p_swg = None
    _model_feeding_time = None
    _model_final_weight = None

    _print_model_lp = False
    _print_model_lp_infeasible = False
    _print_solution_xml = False

    opt_sol = None
    prefix_id = ""

    def __init__(self, out_ds, parameters):
        self._cast_data(out_ds, parameters)

    @staticmethod
    def _remove_inf(vector):
        for i in range(len(vector)):
            if vector[i] == float("-inf"):
                vector[i] = -bigM
            elif vector[i] == float("inf"):
                vector[i] = bigM

    def run(self, p_id, p_cnem):
        """Either build or update model, solve ir and return solution = {dict xor None}"""
        logging.info("Populating and running model")
        try:
            self.opt_sol = None
            self._p_cnem = p_cnem
            if not self._compute_parameters(p_id):
                self._infeasible_output(p_id)
                return None
            if self._diet is None:
                self._build_model()
            else:
                self._update_model()
            return self._solve(p_id)
        except Exception as e:
            logging.error("An error occurred in lp_model.py L86:\n{}".format(str(e)))
            return None

    def _get_params(self, p_swg):
        if p_swg is None:
            return dict(zip(["CNEm", "CNEg", "NEm", "NEg", "DMI", "MPm",  "peNDF"],
                            [self._p_cnem, self._p_cneg, self._p_nem, self._p_neg,
                             self._p_dmi, self._p_mpm * 0.001, self._p_pe_ndf]))
        else:
            return dict(zip(["CNEm", "CNEg", "NEm", "NEg", "SWG", "DMI", "MPm",  "peNDF"],
                            [self._p_cnem, self._p_cneg, self._p_nem, self._p_neg, p_swg,
                             self._p_dmi, self._p_mpm * 0.001, self._p_pe_ndf]))

    def _solve(self, problem_id):
        """Return None if solution is infeasible or Solution dict otherwise"""
        diet = self._diet
        # diet.write_lp(name="CNEm_{}.lp".format(str(self._p_cnem)))
        diet.solve()
        status = diet.get_solution_status()
        logging.info("Solution status: {}".format(status))
        if status.__contains__("infeasible"):
            self._infeasible_output(problem_id)
            return None

        sol_id = {"Problem_ID": problem_id,
                  "Feeding Time": self._model_feeding_time,
                  "Initial weight": self.p_sbw,
                  "Final weight": self._model_final_weight}
        sol = dict(zip(diet.get_variable_names(), diet.get_solution_vec()))
        sol["obj_func"] = diet.get_solution_obj()
        sol["obj_cost"] = 0
        sol["obj_revenue"] = self.revenue
        for i in range(len(self._var_names_x)):
            sol["obj_cost"] += diet.get_solution_vec()[i] * self.expenditure_obj_vector[i]

        params = self._get_params(self._p_swg)
        sol_activity = dict(zip(["{}_act".format(constraint) for constraint in self.constraints_names],
                                diet.get_solution_activity_levels(self.constraints_names)))
        sol_rhs = dict(zip(["{}_rhs".format(constraint) for constraint in self.constraints_names],
                           diet.get_constraints_rhs(self.constraints_names)))
        sol_red_cost = dict(zip(["{}_red_cost".format(var) for var in diet.get_variable_names()],
                                diet.get_dual_reduced_costs())) #get dual values
        sol_dual = dict(zip(["{}_dual".format(const) for const in diet.get_constraints_names()],
                            diet.get_dual_values())) # get dual reduced costs
        sol_slack = dict(zip(["{}_slack".format(const) for const in diet.get_constraints_names()],
                             diet.get_dual_linear_slacks()))
        sol = {**sol_id, **params, **sol, **sol_rhs, **sol_activity,
               **sol, **sol_dual, **sol_red_cost, **sol_slack}
        self.opt_sol = diet.get_solution_obj()

        return sol

    def _infeasible_output(self, problem_id):
        sol_id = {"Problem_ID": self.prefix_id + str(problem_id)}
        params = self._get_params(p_swg=None)
        sol = {**sol_id, **params}
        self.opt_sol = None
        # diet.write_lp(f"lp_infeasible_{str(problem_id)}.lp")
        logging.warning("Infeasible parameters:{}".format(sol))

    # Parameters filled by inner method ._cast_data()
    n_ingredients = None
    cost_vector = None
    cost_obj_vector = None
    constraints_names = None
    # revenue_obj_vector = None
    revenue = None
    expenditure_obj_vector = None
    dm_af_coversion = None
    cst_obj = None
    scenario_parameters = None

    def __set_parameters(self, parameters):
        if isinstance(parameters, dict):
            [self.p_id, self.p_feed_scenario, self.p_breed, self.p_sbw, self.p_feed_time,
             self.p_target_weight,self.p_bcs, self.p_be, self.p_l,
             self.p_sex, self.p_a2, self.p_ph, self.p_selling_price,
             self.p_algorithm, self.p_identifier, self.p_lb, self.p_ub, self.p_tol, self.p_dmi_eq, self.p_obj] = parameters.values()
        elif isinstance(parameters, list):
            [self.p_id, self.p_feed_scenario, self.p_breed, self.p_sbw, self.p_feed_time,
             self.p_target_weight,self.p_bcs, self.p_be, self.p_l,
             self.p_sex, self.p_a2, self.p_ph, self.p_selling_price,
             self.p_algorithm, self.p_identifier, self.p_lb, self.p_ub, self.p_tol, self.p_obj] = parameters

    def _cast_data(self, out_ds, parameters):
        """Retrieve parameters data from table. See data_handler.py for more"""
        self.ds = out_ds

        self.data_feed_scenario = self.ds.data_feed_scenario
        self.headers_feed_scenario = self.ds.headers_feed_scenario

        self.scenario_parameters = parameters
        self.__set_parameters(parameters)

        headers_feed_scenario = self.ds.headers_feed_scenario
        self.data_feed_scenario = self.ds.filter_column(self.ds.data_feed_scenario,
                                                        self.ds.headers_feed_scenario.s_feed_scenario,
                                                        self.p_feed_scenario)
        self.data_feed_scenario = self.ds.sort_df(self.data_feed_scenario, self.headers_feed_scenario.s_ID)

        self.ingredient_ids = list(
            self.ds.get_column_data(self.data_feed_scenario, self.headers_feed_scenario.s_ID, int))

        self.headers_feed_lib = self.ds.headers_feed_lib
        self.data_feed_lib = self.ds.filter_column(self.ds.data_feed_lib, self.headers_feed_lib.s_ID,
                                                   self.ingredient_ids)

        self.cost_vector = self.ds.sorted_column(self.data_feed_scenario, self.headers_feed_scenario.s_feed_cost,
                                                 self.ingredient_ids,
                                                 self.headers_feed_scenario.s_ID)
        self.n_ingredients = self.data_feed_scenario.shape[0]
        self.cost_vector = self.ds.sorted_column(self.data_feed_scenario, headers_feed_scenario.s_feed_cost,
                                                 self.ingredient_ids,
                                                 self.headers_feed_scenario.s_ID)
        self.dm_af_coversion = self.ds.sorted_column(self.data_feed_lib, self.headers_feed_lib.s_DM,
                                                self.ingredient_ids,
                                                self.headers_feed_lib.s_ID)
#         for i in range(len(self.cost_vector)):
#             self.cost_vector[i] /= self.dm_af_coversion[i]

    def _compute_parameters(self, problem_id):

        """Compute parameters variable with CNEm"""
        self._p_mpm, self._p_dmi, self._p_nem, self._p_pe_ndf = \
            nrc.get_all_parameters(self._p_cnem, self.p_sbw, self.p_bcs,
                                   self.p_be, self.p_l, self.p_sex, self.p_a2, self.p_ph, self.p_target_weight, self.p_dmi_eq)

        self._p_cneg = nrc.cneg(self._p_cnem)
        self._p_neg = nrc.neg(self._p_cneg, self._p_dmi, self._p_cnem, self._p_nem)
        if self._p_neg is None:
            return False
        # self._p_swg = nrc.swg(self._p_neg, self.p_sbw, self.p_target_weight)
        if math.isnan(self.p_feed_time) or self.p_feed_time == 0:
            self._model_final_weight = self.p_target_weight
            self._p_swg = nrc.swg(self._p_neg, self.p_sbw, self._model_final_weight)
            self._model_feeding_time = (self.p_target_weight - self.p_sbw)/self._p_swg
        elif math.isnan(self.p_target_weight) or self.p_target_weight == 0:
            self._model_feeding_time = self.p_feed_time
            self._p_swg = nrc.swg_time(self._p_neg, self.p_sbw, self._model_feeding_time)
            self._model_final_weight = self._model_feeding_time * self._p_swg + self.p_sbw
        else:
            raise Exception("target weight and feeding time cannot be defined at the same time")

        self.cost_obj_vector = self.cost_vector.copy()
        for i in range(len(self.cost_obj_vector)):
            self.cost_obj_vector[i] /= self.dm_af_coversion[i]
            
        self.revenue = self.p_selling_price * (self.p_sbw + self._p_swg * self._model_feeding_time)
        # self.revenue_obj_vector = self.cost_vector.copy()
        self.expenditure_obj_vector = self.cost_vector.copy()
        for i in range(len(self.cost_vector)):
            # self.revenue_obj_vector[i] = self.p_selling_price * (self.p_sbw + self._p_swg * self._model_feeding_time)
            self.expenditure_obj_vector[i] = self.cost_vector[i] * self._p_dmi * self._model_feeding_time
        # r = [self.revenue_obj_vector[i] - self.expenditure_obj_vector[i] for i in range(len(self.revenue_obj_vector))]
        if self.p_obj == "MaxProfit":
            for i in range(len(self.cost_vector)):
                self.cost_obj_vector[i] = - self.expenditure_obj_vector[i]
            self.cst_obj = self.revenue
        elif self.p_obj == "MinCost":
            for i in range(len(self.cost_vector)):
                self.cost_obj_vector[i] = - self.expenditure_obj_vector[i]
            self.cst_obj = 0
        elif self.p_obj == "MaxProfitSWG":
            for i in range(len(self.cost_vector)):
                self.cost_obj_vector[i] = -(self.expenditure_obj_vector[i])/self._p_swg
            self.cst_obj = self.revenue/self._p_swg
        elif self.p_obj == "MinCostSWG":
            for i in range(len(self.cost_vector)):
                self.cost_obj_vector[i] = -(self.expenditure_obj_vector[i])/self._p_swg
            self.cst_obj = 0

#         self.cost_obj_vector_mono = self.cost_obj_vector.copy()
        return True

    def _build_model(self):
        """Build model (initially based on CPLEX 12.8.1)"""
        self._diet = optimizer.Optimizer()
        self._var_names_x = ["x" + str(f_id)
                             for f_id in self.ingredient_ids]

        diet = self._diet
        diet.set_sense(sense="max")

        self._remove_inf(self.cost_obj_vector)

        x_vars = list(diet.add_variables(obj=self.cost_obj_vector,
                                         lb=self.ds.sorted_column(self.data_feed_scenario,
                                                                  self.headers_feed_scenario.s_min,
                                                                  self.ingredient_ids,
                                                                  self.headers_feed_scenario.s_ID),
                                         ub=self.ds.sorted_column(self.data_feed_scenario,
                                                                  self.headers_feed_scenario.s_max,
                                                                  self.ingredient_ids,
                                                                  self.headers_feed_scenario.s_ID),
                                         names=self._var_names_x))
        diet.set_obj_offset(self.cst_obj)

        "Constraint: sum(x a) == CNEm"
        diet.add_constraint(names=["CNEm GE"],
                            lin_expr=[[x_vars, self.ds.sorted_column(self.data_feed_lib,
                                                                     self.headers_feed_lib.s_NEma,
                                                                     self.ingredient_ids,
                                                                     self.headers_feed_lib.s_ID)]],
                            rhs=[self._p_cnem * 0.999],
                            senses=["G"]
                            )
        diet.add_constraint(names=["CNEm LE"],
                            lin_expr=[[x_vars, self.ds.sorted_column(self.data_feed_lib,
                                                                     self.headers_feed_lib.s_NEma,
                                                                     self.ingredient_ids,
                                                                     self.headers_feed_lib.s_ID)]],
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
        mp_properties = self.ds.sorted_column(self.data_feed_lib,
                                              [self.headers_feed_lib.s_DM,
                                               self.headers_feed_lib.s_TDN,
                                               self.headers_feed_lib.s_CP,
                                               self.headers_feed_lib.s_RUP,
                                               self.headers_feed_lib.s_Forage,
                                               self.headers_feed_lib.s_Fat],
                                              self.ingredient_ids,
                                              self.headers_feed_lib.s_ID)
        mpm_list = [nrc.mp(*row) for row in mp_properties]

        # for i, v in enumerate(mpm_list):
        #     mpm_list[i] = v - (self._p_swg * 268 - self._p_neg * 29.4) * 0.001 / self._p_dmi

        diet.add_constraint(names=["MPm"],
                            lin_expr=[[x_vars, mpm_list]],
                            rhs=[(self._p_mpm + 268 * self._p_swg - 29.4 * self._p_neg)* 0.001 / self._p_dmi],
                            senses=["G"]
                            )

        rdp_data = [(1 - self.ds.sorted_column(self.data_feed_lib,
                                               self.headers_feed_lib.s_RUP,
                                               self.ingredient_ids,
                                               self.headers_feed_lib.s_ID)[x_index])
                    * self.ds.sorted_column(self.data_feed_lib,
                                            self.headers_feed_lib.s_CP,
                                            self.ingredient_ids,
                                            self.headers_feed_lib.s_ID)[x_index]
                    for x_index in range(len(x_vars))]

        "Constraint: RUP: sum(x a) >= 0.125 CNEm"
        diet.add_constraint(names=["RDP"],
                            lin_expr=[[x_vars, rdp_data]],
                            rhs=[0.125 * self._p_cnem],
                            senses=["G"]
                            )

        "Constraint: Fat: sum(x a) <= 0.06 DMI"
        diet.add_constraint(names=["Fat"],
                            lin_expr=[[x_vars, self.ds.sorted_column(self.data_feed_lib,
                                                                     self.headers_feed_lib.s_Fat,
                                                                     self.ingredient_ids,
                                                                     self.headers_feed_lib.s_ID)]],
                            rhs=[0.06],
                            senses=["L"]
                            )

        "Constraint: peNDF: sum(x a) <= peNDF DMI"
        pendf_data = [self.ds.sorted_column(self.data_feed_lib,
                                            self.headers_feed_lib.s_NDF,
                                            self.ingredient_ids,
                                            self.headers_feed_lib.s_ID)[x_index]
                      * self.ds.sorted_column(self.data_feed_lib,
                                              self.headers_feed_lib.s_pef,
                                              self.ingredient_ids,
                                              self.headers_feed_lib.s_ID)[x_index]
                      for x_index in range(len(x_vars))]
        diet.add_constraint(names=["peNDF"],
                            lin_expr=[[x_vars, pendf_data]],
                            rhs=[self._p_pe_ndf],
                            senses=["G"]
                            )

        self.constraints_names = diet.get_constraints_names()
        # diet.write_lp(name="file.lp")
        pass

    def _update_model(self):
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

        self._diet.set_objective_function(list(zip(self._var_names_x, self.cost_obj_vector)), self.cst_obj)
