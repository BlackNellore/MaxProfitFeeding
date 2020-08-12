import csv
import logging
import os, os.path
import shutil
from datetime import datetime


class Output:
    temp_dir = "model/temp_output/"

    def __init__(self):

        if not os.path.exists(self.temp_dir):
            os.mkdir(self.temp_dir)


        self.delete_all_files_in(self.temp_dir)
        pass

    @staticmethod
    def delete_all_files_in(directory):
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        for f in files:
            os.remove(directory + f)

    def store(self):

        # create a new folder in /Output/ and name it YYYY_MM_DD_HHMMSS
        dirName = './Output/'

        if not os.path.exists(dirName):
            os.mkdir(dirName)

        now = datetime.now()
        now = now.strftime("%Y_%m_%d_%H%M%S")
        dirName = dirName + now

        try:
            os.mkdir(dirName)
        except FileExistsError:
            print("Directory ", dirName, " already exists.")

        # copy input
        shutil.copy('./Input.xlsx', dirName)

        files = [f for f in os.listdir(self.temp_dir) if os.path.isfile(os.path.join(self.temp_dir, f))]

        # move all csv files from temp_output to the new folder
        for f in files:
            os.rename(self.temp_dir + f, dirName + "/" + f)

    def save_as_csv(self, name="", solution=[]):
        """Save solution as a csv file"""
        keys = list(solution[0].keys())
        values = []
        for line in solution:
            values.append(list(line.values()))

        path = self.temp_dir + name + ".csv"

        with open(path, "a+", newline='', encoding='utf-16') as file:
            writer = csv.writer(file)
            file.seek(0)
            first_line = file.readline()
            if len(first_line) == 0:
                writer.writerow(keys)
            for line in values:
                writer.writerow(line)
        return 0

    # deprecated
    # def store_output(self, filename="output.xlsx"):
    #    # open temp output and load all files to results_dict
    #    results_dict = {}
    #    for name in self.temp_names:
    #        solution = []
    #        with open('model/output_temp/' + name + '.csv', newline='', encoding='utf-16') as file:
    #            reader = csv.DictReader(file)
    #            for line in reader:
    #                solution.append(line)
    #        results_dict[name] = solution
    #    # write final output
    #    writer = pandas.ExcelWriter(filename)
    #    if len(results_dict) == 0:
    #        logging.warning("NO SOLUTION FOUND, NOTHING TO BE SAVED")
    #        return
    #    for sheet_name in results_dict.keys():
    #        results = results_dict[sheet_name]
    #        if results is None or len(results) == 0:
    #            break
    #        df = pandas.DataFrame(results)
    #        df.to_excel(writer, sheet_name=sheet_name, columns=[*results[0].keys()])
    #    writer.save()


if __name__ == "__main__":

    if not os.path.exists("../Output"):
        os.makedirs("../Output")

    pass
