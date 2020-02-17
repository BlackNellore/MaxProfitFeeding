from model import data_handler
import pandas
from model.lp_model import Model
from optimizer.numerical_methods import Searcher, Status
import logging

INPUT = {}
OUTPUT = None

ds: data_handler.Data = None

ingredients: pandas.DataFrame = None
h_ingredients: data_handler.Data.IngredientProperties = None
available_feed: pandas.DataFrame = None
h_available_feed: data_handler.Data.ScenarioFeedProperties = None
scenarios: pandas.DataFrame = None
h_scenarios: data_handler.Data.ScenarioParameters = None


def config(input_info, output_info):
    global INPUT, OUTPUT
    INPUT = input_info
    OUTPUT = output_info


class Diet:
    @staticmethod
    def run():
        logging.info("Iterating through scenarios")
        results = {}
        for scenario in scenarios.values:
            parameters = dict(zip(h_scenarios, scenario))
            logging.info("Current Scenario:")
            logging.info("{}".format(parameters))

            logging.info("Initializing model")
            model = Model(ds, parameters)
            logging.info("Initializing numerical methods")
            optimizer = Searcher(model)

            tol = parameters[h_scenarios.s_tol]
            logging.info("Refining bounds")
            lb, ub = optimizer.refine_bounds(parameters[h_scenarios.s_lb],
                                             parameters[h_scenarios.s_ub],
                                             tol
                                             )

            if lb is None or ub is None:
                logging.warning("There is no feasible solution in the domain {0} <= CNEm <= {1}"
                                .format(parameters[h_scenarios.s_lb], parameters[h_scenarios.s_ub]))
                continue
            logging.info("Refinement completed")
            logging.info("Choosing optimization method")
            if parameters[h_scenarios.s_algorithm] == "GSS":
                logging.info("Optimizing with Golden-Section Search algorithm")
                optimizer.golden_section_search(lb, ub, tol)
            elif parameters[h_scenarios.s_algorithm] == "BF":
                logging.info("Optimizing with Brute Force algorithm")
                optimizer.brute_force_search(lb, ub, tol)
            else:
                logging.error("Algorithm {} not found, scenario skipped".format(
                    parameters[h_scenarios.s_algorithm]))
                continue
            logging.info("Saving solution locally")
            status, solution = optimizer.get_results()
            if status == Status.SOLVED:
                results[parameters[h_scenarios.s_identifier]] = solution
            else:
                logging.warning("Bad Status: {0}, {1}".format(status, parameters))

        logging.info("Exporting solution to {}".format(OUTPUT))
        ds.store_output(results, OUTPUT)

        logging.info("END")

    @staticmethod
    def initialize(special_msg):
        global ds, ingredients, h_ingredients, available_feed, h_available_feed, scenarios, h_scenarios
        ds = data_handler.Data(**INPUT)

        ingredients = ds.data_feed_scenario
        h_ingredients = ds.headers_data_feed
        available_feed = ds.data_available_feed
        h_available_feed = ds.headers_available_feed
        scenarios = ds.data_scenario
        h_scenarios = ds.headers_data_scenario

        fmt_str = "%(asctime)s: %(levelname)s: %(funcName)s Line:%(lineno)d %(message)s"
        logging.basicConfig(filename="activity.log",
                            level=logging.DEBUG,
                            filemode="w",
                            format=fmt_str)
        logging.info(special_msg)
        logging.info("\n\n{}".format(ingredients))
        logging.info("\n\n")
        logging.info("\n\n{}".format(available_feed))
        logging.info("\n\n")
        logging.info("\n\n{}".format(scenarios))

        # ingredients.index = range(available_feed.last_valid_index() + 1)


if __name__ == "__main__":
    pass
