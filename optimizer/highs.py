import ctypes
import logging
import numpy as np
from scipy.sparse import csc_matrix
import platform

# highs lib folder must be in "LD_LIBRARY_PATH" environment variable
highslib = None

def_status = {0: "optimal", None: "infeasible"}
epsilon = 0.0000001
infinite = 10000000


def config():
    global highslib
    if platform.system() in ('Windows', 'Microsoft'):
        highslib = ctypes.cdll.LoadLibrary("./resources/highs.dll")
    else:
        # Implement call to LINUX .so solver
        raise SystemError("Only windows dll available")

    highslib.Highs_call.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_int),
                                    ctypes.POINTER(ctypes.c_int),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_double),
                                    ctypes.POINTER(ctypes.c_int),
                                    ctypes.POINTER(ctypes.c_int),
                                    ctypes.POINTER(ctypes.c_int))
    highslib.Highs_call.restype = ctypes.c_int


def highs_call(colcost, collower, colupper, rowlower, rowupper, astart, aindex, avalue):
    """
    :param colcost: obj-fun coefficients [default minimize]
    :param collower: vector variables lower bound
    :param colupper: vector variables upper bound
    :param rowlower: vector with constraints lhs bounds
    :param rowupper: vector with constraints rhs bounds
    :param astart: column pointer vector (column compression matrix)
    :param aindex: row-index vector (column compression matrix)
    :param avalue: non-zero coefficients vector (column compression matrix)
    :returns retcode: status code
    :returns col_value: optimal variables' values
    :returns col_dual: optimal dual variables' values (shadow price)
    :returns row_value: Ax
    :returns row_dual: reduced costs of constraints
    :returns col_basis: check comment on Enum objetc below
    :returns row_basis: check comment on Enum objetc below

     enum class HighsBasisStatus {
       LOWER =
           0,  // (slack) variable is at its lower bound [including fixed variables]
       BASIC,  // (slack) variable is basic
       UPPER,  // (slack) variable is at its upper bound
       ZERO,   // free variable is non-basic and set to zero
       NONBASIC, // nonbasic with no specific bound information - useful for users and postsolve
       SUPER   // Super-basic variable: non-basic and either free and
               // nonzero or not at a bound. No SCIP equivalent
     };
    """

    global highslib
    n_col = len(colcost)
    n_row = len(rowlower)
    n_nz = len(aindex)

    dbl_array_type_col = ctypes.c_double * n_col
    dbl_array_type_row = ctypes.c_double * n_row
    int_array_type_astart = ctypes.c_int * (n_col + 1)
    int_array_type_aindex = ctypes.c_int * n_nz
    dbl_array_type_avalue = ctypes.c_double * n_nz

    int_array_type_col = ctypes.c_int * n_col
    int_array_type_row = ctypes.c_int * n_row

    col_value = [0] * n_col
    col_dual = [0] * n_col

    row_value = [0] * n_row
    row_dual = [0] * n_row

    col_basis = [0] * n_col
    row_basis = [0] * n_row

    return_val = 0

    col_value = dbl_array_type_col(*col_value)
    col_dual = dbl_array_type_col(*col_dual)
    row_value = dbl_array_type_row(*row_value)
    row_dual = dbl_array_type_row(*row_dual)
    col_basis = int_array_type_col(*col_basis)
    row_basis = int_array_type_row(*row_basis)
    try:
        retcode = highslib.Highs_call(
            ctypes.c_int(n_col), ctypes.c_int(n_row), ctypes.c_int(n_nz),
            dbl_array_type_col(*colcost), dbl_array_type_col(*collower), dbl_array_type_col(*colupper),
            dbl_array_type_row(*rowlower), dbl_array_type_row(*rowupper),
            int_array_type_astart(*astart), int_array_type_aindex(*aindex), dbl_array_type_avalue(*avalue),
            col_value, col_dual,
            row_value, row_dual,
            col_basis, row_basis, ctypes.byref(ctypes.c_int(return_val)))
    except Exception as e:
        if "writing" in e.args[0]:
            logging.error("A serious error occurred when executing HiGHS, probably infeasible: {}".format(str(e)))
        else:
            logging.error("An error occurred when executing HiGHS, probably infeasible: {}".format(str(e)))
        return None
    return retcode, list(col_value), list(col_dual), list(row_value), list(row_dual), list(col_basis), list(row_basis)


if __name__ == "__main__":
    config()

    cc = (1.0, -2.0, 0.5)
    cl = (0.0, 0.0, 0.0)
    cu = (10.0, 10.0, 10.0)
    ru = (4.0, 3.0)
    rl = (0.0, 0.0)

    # astart = (0, 2, 4, 6)
    # aindex = (0, 1, 0, 1, 0, 1)
    # avalue = (1.0, 2.0, 1.0, 3.0, 3.0, 5.0)

    data = [[1.0, 2.0, 3.0],
            [1.0, 3.0, 0.5]]
    row_i = []
    col_i = []
    lin_data = []
    for i, r in enumerate(data):
        for j, c in enumerate(r):
            row_i.append(i)
            col_i.append(j)
            lin_data.append(c)

    sparse_matrix = csc_matrix((lin_data, (row_i, col_i)), shape=(len(ru), len(cc)))
    aindex = list(sparse_matrix.indices)
    astart = list(sparse_matrix.indptr)
    avalue = list(sparse_matrix.data)


    rc, cv, cd, rv, rd , cbs, rbs = highs_call(cc, cl, cu, rl, ru, astart, aindex, avalue)

    print(rc, cv, cd, rv, rd, cbs, rbs)
