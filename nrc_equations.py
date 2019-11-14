""" NRC equations used to determine the model's parameter"""
import numpy as np


def swg(v_cneg, v_dmi, cnem, v_nem, sbw, linear_factor):
    """ Shrunk Weight Gain """
    return linear_factor * 0.87 * (v_dmi - v_nem/cnem) * v_cneg / np.power(sbw, 0.6836)


def swg_const(v_dmi, cnem, v_nem, sbw, linear_factor):
    """
    DEBUG PURPOSES:
    Constant parameter of SWG equation
    """
    return linear_factor * 0.87 * (v_dmi - v_nem / cnem) / np.power(sbw, 0.6836)


def dmi(cnem, sbw):
    """ Dry Matter Intake """
    return 0.007259 * sbw * (1.71167 + 2.64747 * cnem - np.power(cnem, 2))


def mpm(sbw):
    """ Metabolizable Protein for Maintenance """
    return 3.8 * np.power(sbw, 0.75)


def nem(sbw, bcs, be, l, sex, a2):
    """ Net Energy for Maintenance """
    return np.power(sbw, 0.75) * (0.077 * be * l * (0.8 + 0.05 * (bcs-1) * sex + a2))


def get_all_parameters(cnem, sbw, bcs, be, l, sex, a2, ph_val):
    """Easier way to get all parameters needed on the model at once"""
    return mpm(sbw), dmi(cnem, sbw), nem(sbw, bcs, be, l, sex, a2), pe_ndf(ph_val)


def mp(p_dmi, p_tdn, p_cp, p_rup, p_forage, p_ee):
    """Metabolizable Protein"""
    if p_dmi > 1:
        percentage = 0.01
    else:
        percentage = 1

    # NRC 8th Ed. pg 95 and pg 366
    if p_ee < 0.039:
        a = 42.73
        b = 0.087
        c = p_tdn
        if p_forage < 1:
            alpha = 0.8
        else:
            alpha = 0.8
    else:
        a = 53.33
        b = 0.096
        c = p_tdn - 2.55 * p_ee
        if p_forage < 1:
            alpha = 0.8
        else:
            alpha = 0.8

    protein = a * 1/1000 * 0 + 0.64 * b * c * percentage * 1/1000 + p_rup * percentage * p_cp * percentage * alpha

    return protein


def pe_ndf(ph_val):
    """Physically Effective Non-Detergent Fiber"""
    return 0.01 * (ph_val - 5.46)/0.038


# TODO: ch4 emissions
def ch4_diet():
    pass


def quick_check_lambda1(v_cneg, v_dmi, sbw, price, cost, linear_factor):
    return price * linear_factor * 0.87 * v_dmi * v_cneg / np.power(sbw, 0.6836) - v_dmi * cost


if __name__ == "__main__":
    print("hello nrc_equations")
