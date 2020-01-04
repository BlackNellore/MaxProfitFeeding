# MaxProfitFeeding
Diet optimization model for beef cattle based on "Nutritional Requirements for Beef Cattle" 8th Ed. (NASEM, 2016).

NASEM - National Academies of Sciences, Engineering, and Medicine 2016. Nutrient Requirements of Beef Cattle, 8th Revised Edition. National Academies Press, Washington, D.C.


## Getting Started
**TLDR:**
```
>python setup.py develop
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
>python setup.py develop
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
    1. Sheet "Feeds": Choose the available feeds setting the ID, it will automatically retrieve the name from sheet "FeedLibrary" (NASEM, 2016). Set minimum and maximum concentration allowed (between 0 and 1), and feed cost \[US$/kg\].
    2. Sheet "Scenario":
        * ID: Scenario ID \[int\]
        * Breed: Breed Name (does not affect result)
        * SBW: Shrunk Bodyweight \[100; 800\]
        * BCS: Body Condition Score \[0; 9\]
        * BE: Breed Factor (check NASEM 2016, pg355 Table 19-1)
        * L: Lactation Factor {1, 1.2}
        * SEX: {1, 1.15}
        * a2: 0 if not considering acclimatization factor, check NASEM (2016) otherwise
        * PH: Rumen desired pH
        * Selling Price: Cattle Selling Price per \[U$/kg\]
        * Linearization factor: 
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
You can change the file names and other settings in ```config.py```:
```
INPUT_FILE = {'filename': 'input.xlsx',
              'sheet_feed': "FeedLibrary",
               'sheet_scenario': "Feeds",
               'sheet_cattle': "Scenario"}
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
