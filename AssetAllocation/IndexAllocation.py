# -*- coding: UTF-8 -*-

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from PrintInfo import PrintInfo
# import matplotlib.pyplot as plt

PrintInfoDemo = PrintInfo()

def get_smart_weight(returnDf,initX, method='mean_var',wts_adjusted=False,**modelParam):
    '''
    功能：输入协方差矩阵，得到不同优化方法下的权重配置
    输入：
        cov_mat  pd.DataFrame,协方差矩阵，index和column均为资产名称
        method  优化方法，可选的有min variance、risk parity、max diversification、equal weight
    输出：
        pd.Series  index为资产名，values为weight
    PS:
        依赖scipy package
    '''
    cov_mat = returnDf.cov()

    if not isinstance(cov_mat, pd.DataFrame):
        raise ValueError('cov_mat should be pandas DataFrame！')

    omega = np.matrix(cov_mat.values)  # 协方差矩阵
    def MaxDrawdown(return_list):
        '''最大回撤率'''
        return_list = (return_list+1).cumprod()
        return_list = return_list.values
        i = np.argmax(np.maximum.accumulate(return_list) - return_list)
        if i == 0:
            return 0
        j = np.argmax(return_list[:i])
        result = (return_list[j] - return_list[i]) / return_list[j]
        return result

    if method == 'target_maxdown':
        rate = modelParam.get('allocationParam',0.3)
        maxDwonSe = returnDf.dropna().apply(MaxDrawdown)
        assetMaxDown = (maxDwonSe.max() -maxDwonSe.min()) * rate  # 用户可承担的最大回撤组合站所有资产最大的百分比
    elif method == 'target_risk':
        rate = modelParam.get('allocationParam', 0.2)
        #用户可承担的风险组合占所有资产最大的百分比
        assetStd = (returnDf.std().max() - returnDf.std().min())*np.sqrt(250)*rate
    elif method == 'risk_parity':
        riskAr = []             #对国内股票看重的程度
        if not modelParam or modelParam['allocationParam'] == 'equal':
            riskAr = [1/returnDf.shape[1]]*returnDf.shape[1]
        else:
            riskRate = modelParam['allocationParam']
            for indexName in returnDf.columns:
                 if indexName in ['000016.SH','000300.SH','000905.SH']:
                     riskAr.append(riskRate/3)
                 elif indexName != 'CBA00601.CS':
                     riskAr.append((1-riskRate)*0.98/(returnDf.shape[1]-4))
                 else:
                     riskAr.append((1-riskRate)*0.02)

            print('riskAr:',riskAr)

    # 定义目标函数
    def fun1(x):  # 组合总风险
        result = np.matrix(x) * omega * np.matrix(x).T
        return result

    def fun2(x):
        tmp = (omega * np.matrix(x).T).A1
        risk = x * tmp
        # delta_risk = [sum((i - risk) ** 2) for i in risk]
        totalRisk = risk.sum()

        delta_risk = [((i - riskAr[list(risk).index(i)]*totalRisk) ** 2).sum() for i in risk]
        # delta_risk = [sum((i - riskAr[list(risk).index(i)]*risk) ** 2) for i in risk]
        return sum(delta_risk)

    def fun3(x):
        den = x * omega.diagonal().T
        num = np.sqrt(np.matrix(x) * omega * np.matrix(x).T)
        return num / den

    def fun4(x):
        port_returns = np.sum(returnDf.mean() * x) * 252
        port_variance = np.sqrt(252 * np.matrix(x) * omega * np.matrix(x).T)

        # result = -port_returns / port_variance
        result = -(port_returns-100*(port_variance))

        return result

    def fun5(x):
        port_returns = -np.sum(returnDf.mean() * x) * 252
        return port_returns

    # 初始值 + 约束条件
    x0 = initX.values
    bnds = tuple((0, 1) for x in x0)
    cons = ({'type': 'eq', 'fun': lambda x: sum(x) - 1})
    options = {'disp': False, 'maxiter': 1000, 'ftol': 1e-25,}

    if method == 'min_variance':
        res = minimize(fun1, x0, bounds=bnds, constraints=cons, method='SLSQP', options=options)
    elif method == 'risk_parity':
        res = minimize(fun2, x0, bounds=bnds, constraints=cons, method='SLSQP', options=options)
    elif method == 'max_diversification':
        res = minimize(fun3, x0, bounds=bnds, constraints=cons, method='SLSQP', options=options)
    elif method == 'equal_weight':
        return pd.Series(index=cov_mat.index, data=1.0 / cov_mat.shape[0])
    elif method == 'mean_var':
        bnds = tuple((0, 0.4) for x in x0)
        res = minimize(fun4, x0, bounds=bnds, constraints=cons, method='SLSQP', options=options)
    elif method == 'target_maxdown':
        cons = ({'type': 'eq', 'fun': lambda x: sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: -MaxDrawdown((x*returnDf).sum(axis=1))+assetMaxDown})
        res = minimize(fun5, x0, bounds=bnds, constraints=cons, method='SLSQP', options=options,tol=1e-5)  #Nelder Mead,SLSQP
    elif method == 'target_risk':
        cons = ({'type': 'eq', 'fun': lambda x: sum(x) - 1},{'type': 'eq', 'fun': lambda x: -np.sqrt(fun1(x)[0,0])*np.sqrt(250)+assetStd}
                )#,
        res = minimize(fun5, x0, bounds=bnds, constraints=cons, method='SLSQP', options=options)
    else:
        raise ValueError('method should be min variance/risk parity/max diversification/equal weight！！！')

    # 权重调整
    if res['success'] == False:
        PrintInfoDemo.PrintLog(infostr="minize result：",otherInfo=res['message'])
        # print("minize result：",res['message'])

    wts = pd.Series(index=cov_mat.index, data=res['x'])
    if wts_adjusted == True:
        wts = wts[wts >= 0.0001]
        return wts / wts.sum() * 1.0
    elif wts_adjusted == False:
        return wts
    else:
        raise ValueError('wts_adjusted should be True/False！')
