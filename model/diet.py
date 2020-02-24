from model import data_handler
import pandas
from model.lp_model import model_factory
from optimizer.numerical_methods import Searcher, Status
import logging

INPUT = {}
OUTPUT = None

class Diet:
    ds: data_handler.Data = None

    data_scenario: pandas.DataFrame = None  # Scenario
    headers_scenario: data_handler.Data.ScenarioParameters = None  # Scenario

    @staticmethod
    def initialize(msg):
        global ds, data_scenario, headers_scenario
        ds = data_handler.Data(**INPUT)
        data_scenario = ds.data_scenario
        headers_scenario = ds.headers_scenario
        logging.info(msg)

    @staticmethod
    def run():
        logging.info("Iterating through scenarios")
        results = {}
        for scenario in data_scenario.values:
            parameters = dict(zip(headers_scenario, scenario))

            logging.info("Current Scenario:")
            logging.info("{}".format(parameters))

            logging.info("Initializing model")
            model = model_factory(ds, parameters)
            logging.info("Initializing numerical methods")
            optimizer = Searcher(model)

            tol = parameters[headers_scenario.s_tol]
            logging.info("Refining bounds")
            lb, ub = optimizer.refine_bounds(parameters[headers_scenario.s_lb],
                                             parameters[headers_scenario.s_ub],
                                             tol
                                             )

            if lb is None or ub is None:
                logging.warning("There is no feasible solution in the domain {0} <= CNEm <= {1}"
                                .format(parameters[headers_scenario.s_lb], parameters[headers_scenario.s_ub]))
                continue
            logging.info("Refinement completed")
            logging.info("Choosing optimization method")

            if parameters[headers_scenario.s_algorithm] == "GSS":
                logging.info("Optimizing with Golden-Section Search algorithm")
                optimizer.golden_section_search(lb, ub, tol)
            elif parameters[headers_scenario.s_algorithm] == "BF":
                logging.info("Optimizing with Brute Force algorithm")
                optimizer.brute_force_search(lb, ub, tol)
            else:
                logging.error("Algorithm {} not found, scenario skipped".format(
                    parameters[headers_scenario.s_algorithm]))
                continue

            logging.info("Saving solution locally")
            status, solution = optimizer.get_results()
            if status == Status.SOLVED:
                results[parameters[headers_scenario.s_identifier]] = solution
            else:
                logging.warning("Bad Status: {0}, {1}".format(status, parameters))

        logging.info("Exporting solution to {}".format(OUTPUT))
        ds.store_output(results, OUTPUT)

        logging.info("END")


def config(input_info, output_info):
    global INPUT, OUTPUT
    INPUT = input_info
    OUTPUT = output_info


if __name__ == "__main__":
    pass
