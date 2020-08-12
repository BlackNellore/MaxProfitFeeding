from model import data_handler
import pandas

from model.output_handler import Output
from model.lp_model import model_factory
from optimizer.numerical_methods import Searcher, Status, Algorithms
import logging

INPUT = {}
OUTPUT = None


class Diet:
    _output: Output = None

    ds: data_handler.Data = None

    data_scenario: pandas.DataFrame = None  # Scenario
    headers_scenario: data_handler.Data.ScenarioParameters = None  # Scenario
    data_batch: pandas.DataFrame = None  # Scenario

    @staticmethod
    def initialize(msg):
        global _output, ds, data_scenario, headers_scenario, data_batch, headers_batch
        _output = Output()
        ds = data_handler.Data(**INPUT)
        data_scenario = ds.data_scenario
        headers_scenario = ds.headers_scenario
        logging.info(msg)

    def run(self):
        logging.info("Iterating through scenarios")
        results = {}
        for scenario in data_scenario.values:

            parameters = dict(zip(headers_scenario, scenario))
            if parameters[headers_scenario.s_id] < 0:
                continue

            logging.info("Current Scenario:")
            logging.info("{}".format(parameters))

            logging.info("Initializing model")
            model = model_factory(ds, parameters)
            logging.info("Initializing numerical methods")
            optimizer = Searcher(model)

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
            lb, ub = self.refine_bounds(optimizer, parameters)
            if lb is None:
                continue
            logging.info(f'Optimizing with {msg}')
            self.__single_scenario(optimizer, parameters, lb, ub, tol)
            self.store_results(optimizer, parameters)

        _output.store()

        logging.info("END")

    @staticmethod
    def refine_bounds(optimizer, parameters, batch = False):
        logging.info("Refining bounds")
        if batch:
            optimizer.set_batch_params(0)
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

    @staticmethod
    def store_results(optimizer, parameters):
        logging.info("Saving solution locally")
        status, solution = optimizer.get_results()
        if status == Status.SOLVED:
            _output.save_as_csv(name=str(parameters[headers_scenario.s_identifier]), solution=solution)
        else:
            logging.warning("Bad Status: {0}, {1}".format(status, parameters))


def config(input_info, output_info):
    global INPUT, OUTPUT
    INPUT = input_info
    OUTPUT = output_info


if __name__ == "__main__":
    pass
