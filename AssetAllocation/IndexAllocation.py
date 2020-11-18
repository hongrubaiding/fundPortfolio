# -*- coding: UTF-8 -*-

import numpy as np
import pandas as pd
from scipy.optimize import minimize

def get_smart_weight(returnDf, initX, asset_index={}, method='mean_var', allocationParam={}):
    cov_mat = returnDf.cov()
    if not isinstance(cov_mat, pd.DataFrame):
        raise ValueError('cov_mat should be pandas DataFrame！')

    omega = np.matrix(cov_mat.values)  # 协方差矩阵
    def MaxDrawdown(return_list):
        '''最大回撤率'''
        return_list = (return_list + 1).cumprod()
        return_list = return_list.values
        i = np.argmax(np.maximum.accumulate(return_list) - return_list)
        if i == 0:
            return 0
        j = np.argmax(return_list[:i])
        result = (return_list[j] - return_list[i]) / return_list[j]
        return result

    if method == 'target_maxdown':
        rate = allocationParam.get('allocationParam', 0.3)
        maxDwonSe = returnDf.dropna().apply(MaxDrawdown)
        assetMaxDown = (maxDwonSe.max() - maxDwonSe.min()) * rate  # 用户可承担的最大回撤组合站所有资产最大的百分比
    elif method == 'target_risk':
        rate = allocationParam.get('allocationParam', 0.2)
        # 用户可承担的风险组合占所有资产最大的百分比
        assetStd = (returnDf.std().max() - returnDf.std().min()) * np.sqrt(250) * rate
    elif method == 'risk_parity':
        riskAr = []  # 对国内股票看重的程度
        riskAr = [1 / returnDf.shape[1]] * returnDf.shape[1]
        # not_bond_num = cov_mat.shape[1]-cov_mat[asset_index['bond']].shape[1]
        # mrc_bond = 0.01
        # riskAr = []
        # for col in cov_mat:
        #     if col not in asset_index['bond'].keys():
        #         riskAr.append((1-mrc_bond)/not_bond_num)
        #     else:
        #         riskAr.append(mrc_bond)
        # riskAr = [0.36,0.26,0.26,0.02,0.10]


    def riskparity_and_meanvar_con():
        bnds = []
        for col in cov_mat.columns.tolist():
            if col in asset_index['bond'].keys():
                if method == "risk_parity":
                    tem_bnd = (0,allocationParam.get('bond_limit', 0.2084))
                elif method == 'mean_var':
                    tem_bnd = (0,allocationParam.get('bond_limit', 0.0158))
            elif col in asset_index['commodity']:
                if method == "risk_parity":
                    tem_bnd = (0,allocationParam.get('com_limit', 0.5921))
                elif method == 'mean_var':
                    tem_bnd = (0,allocationParam.get('com_limit', 0.7559))
            else:
                tem_bnd = (0, 1)
            bnds.append(tem_bnd)
        return tuple(bnds)

    # 定义目标函数
    def fun1(x):  # 组合总风险
        result = np.matrix(x) * omega * np.matrix(x).T
        return result

    def fun2(x):
        tmp = (omega * np.matrix(x).T).A1
        delta_risk1 = []
        risk_TRC_div_dp = x * tmp / ((np.sqrt(np.matrix(x) * omega * np.matrix(x).T).A1[0]) ** 2)
        for r2 in risk_TRC_div_dp:
            delta_risk1.append((r2 - riskAr[list(risk_TRC_div_dp).index(r2)]) ** 2)
        total_delta = sum(delta_risk1)
        return total_delta

    def fun3(x):
        den = x * omega.diagonal().T
        num = np.sqrt(np.matrix(x) * omega * np.matrix(x).T)
        return num / den

    def fun4(x):
        port_returns = np.sum(returnDf.mean() * x) * 252
        port_variance = np.sqrt(252 * np.matrix(x) * omega * np.matrix(x).T)

        # result = -port_returns / port_variance
        result = -(port_returns - 10 * (port_variance))
        return result

    def fun5(x):
        port_returns = -np.sum(returnDf.mean() * x) * 252
        return port_returns

    # 初始值 + 约束条件
    x0 = initX.values
    cons = ({'type': 'eq', 'fun': lambda x: sum(x) - 1})
    options = {'disp': False, 'maxiter': 1000, 'ftol': 1e-25, }

    if method == 'min_variance':
        bnds = tuple((0, 1) for x in x0)
        res = minimize(fun1, x0, bounds=bnds, constraints=cons, method='SLSQP', options=options)
    elif method == 'risk_parity':
        bndrisk = riskparity_and_meanvar_con()
        # bndrisk = tuple((0, 1) for x in x0)
        res = minimize(fun2, x0, bounds=bndrisk, constraints=cons, method='SLSQP', options=options)
    elif method == 'max_diversification':
        bnds = tuple((0, 1) for x in x0)
        res = minimize(fun3, x0, bounds=bnds, constraints=cons, method='SLSQP', options=options)
    elif method == 'equal_weight':
        return pd.Series(index=cov_mat.index, data=1.0 / cov_mat.shape[0])
    elif method == 'mean_var':
        bndrisk = riskparity_and_meanvar_con()
        res = minimize(fun4, x0, bounds=bndrisk, constraints=cons, method='SLSQP', options=options)
    elif method == 'target_maxdown':
        bnds = tuple((0, 1) for x in x0)
        cons = ({'type': 'eq', 'fun': lambda x: sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: -MaxDrawdown((x * returnDf).sum(axis=1)) + assetMaxDown})
        res = minimize(fun5, x0, bounds=bnds, constraints=cons, method='SLSQP', options=options,
                       tol=1e-5)  # Nelder Mead,SLSQP
    elif method == 'target_risk':
        bnds = tuple((0, 1) for x in x0)
        cons = ({'type': 'eq', 'fun': lambda x: sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: -np.sqrt(fun1(x)[0, 0]) * np.sqrt(250) + assetStd}
                )  # ,
        res = minimize(fun5, x0, bounds=bnds, constraints=cons, method='SLSQP', options=options)
    else:
        raise ValueError('method should be min variance/risk parity/max diversification/equal weight！！！')

    wts = pd.Series(index=cov_mat.index, data=res['x'])
    wts = wts / wts.sum() * 1.0
    return wts
