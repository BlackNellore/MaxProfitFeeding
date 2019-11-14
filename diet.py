import data_handler
from lp_model import Model
from numerical_methods import Searcher, Status
import logging

ds = data_handler.Data()

ingredients = ds.data_feed_scenario
h_ingredients = ds.headers_data_feed
available_feed = ds.data_available_feed
h_available_feed = ds.headers_available_feed
scenarios = ds.data_cattle
h_scenarios = ds.headers_data_cattle

output_file = "Output.xlsx"


def run_stuff():
    logging.info("Iterating through scenarios")
    results = {}
    for scenario in scenarios.get_values():
        parameters = dict(zip(h_scenarios, scenario))
        logging.info("Current Scenario:")
        logging.info("{}".format(parameters))

        logging.info("Initializing model")
        model = Model(parameters)
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

    logging.info("Exporting solution to {}".format(output_file))
    ds.store_output(results, output_file)

    logging.info("END")


if __name__ == "__main__":
    fmt_str = "%(asctime)s: %(levelname)s: %(funcName)s Line:%(lineno)d %(message)s"
    logging.basicConfig(filename="activity.log",
                        level=logging.DEBUG,
                        filemode="w",
                        format=fmt_str)
    logging.info("Starting diet.py")
    logging.info("\n\n{}".format(ingredients))
    logging.info("\n\n")
    logging.info("\n\n{}".format(available_feed))
    logging.info("\n\n")
    logging.info("\n\n{}".format(scenarios))

    ingredients.index = range(available_feed.last_valid_index() + 1)

    run_stuff()
