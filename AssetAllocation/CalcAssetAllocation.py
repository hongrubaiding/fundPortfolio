# -- coding: utf-8 --


import pandas as pd
import numpy as np
from AssetAllocation.AssetAllocationOptimization import AssetAllocationOptimization
import mylog as mylog
from datetime import datetime, timedelta


class CalcAssetAllocation:
    def __init__(self):
        self.logger = mylog.set_log()
        self.AssetAllocationOptimizationDemo = AssetAllocationOptimization()

    def distribution_init_weight(self, asset_index, tempReturnDF, method, datestr, IndexAllocationParam={}):
        '''
        按大类分配权重
        '''
        if method == 'recyle_update':
            total_index = tempReturnDF.columns.tolist()
            max_index = (1 + tempReturnDF).prod().argmax()
            weight = []
            for index in total_index:
                if index == max_index:
                    weight.append(1)
                else:
                    weight.append(0)
        elif method in ['industry_recyle_stock', 'industry_recyle_mean_var_stock']:
            risk_asset_list = []
            poc_num = 5
            temp_se = (1 + tempReturnDF).prod().sort_values(ascending=False)
            max_index_loss_limit = IndexAllocationParam.get('max_index_loss_limit', 1.297)
            index_corr = IndexAllocationParam['index_corr']

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
            weight = pd.Series(dic_value, name=datestr).sort_values(ascending=False)
            for code in weight.index:
                weight[code] = weight[code] - weight.iloc[5]
            weight[weight < 0] = 0
            weight = weight / weight.sum()
        elif method == 'industry_recyle':
            corr_limit = IndexAllocationParam.get('corr_limit', 0.90)
            poc_num = 5
            risk_asset_list = []
            for style, dic_data in asset_index.items():
                if style != 'bond':
                    risk_asset_list = risk_asset_list + list(dic_data.keys())
            temp_se = (1 + tempReturnDF[risk_asset_list]).prod().sort_values(ascending=False)
            max_index_loss_limit = IndexAllocationParam.get('max_index_loss_limit', 1.297)
            index_corr = IndexAllocationParam['index_corr']
            poc_value_limit = IndexAllocationParam.get('poc_value_limit',0.8)

            if temp_se[temp_se > 1].empty:
                weight = pd.Series()
                return weight
            elif temp_se[temp_se > max_index_loss_limit].empty:
                max_index_loss_limit = 1.0

            dic_value = {}
            for index_code in temp_se.index.tolist():
                if len(dic_value) < poc_num:
                    accreturn = temp_se[index_code]
                    if accreturn >= max_index_loss_limit:
                        if not dic_value:
                            dic_value[index_code] = accreturn - max_index_loss_limit
                            continue

                        temp_result_Se = index_corr.loc[list(dic_value.keys())][index_code]
                        if len(temp_result_Se[temp_result_Se > corr_limit]) >= 1:
                            continue
                        else:
                            dic_value[index_code] = accreturn - max_index_loss_limit
                    else:
                        dic_value[index_code] = 0
                else:
                    dic_value[index_code] = 0
            weight = pd.Series(dic_value, name=datestr)
            weight = weight / weight.sum()
            if max_index_loss_limit == 1.0:
                weight = weight * poc_value_limit
                loss_weight = 1 - poc_value_limit
            else:
                loss_weight = 0

            if 'bond' in asset_index:
                for bond_code in list(asset_index['bond'].keys()):
                    weight[bond_code] = loss_weight / len(asset_index['bond'])
            return weight
        elif method == 'fix_rate':
            fix_stock_weight = IndexAllocationParam.get('fix_stock_weight', 0.9)
            fix_bond = 1 - fix_stock_weight

            # total_stock = []
            total_bond = []
            total_other_asset = []
            for col in tempReturnDF.columns.tolist():
                if col not in asset_index['bond']:
                    total_other_asset.append(col)
                    # total_stock.append(col)
                elif col in asset_index['bond']:
                    total_bond.append(col)

            weight = []
            for col in tempReturnDF.columns.tolist():
                if col in total_other_asset:
                    tmw = fix_stock_weight * 1 / len(total_other_asset)
                elif col in total_bond:
                    tmw = fix_bond * 1 / len(total_bond)
                weight.append(tmw)
        else:
            weight = [1 / tempReturnDF.shape[1]] * tempReturnDF.shape[1]
        initX = pd.Series(weight, index=tempReturnDF.columns, name=datestr)
        initX.fillna(0, inplace=True)
        return initX

    def calcMaxdown(self, return_list):
        '''最大回撤率'''
        return_list.fillna(0, inplace=True)
        return_list = (return_list + 1).cumprod()
        return_list = return_list.values
        i = np.argmax(np.maximum.accumulate(return_list) - return_list)
        if i == 0:
            return 0
        j = np.argmax(return_list[:i])
        result = (return_list[j] - return_list[i]) / return_list[j]
        return result

    def adjust_weight_in(self, datestr, adjust_date_list, indexReturnDf, method, back_day_limit, assetIndex,
                         AssetAllocationOptimizationDemo, IndexAllocationParam, weight_list=[]):
        # 调仓日计算权重
        start_date = (datetime.strptime(datestr, "%Y-%m-%d") - timedelta(days=back_day_limit)).strftime("%Y-%m-%d")
        total_his_list = indexReturnDf[indexReturnDf.index < datestr].index.tolist()[-back_day_limit:]
        start_date = total_his_list[-back_day_limit]
        tempReturnDF = indexReturnDf.loc[total_his_list]
        # tempReturnDF = indexReturnDf[(indexReturnDf.index >= start_date) & (indexReturnDf.index < datestr)]
        weight = pd.Series()
        if datestr in adjust_date_list and adjust_date_list.index(datestr) == 0:
            initX = self.distribution_init_weight(assetIndex, tempReturnDF, method, datestr, IndexAllocationParam)
        else:
            if weight_list:
                initX = weight_list[-1]
            else:
                initX = pd.Series()
        weight = AssetAllocationOptimizationDemo.get_smart_weight(tempReturnDF, initX, assetIndex, method,
                                                                  IndexAllocationParam,indexReturnDf[indexReturnDf.index < datestr])
        weight.name = datestr
        if np.isnan(weight.max()):
            self.logger.info('当前%s调仓日,调整后的权重异常或未调仓' % datestr)
            return pd.Series()

        # self.logger.info('当前%s调仓日,调整后的权重%s,值为%s'%(datestr,weight.argmax(),weight.max()))
        return weight

    def stop_loss_method(self, datestr, total_bond, last_weight, every_asset_se, stop_loss_flag='replace_loss'):
        if stop_loss_flag == 'replace_loss':
            # 以固收，替换损失的资产
            temp_se = every_asset_se.sum()
            target_se = temp_se[temp_se < 0]
            dic_data = {}
            for code in last_weight.index.tolist():
                if code in target_se.index.tolist():
                    dic_data[code] = 0
                else:
                    dic_data[code] = last_weight[code]
            bond_dic = {index_name: last_weight.loc[target_se.index.tolist()].sum() / len(total_bond) for index_name in
                        total_bond}
            dic_data.update(bond_dic)
        else:
            dic_data = {index_name: 1 / len(total_bond) for index_name in
                        last_weight.index.tolist() if
                        index_name in total_bond}
            other_dic = {index_name: 0 for index_name in last_weight.index.tolist() if
                         index_name not in total_bond}
            dic_data.update(other_dic)
        weight = pd.Series(dic_data)
        weight.name = datestr
        return weight

    def calcAssetAllocationWithRiskContorl3(self, back_day_limit, adjust_day_limit, indexReturnDf, assetIndex,
                                            method, IndexAllocationParam={}):
        # 需考虑相关性的配置方法
        if method in ['industry_recyle', 'industry_recyle_mean_var_stock', 'industry_recyle_equ']:
            IndexAllocationParam['index_corr'] = indexReturnDf.corr()

        max_loss_limit = -IndexAllocationParam.get("max_loss_limit",0.05)

        adjust_date_loc = list(range(back_day_limit, indexReturnDf.shape[0], adjust_day_limit))
        adjust_date_list = indexReturnDf.iloc[adjust_date_loc].sort_index().index.tolist()
        # 所有调仓日
        total_date_list = indexReturnDf.index.tolist()

        # 仓位控制的低风险产品
        if 'bond' in assetIndex:
            total_bond = [index_name for index_name in indexReturnDf.columns.tolist() if
                          index_name in assetIndex['bond'].keys()]
        else:
            total_bond = []

        weight_list = []
        AssetAllocationOptimizationDemo = AssetAllocationOptimization()
        for datestr in total_date_list:

            if weight_list:
                last_weight = weight_list[-1].copy()
                current_index_return_df = indexReturnDf[last_weight[last_weight > 0].index.tolist()]
                df = current_index_return_df[
                    (current_index_return_df.index >= last_weight.name) & (current_index_return_df.index <= datestr)]
                temp_poc_se = (1 + df).prod() - 1
                stop_loss_list = temp_poc_se[temp_poc_se < max_loss_limit].index.tolist()
                if stop_loss_list:
                    self.logger.info('时间:%s,止损%s' % (datestr, ','.join(stop_loss_list)))
                    minus_weight = last_weight[stop_loss_list].sum()+last_weight[total_bond].sum()
                    last_weight[stop_loss_list] = 0

                    if total_bond:
                        for bond_code in total_bond:
                            last_weight[bond_code] = minus_weight / len(total_bond)
                    last_weight[last_weight < 0.03] = 0
                    last_weight = last_weight / last_weight.sum()
                    weight = last_weight.copy()
                    weight.name = datestr
                    weight_list.append(weight)

            if datestr in adjust_date_list:
                weight = self.adjust_weight_in(datestr, adjust_date_list, indexReturnDf, method, back_day_limit,
                                               assetIndex, AssetAllocationOptimizationDemo, IndexAllocationParam,
                                               weight_list=weight_list)
                if weight.empty:
                    continue

                if weight_list:
                    # 止损日与调仓日相同，以调仓权重为准
                    if weight_list[-1].name == datestr:
                        weight_list[-1] = weight
                    else:
                        weight_list.append(weight)
                else:
                    weight_list.append(weight)
        weightDf = pd.concat(weight_list, axis=1, sort=True).T
        return weightDf

    def calcAssetAllocationWithRiskContorl2(self, back_day_limit, adjust_day_limit, indexReturnDf, assetIndex,
                                            method, IndexAllocationParam={}):
        if method in ['industry_recyle', 'industry_recyle_mean_var_stock', 'industry_recyle_equ']:
            IndexAllocationParam['index_corr'] = indexReturnDf.corr()

        adjust_date_loc = list(range(back_day_limit, indexReturnDf.shape[0], adjust_day_limit))
        adjust_date_list = indexReturnDf.iloc[adjust_date_loc].sort_index().index.tolist()
        # 所有调仓日
        total_date_list = indexReturnDf.index.tolist()

        if 'bond' in assetIndex:
            total_bond = [index_name for index_name in indexReturnDf.columns.tolist() if
                          index_name in assetIndex['bond'].keys()]
        else:
            total_bond = []

        AssetAllocationOptimizationDemo = AssetAllocationOptimization()
        dic_stop_loss = {}
        dic_stop_loss['last_adjust'] = {'last_max_value': 0, 'last_adjust_day': total_date_list[0]}  # 前期高点，对应日期
        dic_stop_loss['adjust_maxdown'] = IndexAllocationParam.get('adjust_maxdown', 0.15)  # 相对高点回撤
        dic_stop_loss['weight'] = []
        dic_stop_loss['cum_portfolio'] = pd.Series()  # 累计的组合收益率序列

        for datestr in total_date_list:
            if dic_stop_loss['weight']:
                # 更新截止到datetr的 累计组合收益率，前期高点与对应日期
                last_weight = dic_stop_loss['weight'][-1]
                temp_index = indexReturnDf[(indexReturnDf.index >= last_weight.name) & (indexReturnDf.index < datestr)]
                if not dic_stop_loss['cum_portfolio'].empty:
                    cum_port_last = dic_stop_loss['cum_portfolio'].index.tolist()[-1]
                    temp_index = temp_index.loc[temp_index.index > cum_port_last]
                every_asset_se = last_weight * temp_index
                temp_se = every_asset_se.sum(axis=1)
                dic_stop_loss['cum_portfolio'] = pd.concat([dic_stop_loss['cum_portfolio'], temp_se], axis=0, sort=True)
                current_value = (1 + dic_stop_loss['cum_portfolio']).prod()

                if current_value >= dic_stop_loss['last_adjust']['last_max_value']:
                    dic_stop_loss['last_adjust'] = {'last_max_value': current_value, 'last_adjust_day': datestr}
                else:
                    # 检查是否满足止损条件
                    if (datetime.strptime(last_weight.name, "%Y-%m-%d") + timedelta(days=2)).strftime(
                            "%Y-%m-%d") < datestr:
                        last_max_value = dic_stop_loss['last_adjust']['last_max_value']
                        if last_max_value > 0:
                            if 1 - current_value / last_max_value >= dic_stop_loss['adjust_maxdown']:
                                self.logger.info("%s止损信号发出，前期高点日期%s，回撤%s" % (
                                    datestr, dic_stop_loss['last_adjust']['last_adjust_day'],
                                    1 - current_value / last_max_value))
                                dic_stop_loss['last_adjust'] = {'last_max_value': current_value,
                                                                'last_adjust_day': datestr}
                                weight = self.stop_loss_method(datestr, total_bond, last_weight, every_asset_se,
                                                               stop_loss_flag='replace_loss')
                                dic_stop_loss['weight'].append(weight)
                                continue

            if datestr in adjust_date_list:
                weight = self.adjust_weight_in(datestr, adjust_date_list, indexReturnDf, method, back_day_limit,
                                               assetIndex,
                                               AssetAllocationOptimizationDemo, IndexAllocationParam,
                                               weight_list=dic_stop_loss['weight'])
                if weight.empty:
                    continue

                if dic_stop_loss['weight']:
                    last_weight = dic_stop_loss['weight'][-1]
                    temp_index = indexReturnDf[
                        (indexReturnDf.index > last_weight.name) & (indexReturnDf.index <= datestr)]
                    if not dic_stop_loss['cum_portfolio'].empty:
                        cum_port_last = dic_stop_loss['cum_portfolio'].index.tolist()[-1]
                        temp_index = temp_index.loc[temp_index.index > cum_port_last]
                    temp_se = (last_weight * temp_index).sum(axis=1)
                    dic_stop_loss['cum_portfolio'] = pd.concat([dic_stop_loss['cum_portfolio'], temp_se], axis=0,
                                                               sort=True)
                dic_stop_loss['weight'].append(weight)

        weightDf = pd.concat(dic_stop_loss['weight'], axis=1, sort=True).T
        return weightDf

    def calcAssetAllocationNotRiskContorl(self, back_day_limit, adjust_day_limit, indexReturnDf, assetIndex, method,
                                          IndexAllocationParam={}):
        adjust_date_loc = list(range(back_day_limit, indexReturnDf.shape[0], adjust_day_limit))
        adjust_date_list = indexReturnDf.iloc[adjust_date_loc].sort_index().index.tolist()
        AssetAllocationOptimizationDemo = AssetAllocationOptimization()
        weight_list = []
        if method in ['industry_recyle', 'recyle_full', 'industry_recyle_stock', 'industry_recyle_mean_var_stock',
                      'industry_recyle_equ']:
            IndexAllocationParam['index_corr'] = indexReturnDf.corr()
        for datestr in adjust_date_list:
            weight = self.adjust_weight_in(datestr, adjust_date_list, indexReturnDf, method, back_day_limit,
                                           assetIndex, AssetAllocationOptimizationDemo, IndexAllocationParam,
                                           weight_list)
            if weight.empty:
                continue
            weight_list.append(weight)
        if weight_list:
            weightDf = pd.concat(weight_list, axis=1).T
        else:
            weightDf = pd.DataFrame()
        self.logger.info("回测完成！")
        return weightDf

    def calcAssetAllocation(self, method, IndexAllocationParam={}, indexReturnDf=pd.DataFrame(), assetIndex={},
                            risk_control=False):
        self.logger.info("------------------IndexAllocationParam------------------------->")
        self.logger.info(IndexAllocationParam)
        self.logger.info("------------------assetIndex------------------------->")
        self.logger.info(assetIndex)

        adjust_day_limit = int(IndexAllocationParam.get("adjust_day_limit", 5))
        back_day_limit = int(IndexAllocationParam.get("back_day_limit", adjust_day_limit))

        self.logger.info("回测大类资产配置")
        if risk_control:
            self.logger.info("运行有风控逻辑算法...")
            weightDf = self.calcAssetAllocationWithRiskContorl3(back_day_limit, adjust_day_limit, indexReturnDf,
                                                                assetIndex, method,
                                                                IndexAllocationParam=IndexAllocationParam)
        else:
            self.logger.info("运行无风控逻辑算法...")
            weightDf = self.calcAssetAllocationNotRiskContorl(back_day_limit, adjust_day_limit, indexReturnDf,
                                                              assetIndex, method,
                                                              IndexAllocationParam=IndexAllocationParam)
        if not weightDf.empty:
            totalPofolio, equalPofolio = self.calc_total_portfolio(indexReturnDf, weightDf)
        else:
            return pd.Series(), weightDf, pd.Series()
        weightDf = self.adjust_weight_df(weightDf)
        return totalPofolio, weightDf, equalPofolio

    def adjust_weight_df(self, weightDf):
        weightDf[weightDf <= 0.01] = 0
        df_list = []
        for datestr in weightDf.index.tolist():
            tempSe = weightDf.loc[datestr]
            # tempSe = tempSe/tempSe.sum()
            tempSe.name = datestr
            df_list.append(tempSe)

        weightDf = pd.concat(df_list, axis=1, sort=True).T
        return weightDf

    def calc_total_portfolio(self, indexReturnDf, weight_df):
        total_date_poc = weight_df.index.tolist()
        useful_index_df = indexReturnDf.loc[total_date_poc[0]:]

        total_date_list = useful_index_df.index.tolist()
        total_money = 1
        equalWeightMoney = 1
        se_list = []
        equalt_se_list = []
        for poc_date in total_date_poc:
            if total_date_list.index(poc_date) != len(total_date_list) - 1:
                start_date = total_date_list[total_date_list.index(poc_date) + 1]
            else:
                break
            if poc_date != total_date_poc[-1]:
                next_poc_date = total_date_poc[total_date_poc.index(poc_date) + 1]
                temp_df = useful_index_df.loc[start_date:next_poc_date]
            else:
                temp_df = useful_index_df.loc[start_date:]
            portfolio_se = (weight_df.loc[poc_date] * temp_df).sum(axis=1)
            total_money = total_money * (1 + portfolio_se).prod()
            se_list.append(portfolio_se)

            tempEqualPorfolio = (np.array(
                [1 / weight_df.shape[1]] * weight_df.shape[1]) * temp_df).sum(axis=1)
            equalWeightMoney = equalWeightMoney * (1 + tempEqualPorfolio).prod()
            equalt_se_list.append(tempEqualPorfolio)

        result_se = pd.concat(se_list, axis=0, sort=True)
        equal_se = pd.concat(equalt_se_list, axis=0, sort=True)
        return result_se, equal_se
