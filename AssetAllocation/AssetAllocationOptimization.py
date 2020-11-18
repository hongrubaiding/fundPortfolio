# -*- coding: UTF-8 -*-

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import mylog as mylog


class AssetAllocationOptimization:
    def __init__(self):
        # self.logger = mylog.set_log()
        pass

    def calc_omega(self, returnDf):
        cov_mat = returnDf.cov()
        if not isinstance(cov_mat, pd.DataFrame):
            self.logger.info('cov_mat should be pandas DataFrame！')
            return

        omega = np.matrix(cov_mat.values)  # 协方差矩阵
        return omega

    def risk_parity_asset_rate(self, asset_index, returnDf):
        '''
        计算风险平价模型，对各资产的看重程度
        '''
        riskAr = []  # 对国内股票看重的程度
        riskAr = [1 / returnDf.shape[1]] * returnDf.shape[1]
        # not_bond_num = returnDf.shape[1]-returnDf[asset_index['bond']].shape[1]
        # mrc_bond = 0.01
        # riskAr = []
        # for col in cov_mat:
        #     if col not in asset_index['bond'].keys():
        #         riskAr.append((1-mrc_bond)/not_bond_num)
        #     else:
        #         riskAr.append(mrc_bond)
        # riskAr = [0.36,0.26,0.26,0.02,0.10]
        return riskAr

    def set_con(self, returnDf, method, asset_index, allocationParam={}):
        '''
        针对特定模型，计算限制条件
        '''
        bnds = []
        for col in returnDf.columns.tolist():
            if ('bond' in asset_index) and (col in asset_index['bond'].keys()):
                # if col in asset_index['bond'].keys():
                if method == "risk_parity":
                    tem_bnd = (0, allocationParam.get('bond_limit', 0.2084))
                elif method == 'mean_var':
                    tem_bnd = (0, allocationParam.get('bond_limit', 0.0158))
                else:
                    tem_bnd = (0, 1)
            elif ('commodity' in asset_index) and (col in asset_index['commodity']):
                if method == "risk_parity":
                    tem_bnd = (0, allocationParam.get('com_limit', 0.5921))
                elif method == 'mean_var':
                    tem_bnd = (0, allocationParam.get('com_limit', 0.7559))
                else:
                    tem_bnd = (0, 1)
            else:
                tem_bnd = (0, 0.3)
            bnds.append(tem_bnd)
        return tuple(bnds)

    def target_risk_parity(self, returnDf, initX, asset_index, allocationParam):
        omega = self.calc_omega(returnDf)
        riskAr = self.risk_parity_asset_rate(asset_index, returnDf)

        def fun_risk_parity(x):
            tmp = (omega * np.matrix(x).T).A1
            delta_risk1 = []
            risk_TRC_div_dp = x * tmp / ((np.sqrt(np.matrix(x) * omega * np.matrix(x).T).A1[0]) ** 2)
            risk_TRC_div_dp[np.isnan(risk_TRC_div_dp)] = 0
            for r2 in risk_TRC_div_dp:
                delta_risk1.append((r2 - riskAr[list(risk_TRC_div_dp).index(r2)]) ** 2)
            total_delta = sum(delta_risk1)
            return total_delta

        bndrisk = self.set_con(returnDf, 'risk_parity', asset_index, allocationParam)
        cons = ({'type': 'eq', 'fun': lambda x: sum(x) - 1})
        options = {'disp': False, 'maxiter': 1000, 'ftol': 1e-25, }
        res = minimize(fun_risk_parity, initX.values, bounds=bndrisk, constraints=cons, method='SLSQP', options=options)
        wts = pd.Series(index=returnDf.columns.tolist(), data=res['x'])
        wts = wts / wts.sum() * 1.0
        if np.isnan(wts.max()):
            self.logger.info(res)
        return wts

    def target_mean_var(self, returnDf, initX, asset_index, allocationParam):
        omega = self.calc_omega(returnDf)
        bndrisk = self.set_con(returnDf, 'mean_var', asset_index, allocationParam)
        cons = ({'type': 'eq', 'fun': lambda x: sum(x) - 1})
        options = {'disp': False, 'maxiter': 5000, 'ftol': 1e-25, }

        def fun_mean_var(x):
            port_returns = np.sum(returnDf.mean() * x) * 252
            port_variance = np.sqrt(252 * np.matrix(x) * omega * np.matrix(x).T)
            result = -(port_returns - 10 * (port_variance))
            return result

        res = minimize(fun_mean_var, initX.values, bounds=bndrisk, constraints=cons, method='SLSQP', options=options)
        wts = pd.Series(index=returnDf.columns.tolist(), data=res['x'])
        wts = wts / wts.sum() * 1.0
        if np.isnan(wts.max()):
            self.logger.info(res)
        return wts

    def target_fix_rate(self, returnDf, initX, asset_index, allocationParam):
        return_df = returnDf.fillna(0)
        acc_return_df = (1 + return_df).prod()
        last_pos = initX * acc_return_df
        last_pos = last_pos / last_pos.sum()

        total_stock = [index_name for index_name in last_pos.index.tolist() if
                       index_name in asset_index['stock'].keys()]
        total_bond = [index_name for index_name in last_pos.index.tolist() if
                      index_name in asset_index['bond'].keys()]
        total_stock_weight = last_pos.loc[total_stock].sum()

        fix_stock_weight = allocationParam.get('fix_stock_weight', 0.9)
        # fix_bond_weight = allocationParam.get('fix_bond_weight',0.6)
        fix_bond_weight = 1 - fix_stock_weight
        fix_stock_zf = allocationParam.get('fix_stock_zf', 0.625)

        up_limit = fix_stock_weight * (1 + fix_stock_zf)
        dow_limit = fix_stock_weight * (1 - fix_stock_zf)
        if total_stock_weight > up_limit or total_stock_weight < dow_limit:
            dic_adjust = {}
            dic_adjust_stock = {index_name: fix_stock_weight / len(total_stock) for index_name in total_stock}
            dic_adjust_bond = {index_name: fix_bond_weight / len(total_bond) for index_name in total_bond}
            dic_adjust.update(dic_adjust_stock)
            dic_adjust.update(dic_adjust_bond)
            wts = pd.Series(dic_adjust)
            wts = wts / wts.sum()
        else:
            wts = last_pos
        return wts

    def target_recyle(self, returnDf, initX, asset_index, allocationParam):
        return_df = returnDf.fillna(0)
        acc_return_df = (1 + return_df).prod() - 1

        total_recyle_asset = [index_name for index_name in acc_return_df.index.tolist() if
                              index_name in asset_index['stock'].keys()]

        total_bond = [index_name for index_name in acc_return_df.index.tolist() if
                      index_name in asset_index['bond'].keys()]

        asset_commodity = asset_index.get('commodity', {})
        total_commodity = []
        if asset_commodity:
            total_commodity = [index_name for index_name in acc_return_df.index.tolist() if
                               index_name in asset_commodity.keys()]
            total_recyle_asset = total_recyle_asset + total_commodity

        max_index = acc_return_df.loc[total_recyle_asset].argmax()
        max_index_value = acc_return_df.loc[total_recyle_asset].max()

        dic_adjust = {}
        # self.logger.info("max_index: %s;max_index_value: %s"%(max_index,max_index_value))
        max_index_value_limit = allocationParam.get('max_index_value_limit', 0.1107)
        if max_index_value > max_index_value_limit:
            dic_adjust = {index_name: 0 for index_name in acc_return_df.index.tolist() if index_name != max_index}
            dic_adjust.update({max_index: 1})
        else:
            dic_adjust = {index_name: 0 for index_name in acc_return_df.index.tolist() if
                          index_name in total_recyle_asset}
            bond_dic = {index_name: 1 / len(total_bond) for index_name in acc_return_df.index.tolist() if
                        index_name in total_bond}
            dic_adjust.update(bond_dic)

        wts = pd.Series(dic_adjust)
        wts = wts / wts.sum()
        return wts

    def target_recyle_update(self, returnDf, initX, asset_index, allocationParam):
        max_value = (1 + returnDf).prod().max()
        max_index = (1 + returnDf).prod().argmax()
        # weight=pd.Series()
        if max_index == initX.argmax():
            weight = initX.copy()
        else:
            weight_te_list = []
            for index in initX.index.tolist():
                if index == max_index:
                    weight_te_list.append(1)
                else:
                    weight_te_list.append(0)
            weight = pd.Series(weight_te_list, index=initX.index)

        max_index_loss_limit = allocationParam.get('max_index_loss_limit', 1.0003172585708973)
        poc_value_limit = allocationParam.get('poc_value_limit', 0.00020468015454708915)

        if max_value < max_index_loss_limit:
            if max_value <= 1:
                weight = weight * poc_value_limit
                if 'bond' in asset_index:
                    not_bond = [code for code in weight.index.tolist() if code not in asset_index['bond']]
                    loss_weight = 1 - weight.loc[not_bond].sum()
                    for bond_code in list(asset_index['bond'].keys()):
                        weight[bond_code] = loss_weight / len(asset_index['bond'])
            else:
                return weight
        else:
            weight = weight / weight.sum()
        return weight

    def target_recyle_full(self, returnDf, initX, asset_index, allocationParam):
        poc_num = 5
        index_corr = allocationParam['index_corr']
        risk_asset_list = []
        for style, dic_data in asset_index.items():
            if style != 'bond':
                risk_asset_list = risk_asset_list + list(dic_data.keys())
        temp_se = (1 + returnDf[risk_asset_list]).prod().sort_values(ascending=False)
        flag_num = temp_se.median()

        not_zero_num = 0
        dic_value = {}
        for index_code in temp_se.index.tolist():
            if not_zero_num < poc_num:
                accreturn = temp_se[index_code]
                if not dic_value:
                    dic_value[index_code] = accreturn - flag_num
                    not_zero_num = not_zero_num + 1
                    continue

                temp_result_Se = index_corr.loc[list(dic_value.keys())][index_code]
                if len(temp_result_Se[temp_result_Se > 0.90]) >= 1:
                    dic_value[index_code] = 0
                else:
                    dic_value[index_code] = accreturn
                    not_zero_num = not_zero_num + 1
            else:
                dic_value[index_code] = 0
        weight = pd.Series(dic_value)

        weight = weight / weight.sum()

    def target_industry_recyle_equ(self, returnDf, initX, asset_index, allocationParam):
        index_corr = allocationParam['index_corr']
        poc_num = allocationParam.get('poc_num', 4)
        risk_asset_list = []
        for style, dic_data in asset_index.items():
            if style != 'bond':
                risk_asset_list = risk_asset_list + list(dic_data.keys())
        temp_se = (1 + returnDf[risk_asset_list]).prod().sort_values(ascending=False)

        dic_value = {}
        not_zero_num = 0
        total_list = temp_se.index.tolist()
        for index_code in total_list:
            if total_list.index(index_code) == 0:
                dic_value[index_code] = 1 / poc_num
                not_zero_num = not_zero_num + 1
            elif not_zero_num < poc_num:
                temp_result_Se = index_corr.loc[list(dic_value.keys())][index_code]
                if len(temp_result_Se[temp_result_Se > 0.90]) >= 1:
                    dic_value[index_code] = 0
                else:
                    dic_value[index_code] = 1 / poc_num
                    not_zero_num = not_zero_num + 1
            else:
                dic_value[index_code] = 0
        if 'bond' in asset_index:
            for bond_code in list(asset_index['bond'].keys()):
                dic_value[bond_code] = 0

        weight = pd.Series(dic_value)
        return weight

    def get_industry_recyle_port(self, risk_df, index_corr, asset_index, corr_limit, weight_score, temp_judge_market):
        returnDf = risk_df
        target_market_se = (1 + temp_judge_market).prod().sort_values(ascending=False)
        up_se = target_market_se[target_market_se > 1]
        up_se_rate = len(up_se) / temp_judge_market.dropna(axis=1, how='all').shape[1]

        if up_se_rate <= 0.15:
            # 熊市
            risk_free_weight = 0.7
        elif up_se_rate >= 0.75:
            # 牛市
            risk_free_weight = 0.1
        else:
            # 一般
            risk_free_weight = 0.2

        dic_select_etf = {}
        target_se = (1 + returnDf).prod().sort_values(ascending=False)
        for code in target_se.index.tolist():
            dic_select_etf['up_day_num'] = dic_select_etf.get('up_day_num', {})  # 上涨天数
            dic_select_etf['up_max'] = dic_select_etf.get('up_max', {})  # 上证幅度
            dic_select_etf['down_max_num'] = dic_select_etf.get('down_max_num', {})  # 大跌的天数
            dic_select_etf['vol_rate'] = dic_select_etf.get('vol_rate', {})  # 波动率
            dic_select_etf['conti_up_day'] = dic_select_etf.get('conti_up_day', {}) # 连涨天数

            temp_code_se = returnDf[code].copy()
            up_num=0
            maxnum = up_num
            for date_str in temp_code_se.index.tolist():
                if temp_code_se[date_str]>0:
                    up_num = up_num+1
                    if up_num>maxnum:
                        maxnum = up_num
                else:
                    up_num=0

            dic_select_etf['conti_up_day'][code] = maxnum
            dic_select_etf['up_day_num'][code] = len(temp_code_se[temp_code_se > 0])
            dic_select_etf['up_max'][code] = target_se[code]
            dic_select_etf['down_max_num'][code] = len(temp_code_se[temp_code_se < -0.05])
            dic_select_etf['vol_rate'][code] = temp_code_se.std()

        select_df = pd.DataFrame(dic_select_etf)
        score_df = pd.DataFrame()
        score_df['conti_up_day'] = select_df['conti_up_day'].rank(ascending=True)
        score_df['up_max'] = select_df['up_max'].rank(ascending=True)
        score_df['up_day_num'] = select_df['up_day_num'].rank(ascending=True)
        score_df['down_max_num'] = select_df['down_max_num'].rank(ascending=False)
        score_df['vol_rate'] = select_df['vol_rate'].rank(ascending=False)
        normal_df = (score_df - score_df.mean()) / score_df.std()

        total_score = (normal_df * weight_score).sum(axis=1)

        dic_poc = {}
        non_num = 5
        start_num = 1
        for code in total_score.index.tolist():
            if start_num <= non_num:
                temp_result_Se = index_corr.loc[list(dic_poc.keys())][code]
                if len(temp_result_Se[temp_result_Se > corr_limit]) >= 1:
                    dic_poc[code] = 0
                else:
                    dic_poc[code] = total_score[code]
                    start_num = start_num + 1
            else:
                dic_poc[code] = 0

        weight = pd.Series(dic_poc).sort_values(ascending=False)
        weight = weight - weight.iloc[non_num - 1]
        weight[weight < 0] = 0
        weight = (weight / weight.sum()) * (1 - risk_free_weight)

        max_poc = 0.4
        if len(weight[weight > max_poc]) > 0:
            total_add_weight = (weight[weight > max_poc] - max_poc).sum()
            other_weight = weight[weight < max_poc].sum()
            new_weight = {}
            for code in weight.index:
                if max_poc > weight[code] > 0:
                    new_weight[code] = weight[code] + total_add_weight * (weight[code] / other_weight)
                elif weight[code] >= max_poc:
                    new_weight[code] = max_poc
                else:
                    new_weight[code] = 0
            weight = pd.Series(new_weight)

        if 'bond' in asset_index:
            for bond_code in list(asset_index['bond'].keys()):
                weight[bond_code] = risk_free_weight / len(asset_index['bond'])

        weight[weight < 0.03] = 0
        weight = weight / weight.sum()
        return weight

    def target_industry_recyle2(self, returnDf, initX, asset_index, allocationParam, indexReturnDf):
        max_index_loss_limit = allocationParam.get('max_index_loss_limit', 1.0003172585708973)
        poc_value_limit = allocationParam.get('poc_value_limit', 0.00020468015454708915)
        judge_market = allocationParam.get('judge_market', 20)

        up_max = allocationParam.get('up_max', 0.4)
        up_day_num = allocationParam.get('up_day_num', 0.3)
        down_max_num = allocationParam.get('down_max_num', 0.3)
        vol_rate = allocationParam.get('vol_rate', 0.3)
        conti_up_day = allocationParam.get('conti_up_day', 0.3)

        weight_score = pd.Series([up_max, up_day_num, down_max_num, vol_rate, conti_up_day],
                                 index=['up_max', 'up_day_num', 'down_max_num', 'vol_rate', 'conti_up_day'])
        weight_score = weight_score / weight_score.sum()

        corr_limit = allocationParam.get('corr_limit', 0.90)
        index_corr = allocationParam['index_corr']
        risk_asset_list = []
        for style, dic_data in asset_index.items():
            if style != 'bond':
                risk_asset_list = risk_asset_list + list(dic_data.keys())
        risk_df = returnDf[risk_asset_list]
        total_date_list = indexReturnDf.index.tolist()
        if len(total_date_list) > judge_market:
            temp_judge_market = indexReturnDf.loc[total_date_list[-judge_market:]]
        else:
            temp_judge_market = indexReturnDf
        weight = self.get_industry_recyle_port(risk_df, index_corr, asset_index, corr_limit, weight_score,
                                               temp_judge_market)
        return weight

    def target_industry_recyle(self, returnDf, initX, asset_index, allocationParam):
        poc_num = 6
        max_index_loss_limit = allocationParam.get('max_index_loss_limit', 1.0003172585708973)
        poc_value_limit = allocationParam.get('poc_value_limit', 0.00020468015454708915)

        index_corr = allocationParam['index_corr']

        risk_asset_list = []
        for style, dic_data in asset_index.items():
            if style != 'bond':
                risk_asset_list = risk_asset_list + list(dic_data.keys())
        temp_se = (1 + returnDf[risk_asset_list]).prod().sort_values(ascending=False)

        target_se = temp_se[temp_se > max_index_loss_limit]  # 所有上涨超过阈值的行业
        flag = max_index_loss_limit
        dic_value = {}
        if target_se.empty:
            flag = 1
            target_se = temp_se[temp_se > flag]

            if target_se.empty:
                for index_code in temp_se.index.tolist():
                    dic_value[index_code] = 0
                if 'bond' in asset_index:
                    for bond_code in list(asset_index['bond'].keys()):
                        dic_value[bond_code] = 1 / len(asset_index['bond'])
                weight = pd.Series(dic_value)
                weight[weight < 0.03] = 0
                weight = weight / weight.sum()
                return weight

        not_zero_num = 0
        for index_code in temp_se.index.tolist():
            if not_zero_num < poc_num:
                accreturn = temp_se[index_code]
                if accreturn >= flag:
                    if not dic_value:
                        dic_value[index_code] = accreturn - flag
                        not_zero_num = not_zero_num + 1
                        continue

                    temp_result_Se = index_corr.loc[list(dic_value.keys())][index_code]
                    if len(temp_result_Se[temp_result_Se > 0.90]) >= 1:
                        dic_value[index_code] = 0
                    else:
                        dic_value[index_code] = accreturn - flag
                        not_zero_num = not_zero_num + 1
                else:
                    dic_value[index_code] = 0
            else:
                dic_value[index_code] = 0
        weight = pd.Series(dic_value)
        weight = weight / weight.sum()
        if flag == 1:
            weight = weight * poc_value_limit
            loss_weight = 1 - poc_value_limit
        else:
            loss_weight = 0

        if 'bond' in asset_index:
            for bond_code in list(asset_index['bond'].keys()):
                weight[bond_code] = loss_weight / len(asset_index['bond'])
        weight[weight < 0.03] = 0
        weight = weight / weight.sum()
        return weight

    def taret_industry_recyle_stock(self, returnDf, initX, asset_index, allocationParam):
        risk_asset_list = []
        poc_num = 5
        temp_se = (1 + returnDf).prod().sort_values(ascending=False)
        max_index_loss_limit = allocationParam.get('max_index_loss_limit', 1.297)
        index_corr = allocationParam['index_corr']

        dic_value = {}
        for index_code in temp_se.index.tolist():
            if len(dic_value) < poc_num + 1:
                accreturn = temp_se[index_code]
                if not dic_value:
                    dic_value[index_code] = accreturn
                    continue

                temp_result_Se = index_corr.loc[list(dic_value.keys())][index_code]
                if len(temp_result_Se[temp_result_Se > 0.9]) >= 1:
                    continue
                else:
                    dic_value[index_code] = accreturn
            else:
                dic_value[index_code] = 0
        weight = pd.Series(dic_value, ).sort_values(ascending=False)
        for code in weight.index:
            weight[code] = weight[code] - weight.iloc[5]
        weight[weight < 0.03] = 0
        # wts[wts < 0.03] = 0
        # wts = wts / wts.sum() * 1.0
        weight = weight / weight.sum()
        return weight

    def target_industry_recyle_mean_var_stock(self, return_old_Df, initX, asset_index, allocationParam):
        returnDf = return_old_Df.dropna(axis=1, how='all')
        try:
            initX = initX.loc[returnDf.columns.tolist()]
        except:
            initX = pd.Series([1 / returnDf.shape[1]] * returnDf.shape[0], index=returnDf.columns.tolist())

        omega = self.calc_omega(returnDf)
        bndrisk = self.set_con(returnDf, 'mean_var', asset_index, allocationParam)
        cons = ({'type': 'eq', 'fun': lambda x: sum(x) - 1})
        options = {'disp': False, 'maxiter': 2000, 'ftol': 1e-25, }

        def fun_mean_var(x):
            port_returns = np.sum(returnDf.mean() * x) * 252
            port_variance = np.sqrt(252 * np.matrix(x) * omega * np.matrix(x).T)
            result = -(port_returns - 10 * (port_variance))
            return result

        res = minimize(fun_mean_var, initX.values, bounds=bndrisk, constraints=cons, method='SLSQP', options=options)
        wts = pd.Series(index=returnDf.columns.tolist(), data=res['x'])
        for col in return_old_Df.columns.tolist():
            if col not in wts.index.tolist():
                wts[col] = 0
        wts[wts < 0.03] = 0
        wts = wts / wts.sum() * 1.0
        if np.isnan(wts.max()):
            # self.logger.info(res)
            pass
        return wts

    def get_smart_weight(self, returnDf, initX, asset_index={}, method='mean_var', allocationParam={},
                         indexReturnDf=pd.DataFrame()):
        if method == 'risk_parity':
            wts = self.target_risk_parity(returnDf, initX, asset_index, allocationParam)
        elif method == 'mean_var':
            wts = self.target_mean_var(returnDf, initX, asset_index, allocationParam)
        elif method == 'fix_rate':
            wts = self.target_fix_rate(returnDf, initX, asset_index, allocationParam)
        elif method == 'recyle':
            wts = self.target_recyle(returnDf, initX, asset_index, allocationParam)
        elif method == 'recyle_update':
            wts = self.target_recyle_update(returnDf, initX, asset_index, allocationParam)
        elif method == 'industry_recyle':
            wts = self.target_industry_recyle2(returnDf, initX, asset_index, allocationParam, indexReturnDf)
        elif method == 'recyle_full':
            wts = self.target_recyle_full(returnDf, initX, asset_index, allocationParam)
        elif method == 'industry_recyle_stock':
            wts = self.taret_industry_recyle_stock(returnDf, initX, asset_index, allocationParam)
        elif method == 'industry_recyle_mean_var_stock':
            wts = self.target_industry_recyle_mean_var_stock(returnDf, initX, asset_index, allocationParam)
        elif method == 'industry_recyle_equ':
            wts = self.target_industry_recyle_equ(returnDf, initX, asset_index, allocationParam)
        return wts
