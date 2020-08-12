import unittest
from model.nrc_equations import NRC_eq as Nrc


class TestNRCequations(unittest.TestCase):
    # Testing these functions from nrc_equations.py
    # cneg(cnem)
    # dmi(cnem, sbw)
    # mpm(sbw)
    # nem(sbw, bcs, be, l, sex, a2)
    # neg(cneg, v_dmi, cnem, v_nem)
    # swg(neg, sbw)
    #
    # pe_ndf(ph_val)
    #
    # get_all_parameters(cnem, sbw, bcs, be, l, sex, a2, ph_val)
    #
    # mp(p_dmi=0, p_tdn=0, p_cp=0, p_rup=0, p_forage=0, p_ee=0)

    # Test ranges
    # [cnem, sbw, bcs, be, l, sex, a2, ph_val] = [None for i in range(8)]
    cnem_range = [-0.2 + 0.10001 * i for i in range(21)]
    sbw_range = [-50 + 50.00001 * i for i in range(21)]
    bcs_range = [i for i in range(-1, 10)]
    be_range = [i for i in range(-1, 2)]
    l_range = [-1, 0, 1, 1.1]
    sex_range = [-1, 0, 1, 1.1]
    a2_range = [-1, 0, 0.5, 1]
    ph_val_range = [-1.5 + i * 1.5 for i in range(16)]

    def __value_error(self, func, **kwargs):
        if None in kwargs.values():
            return None
        if any([v < 0 for k, v in kwargs.items()]):
            self.assertRaises(ValueError, func, *list(kwargs.values()))
            return None
        else:
            return func(**kwargs)

    def test_default_parameters(self):
        for sbw in self.sbw_range:
            self.__value_error(Nrc.mpm, sbw=sbw)
            for bcs in self.bcs_range:
                for be in self.be_range:
                    for sex in self.sex_range:
                        for ll in self.l_range:
                            for a2 in self.a2_range:
                                nem = self.__value_error(Nrc.nem, sbw=sbw, bcs=bcs, be=be, l=ll, sex=sex, a2=a2)
                                for cnem in self.cnem_range:
                                    dmi = self.__value_error(Nrc.dmi, cnem=cnem, sbw=sbw)
                                    cneg = self.__value_error(Nrc.cneg, cnem=cnem)
                                    neg = self.__value_error(Nrc.neg, cneg=cneg, v_dmi=dmi, cnem=cnem, v_nem=nem)
                                    self.__value_error(Nrc.swg, neg=neg, sbw=sbw)
        for ph_val in self.ph_val_range:
            self.__value_error(Nrc.pe_ndf, ph_val=ph_val)


if __name__ == '__main__':
    tests = TestNRCequations()
    tests.test_default_parameters()
