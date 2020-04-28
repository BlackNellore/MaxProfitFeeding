from model import data_handler
import pandas
from model.lp_model import model_factory
from optimizer.numerical_methods import Searcher, Status, Algorithms
import logging

INPUT = {}
OUTPUT = None

class Diet:
    ds: data_handler.Data = None

    data_scenario: pandas.DataFrame = None  # Scenario
    headers_scenario: data_handler.Data.ScenarioParameters = None  # Scenario
    data_batch: pandas.DataFrame = None  # Scenario
    headers_batch: data_handler.Data.BatchParameters = None  # Scenario

    @staticmethod
    def initialize(msg):
        global ds, data_scenario, headers_scenario, data_batch, headers_batch
        ds = data_handler.Data(**INPUT)
        data_scenario = ds.data_scenario
        headers_scenario = ds.headers_scenario
        data_batch = ds.data_batch
        headers_batch = ds.headers_batch
        logging.info(msg)

    def run(self):
        logging.info("Iterating through scenarios")
        results = {}
        for scenario in data_scenario.values:
            parameters = dict(zip(headers_scenario, scenario))
            batch = False
            if parameters[headers_scenario.s_batch] > 0:
                batch = True

            logging.info("Current Scenario:")
            logging.info("{}".format(parameters))

            logging.info("Initializing model")
            model = model_factory(ds, parameters)
            logging.info("Initializing numerical methods")
            optimizer = Searcher(model, batch)

            # TODO Implement Sensitivity Analysis: sensitivity.py

            if parameters[headers_scenario.s_algorithm] == "GSS":
                msg = "Golden-Section Search algorithm"
            elif parameters[headers_scenario.s_algorithm] == "BF":
                msg = "Brute Force algorithm"
            else:
                logging.error("Algorithm {} not found, scenario skipped".format(
                    parameters[headers_scenario.s_algorithm]))
                continue

            tol = parameters[headers_scenario.s_tol]
            lb = parameters[headers_scenario.s_lb]
            ub = parameters[headers_scenario.s_ub]
            if not batch:
                lb, ub = self.refine_bounds(optimizer, parameters)
                if lb is None:
                    continue
                logging.info(f'Optimizing with {msg}')
                self.__single_scenario(optimizer, parameters, lb, ub, tol)
            else:
                logging.info(f"Optimizing with multiobjective epsilon-constrained based on {msg}")
                self.__multi_scenario(optimizer, parameters, lb, ub, tol)

            logging.info("Saving solution locally")
            status, solution = optimizer.get_results()
            if status == Status.SOLVED:
                results[parameters[headers_scenario.s_identifier]] = solution
            else:
                logging.warning("Bad Status: {0}, {1}".format(status, parameters))

        logging.info("Exporting solution to {}".format(OUTPUT))
        ds.store_output(results, OUTPUT)

        logging.info("END")

    @staticmethod
    def refine_bounds(optimizer, parameters):
        logging.info("Refining bounds")
        lb, ub = optimizer.refine_bounds(parameters[headers_scenario.s_lb],
                                         parameters[headers_scenario.s_ub],
                                         parameters[headers_scenario.s_tol]
                                         )

        if lb is None or ub is None:
            logging.warning("There is no feasible solution in the domain {0} <= CNEm <= {1}"
                            .format(parameters[headers_scenario.s_lb], parameters[headers_scenario.s_ub]))
            return None, None
        logging.info("Refinement completed")
        logging.info("Choosing optimization method")
        return lb, ub

    @staticmethod
    def __single_scenario(optimizer, parameters, lb, ub, tol):
        algorithm = Algorithms[parameters[headers_scenario.s_algorithm]]
        optimizer.run_scenario(algorithm, lb, ub, tol)

    def __multi_scenario(self, optimizer, parameters, lb, ub, tol):
        optimizer.clear_searcher(force=True)
        algorithm = Algorithms[parameters[headers_scenario.s_algorithm]]
        batch_id = parameters[headers_scenario.s_batch]
        batch_parameters = ds.filter_column(data_batch, headers_batch.s_batch_id, batch_id, int64=True)

        # batch_space = range(list(batch_parameters[headers_batch.s_initial_period])[0],
        #                     list(batch_parameters[headers_batch.s_final_period])[0],
        #                     1)
        batch_space = range(list(batch_parameters[headers_batch.s_final_period])[0] -
                            list(batch_parameters[headers_batch.s_initial_period])[0] + 1)
        for i in batch_space:
            optimizer.set_batch_params(i)
            self.__single_scenario(optimizer, parameters, lb, ub, tol)


def config(input_info, output_info):
    global INPUT, OUTPUT
    INPUT = input_info
    OUTPUT = output_info


if __name__ == "__main__":
    pass
