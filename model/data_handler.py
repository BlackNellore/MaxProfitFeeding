from typing import NamedTuple
import pandas
import logging


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


def mask(df, key, value):
    """ Defines mask to filter row elements in panda's DataFrame """
    if type(value) is int:
        return df[df[key] == value]
    if type(value) is list:
        return df[df[key].isin(value)]


def unwrap_list(nested_list):
    new_list = []
    for sublist in nested_list:
        for item in sublist:
            new_list.append(item)
    return new_list


class Data:
    pandas.DataFrame.mask = mask

    # Sheet Cattle
    class ScenarioParameters(NamedTuple):
        s_id: str
        s_feed_scenario: str
        s_breed: str
        s_sbw: str
        s_bcs: str
        s_be: str
        s_l: str
        s_sex: str
        s_a2: str
        s_ph: str
        s_price: str
        s_linear_factor: str
        s_algorithm: str
        s_identifier: str
        s_lb: str
        s_ub: str
        s_tol: str
        s_obj: str

    # Sheet Feeds
    class ScenarioFeedProperties(NamedTuple):
        s_feed_scenario: str
        s_ID: str
        s_min: str
        s_max: str
        s_feed_cost: str
        s_name: str

    # Sheet FeedLibrary
    class IngredientProperties(NamedTuple):
        s_ID: str
        s_FEED: str
        s_Cost: str
        s_IFN: str
        s_Forage: str
        s_DM: str
        s_CP: str
        s_SP: str
        s_ADICP: str
        s_Sugars: str
        s_OA: str
        s_Fat: str
        s_Ash: str
        s_Starch: str
        s_NDF: str
        s_Lignin: str
        s_TDN: str
        s_ME: str
        s_NEma: str
        s_NEga: str
        s_RUP: str
        s_kd_PB: str
        s_kd_CB1: str
        s_kd_CB2: str
        s_kd_CB3: str
        s_PBID: str
        s_CB1ID: str
        s_CB2ID: str
        s_pef: str
        s_ARG: str
        s_HIS: str
        s_ILE: str
        s_LEU: str
        s_LYS: str
        s_MET: str
        s_CYS: str
        s_PHE: str
        s_TYR: str
        s_THR: str
        s_TRP: str
        s_VAL: str
        s_Ca: str
        s_P: str
        s_Mg: str
        s_Cl: str
        s_K: str
        s_Na: str
        s_S: str
        s_Co: str
        s_Cu: str
        s_I: str
        s_Fe: str
        s_Mn: str
        s_Se: str
        s_Zn: str
        s_Vit_A: str
        s_Vit_D: str
        s_Vit_E: str

    def __init__(self,
                 filename,
                 sheet_feed,
                 sheet_scenario,
                 sheet_cattle):
        """
        Read excel file
        I know, I know, shouldn't be hardcoded, one day I will fix that
        """
        excel_file = pandas.ExcelFile(filename)

        # FeedLibrary
        data_feed = pandas.read_excel(excel_file, sheet_feed)
        self.headers_data_feed = self.IngredientProperties(*(list(data_feed)))

        # Feeds scenarios
        self.data_available_feed = pandas.read_excel(excel_file, sheet_scenario)
        self.headers_available_feed = self.ScenarioFeedProperties(*(list(self.data_available_feed)))

        # Filters feed library with the feeds on the scenario
        filter_ingredients_ids = \
            self.data_available_feed.filter(items=[self.headers_available_feed.s_ID]).values
        self.data_feed_scenario = self.filter_column(data_feed,
                                                     self.headers_data_feed.s_ID,
                                                     unwrap_list(filter_ingredients_ids))

        # TODO Check if all ingridients exist in the library.

        # Sheet Scenario
        self.data_scenario = pandas.read_excel(excel_file, sheet_cattle)
        self.headers_data_scenario = self.ScenarioParameters(*(list(self.data_scenario)))

    @staticmethod
    def filter_column(data_frame, col_name, val):
        """ Filter elements in data_frame where col_name == val or in [val]"""
        return data_frame.mask(col_name, val)

    @staticmethod
    def get_column_data(data_frame, col_name, func=None):
        """ Get all elements of a certain column"""
        if not isinstance(col_name, list):
            ds = data_frame.filter(items=[col_name]).values
            if func is None:
                resulting_list = [i for i in unwrap_list(ds)]
            else:
                resulting_list = [func(i) for i in unwrap_list(ds)]
            if "%" in col_name:
                resulting_list = [i*0.01 for i in unwrap_list(ds)]
            if len(resulting_list) == 1:
                return resulting_list[0]
            else:
                return resulting_list
        else:
            ds = data_frame.filter(items=col_name).get_values()
            return unwrap_list(ds)

    @staticmethod
    def map_values(headers, vals):
        """Map all column values in a dic based on the parsed header"""
        return dict(zip(list(headers), list(vals)))

    @staticmethod
    def match_by_column(data_frame1, data_frame2, col_name):
        """Return intersection of df1 with df2 filtered by column elements"""
        elements = data_frame2.filter(items=[col_name]).get_values()
        ds = data_frame1.mask(col_name, unwrap_list(elements))
        return ds

    @staticmethod
    def store_output(results_dict, filename="output.xlsx"):
        writer = pandas.ExcelWriter(filename)
        if len(results_dict) == 0:
            logging.warning("NO SOLUTION FOUND, NOTHING TO BE SAVED")
            return
        for sheet_name in results_dict.keys():
            results = results_dict[sheet_name]
            if results is None or len(results) == 0:
                break
            df = pandas.DataFrame(results)
            df.to_excel(writer, sheet_name=sheet_name, columns=[*results[0].keys()])
        writer.save()


if __name__ == "__main__":
    print("hello data_handler")
    test_ds = Data(filename="Input.xlsx",
                   sheet_feed="FeedLibrary",
                   sheet_scenario="Feeds",
                   sheet_cattle="Scenario"
                   )
