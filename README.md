# MaxProfitFeeding (teste jair)
Diet optimization model for beef cattle based on "Nutritional Requirements for Beef Cattle" 8th Ed. (NASEM, 2016).

This model requires only the available feedstuff and animal's characteristics to compute a maximum profit diet.
We use feestuff properties from NASEM (2016). This work is based on a theoretical framework and in no way replace an appropriate nutritional analysis.
Thus, we do not hold any responsibility for applications of this work in livestock.
Always consult a veterinary before changing the feed composition for your herd.

This model is part of a PhD project at the University of Edinburgh and a thematic project funded by FAPESP.


#### References
FAPESP project Title: "Sugarcane - Livestock Integration: Modeling and Optimization", FAPESP Project Number:  2017/11523-5

NASEM - National Academies of Sciences, Engineering, and Medicine 2016. Nutrient Requirements of Beef Cattle, 8th Revised Edition. National Academies Press, Washington, D.C.


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

This python project requires some libraries. They should be automatically installed if you execute with administrative rights:
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


### Running
1. Adjust your input in the file **"./input.xlsx"**: 
    1. Sheet "Feeds": Choose the available feeds setting the ID, it will automatically retrieve the name from sheet "FeedLibrary" (NASEM, 2016).
    Set minimum and maximum concentration allowed (between 0 and 1), and feed cost \[US$/kg\].
    The column "Feed Scenario" aggregates all feedstuff that belong to a particular scenario.
    This index will be matched with the one in the sheet "Scenario"
    2. Sheet "Scenario":
        * ID: Scenario ID \[int\]
        * Feed Scenario: Define with feed scenario should be match in the sheet "Feeds" \[int\]
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
2. Run:
    ```
    >python run.py
    ```
3. Results: if everything is alright, you can check your solution on **"./output.xlsx"**. Otherwise, you can check the **"./activity.log"** to see if any errors happened.

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
We use the open-source solver [HiGHS](https://highs.dev) to optimize the LP models. Alternatively, you can use CPLEX (based on 12.8.1) by simply changing the header of ```config.py``` to:
```
SOLVER = "CPLEX"
```
Be sure to setup CPLEX properly.
Moreover, you can use any alternative solver by implementing the appropriate methods on the file "./maxprofitfeeding/optimizer.py"

#### W64 vs LINUX
This project distributes HiGHS' DLL for W64. To run in Linux based systems, add the HiGHS ".so" file in the folder **"./optimizer/resources/"** and adjust the reference on **"./optimizer/resources/highs_solver.py"** in line 7:
```
highslib = ctypes.cdll.LoadLibrary("resources/highs.dll")
```
