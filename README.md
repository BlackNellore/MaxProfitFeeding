# MaxProfitFeeding v1.2 - README under construction
Diet optimization model for beef cattle based on "Nutritional Requirements for Beef Cattle" 8th Ed. (NASEM, 2016).
This is an updated version of the work published in the Animal Journal: **An improved algorithm for solving
profit-maximizing cattle diet problems**, [DOI: 10.1017/S1751731120001433](https://doi.org/10.1017/S1751731120001433)

This model requires only the available feedstuff and animal's characteristics to compute a maximum profit diet either
 for a fixed feeding time or for a target weight.
We use feedtuff properties from NASEM (2016). This work is based on a theoretical framework and in no way replace an
 appropriate nutritional analysis.
Thus, we do not hold any responsibility for applications of this work in livestock.
Always consult a veterinary before changing the feed composition for your herd.

This model is part of a PhD project at the University of Edinburgh and a thematic project funded by FAPESP.
If you refeer to this code, cite as: 

**Marques, J., Silva, R., Barioni, L., Hall, J., Tedeschi, L., & Moran, D. (2020). An improved algorithm for solving profit-maximizing cattle diet problems. Animal, 1-10. [doi:10.1017/S1751731120001433](https://doi.org/10.1017/S1751731120001433)**


#### References
FAPESP project Title: "Sugarcane - Livestock Integration: Modeling and Optimization", FAPESP Project Number:
  2017/11523-5

NASEM - National Academies of Sciences, Engineering, and Medicine 2016. Nutrient Requirements of Beef Cattle,
 8th Revised Edition. National Academies Press, Washington, D.C.


## Getting Started
**TLDR:**
```
>pip3 install -r requirements
>python run.py
```
* Input in **"./input.xlsx"**
* Ouput in **"./output.xlsx"**
* Log in **"./activity.log"**
* Settings in **"./config.py"**

### Prerequisites and Setup
**If you are trying to run on Linux or MacOS scroll down to last item: it won't run.**

This python project requires some libraries. They should be automatically installed if you execute with
 administrative rights:
```
>pip3 install -r requirements
```
List of libraries installed:
* xlrd
* openpyxl
* aenum
* numpy
* pandas
* scipy

NOTE: Linear programming solver [HiGHS](https://highs.dev) distributed along.


### Basic Run
1. Adjust your input in the file **"./input.xlsx"**: 
    1. Sheet "Feeds": Choose the available feeds setting the ID, it will automatically retrieve the name from sheet
     "FeedLibrary" (NASEM, 2016).
    Set minimum and maximum concentration allowed (between 0 and 1), and feed cost \[US$/kg\].
    The column "Feed Scenario" aggregates all feedstuff that belong to a particular scenario.
    This index will be matched with the one in the sheet "Scenario"
    2. Sheet "Scenario":
        * ID: Scenario ID \[int\]
        * Feed Scenario: Define which feed scenario should be match in the sheet "Feeds" \[int\]
        * Breed: Breed Name (does not affect result)
        * SBW: Shrunk Bodyweight \[100; 800\]
        * BCS: Body Condition Score \[0; 9\]
        * BE: Breed Factor (check NASEM 2016, pg355 Table 19-1)
        * L: Lactation Factor {1, 1.2}
        * SEX: {1, 1.15}
        * a2: 0 if not considering acclimatization factor, check NASEM (2016) otherwise
        * PH: Rumen desired pH
        * Selling Price: Cattle Selling Price per \[U$/kg\]
        * Linearization factor: an coefficient to adjust nonlinear SWG by a line. 
        * Algorithm: BF - Brute Force; GSS - Golden Section Search
        * Identifier: String to name sheets when writing results
        * LB: Concentration of Net Energy for Maintenance (CNEm) \[Mcal/kg\] lower bound (suggestion: 0.8)
        * UB: Concentration of Net Energy for Maintenance (CNEm) \[Mcal/kg\] upper bound (suggestion: 3.0)
        * Tol: Result tolerance (suggested: 0.01)
        * Obj: MaxProfit (maximizes profit), MinCost (minimizes cost), or MaxProfitSWG (maximize profit/shrunk weight
         gain)
2. Run:
    ```
    >python run.py
    ```
3. Results: if everything is alright, you can check your solution on **"./output.xlsx"**. Otherwise, you can check the 
**"./activity.log"** to see if any errors happened.

### Batch Run
1. The table 'Batch' takes 5 inputs:
    * Batch ID: ID to be crossed with table 'Scenario'
    * Filename: path + filename of CSV file with batch info
    * Period col: name of the col that contains the IDs of each running
    * Initial period: p<sub>i</sub>  such as 'Period col' &ge; p<sub>i</sub>
    * Final period: p<sub>f</sub>  such as 'Period col' &le; p<sub>f</sub>
2. Example CSV file 'test.csv':

    | row_ids   | DDGS_01      | Animal_price   | ...   | variable_m    |
    | ----------|:-------------:|:-------------:| :----:|:-------------:|
    | 1         | 0.86          | 5.43          | ...   | 17.4          |
    | 2         | 1.23          | 3.45          | ...   | 13.2          |
    | ...       |...            | ...           | ...   | ...           |
    | n         | 2.26          | 4.25          | ...   | 11.9          |
3. For the table above 'Filename' = 'test.csv' and 'Period col' = 'row_ids'. We could also set 'Initial period' = 2 and 'Final period' = 7 or leave 
them blank to use the whole file.
4. The following tables and columns can be have the values replaced for a batch column:
    1. Feeds:
        * Min %DM
        * Max %DM
        * Cost [US$/kg AF]
    2. Scenario
        * SBW
        * BCS
        * BE
        * L
        * SEX
        * a2
        * PH
        * Selling Price [US$]
5. To run the batch simply make sure that you place the name of the batch column in the cell that you want to run as a
batch. For example, instead of putting a value in the column 'Selling Price [US$]' on table 'Scenario', one could write
'Animal_price', assuming the file showed on item 2.

NOTE: If a scenario has batch ID = -1 or blank, i.e., it is not a batch scenario, having strings in place of values 
will raise error. So pay attention if you have multiple scenarios and not all are batch.

## Bonus
### Settings
You can change the file names and other settings in ```config.py```.
Be sure to have headers and sheet names matching in the ```config.py``` and ```input.xlsx```.
```
INPUT_FILE = {'filename': {'name': 'input.xlsx'},
              'sheet_feed_lib': {'name': 'Feed Library',
                                 'headers': [...]},
              'sheet_feeds': {'name': 'Feeds',
                              'headers': [...]},
              'sheet_scenario': {'name': 'Scenario',
                                 'headers': [...]}}
OUTPUT_FILE = 'output.xlsx'
SOLVER = 'HiGHS'
```
### Solver
We use the open-source solver [HiGHS](https://highs.dev) to optimize the LP models. Alternatively, you can use CPLEX
 (based on 12.8.1) by simply changing the header of ```config.py``` to:
```
SOLVER = "CPLEX"
```
Be sure to setup CPLEX properly.
Moreover, you can use any alternative solver by implementing the appropriate methods on the file "./maxprofitfeeding/
optimizer.py"

#### W64 vs LINUX
This project distributes HiGHS' DLL for W64. To run in Linux based systems, add the HiGHS ".so" file in the folder
 **"./optimizer/resources/"** and adjust the reference on **"./optimizer/resources/highs_solver.py"** in line 7:
```
highslib = ctypes.cdll.LoadLibrary("resources/highs.dll")
```
