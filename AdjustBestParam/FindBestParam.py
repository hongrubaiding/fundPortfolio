# -- coding: utf-8 --

'''
寻找最优参数
'''

import pandas as pd
from AssetAllocation.AssetAllocationMain import AssetAllocationMain
import mylog as mylog
from fundSelect.SetPortfolio import SetPortfolio
import numpy as np
from GetAndSaveWindData.GetDataTotalMain import GetDataTotalMain
from AssetAllocation.CalcAssetAllocation import CalcAssetAllocation
from hyperopt import fmin, tpe, hp, space_eval, rand, Trials, partial, STATUS_OK
from datetime import datetime,timedelta
import time


class FindBestParam:
    def __init__(self, method, param_file_name=''):
        self.logger = mylog.set_log(method)
        # self.logger = logdemo.set_logger(method+'.log')
        self.method = method
        if not param_file_name:
            self.param_file_name = self.method
        else:
            self.param_file_name = param_file_name
        self.save_dic = {}

    def getAssetIndexData(self, assetIndex):
        GetDataTotalMainDemo = GetDataTotalMain(data_resource='wind')
        total_index_code = [list(dic.keys()) for style, dic in assetIndex.items()]
        df_list = []
        for asset_style, dic in assetIndex.items():
            for code in list(dic.keys()):
                index_df = GetDataTotalMainDemo.get_hq_data(code, start_date=self.startDate,
                                                            end_date=self.endDate, code_style='index')
                index_df.rename(columns={"close_price": code}, inplace=True)
                df_list.append(index_df)
        index_data_df = pd.concat(df_list, axis=1, sort=True)
        index_data_df.fillna(method='pad', inplace=True)
        # 收益率序列
        indexReturnDf = (index_data_df - index_data_df.shift(1)) / index_data_df.shift(1)
        return indexReturnDf

    def find_param_self(self, asset_index={}, control_method={}):
        # self.AssetAllocationMainDemo = AssetAllocationMain()
        self.AssetAllocationMainDemo = AssetAllocationMain()
        self.CalcAssetAllocationDemo = CalcAssetAllocation()
        if not asset_index:
            self.assetIndex = self.AssetAllocationMainDemo.getParam(self.method)
        else:
            self.assetIndex = asset_index

        if control_method:
            self.control_method = control_method['control']
        else:
            self.control_method = ''

        # self.startDate = '2015-09-01'
        # self.endDate = (datetime.today() - timedelta(days=5)).strftime('%Y-%m-%d')

        self.startDate = '2010-01-01'
        self.endDate = '2018-01-01'


        self.indexReturnDf = self.getAssetIndexData(self.assetIndex)
        self.dic_product = {}

    def getPortfolioWeightDf(self, IndexWeightDf, dicResult, resultDf):
        # usefulNetDf = resultDf.dropna(axis=0)
        usefulNetDf =resultDf.copy()
        timeList = usefulNetDf.index.tolist()

        # 找到第一个持仓日
        totalDate = IndexWeightDf.index.tolist()
        for assetDate in totalDate:
            if assetDate >= timeList[0]:
                if assetDate != timeList[0]:
                    if totalDate.index(assetDate) != 0:
                        assetPreDate = totalDate.index(assetDate) - 1
                        usefulIndexWeightDf = IndexWeightDf.iloc[assetPreDate:]
                    else:
                        usefulIndexWeightDf = IndexWeightDf
                else:
                    usefulIndexWeightDf = IndexWeightDf.loc[assetDate:]
                break
        else:
            self.logger.info('可用净值日期最小值，大于大类资产可用日期，请检查 ')
            return

        adjustDateList = usefulIndexWeightDf.index.tolist()  # 调仓日
        positionList = []
        for adjustDate in adjustDateList:
            fundWeightDic = {}
            tempDicIndexWeight = usefulIndexWeightDf.loc[adjustDate].to_dict()
            for indexCode in tempDicIndexWeight:
                fundWeightDic.update(
                    self.getFundWeight(tempDicIndexWeight[indexCode], dicResult[indexCode]))  # 大类的权重分配到产品中
            tempDf = pd.DataFrame(fundWeightDic, index=[adjustDate])
            positionList.append(tempDf)
        positionDf = pd.concat(positionList, axis=0)  # 调仓周期内各资产权重
        return positionDf, usefulNetDf

    # 大类权重分配到具体产品
    def getFundWeight(self, assetWeight, fundCodeList, flag='equal'):
        dicResult = {}
        if flag == 'equal':
            dicResult = {code: assetWeight / len(fundCodeList) for code in fundCodeList}
        return dicResult

    # 回测投资组合状况
    def backPofolio(self, positionDf, usefulNetDf):
        usefulNetReturnDf = (usefulNetDf - usefulNetDf.shift(1)) / usefulNetDf.shift(1)
        usefulNetReturnDf.fillna(0, inplace=True)

        portfolioBackList = []
        positionDateList = positionDf.index.tolist()
        for dateNum in range(len(positionDateList) - 1):
            if dateNum == 0:
                startDate = usefulNetDf.index[0]
            else:
                startDate = positionDateList[dateNum]

            tempNetReturnDf = usefulNetReturnDf.loc[startDate:positionDateList[dateNum + 1]]
            tempPorfolioReturn = (tempNetReturnDf * positionDf.loc[positionDateList[dateNum]]).sum(axis=1)

            if dateNum == 0:
                portfolioBackList.append(tempPorfolioReturn)
            else:
                portfolioBackList.append(tempPorfolioReturn[1:])
        portfolioSe = pd.concat(portfolioBackList, axis=0)
        if usefulNetDf.index.tolist()[-1] > portfolioSe.index.tolist()[-1]:
            startDate = positionDateList[-1]
            tempNetReturnDf = usefulNetReturnDf.loc[startDate:]
            tempPorfolioReturn = (tempNetReturnDf * positionDf.loc[positionDateList[-1]]).sum(axis=1)
            portfolioSe = pd.concat([portfolioSe,tempPorfolioReturn],axis=0)
        portfolioSe.name = u'基金投资组合'
        return portfolioSe

    def get_space_value(self):
        space = {}
        method = self.method
        if method in ['mean_var', 'risk_parity', 'risk_parity_self']:
            space = {"back_day_limit": hp.randint("back_day_limit", 50, 400),
                     "adjust_day_limit": hp.randint("adjust_day_limit", 10, 90)}
            if 'bond' in self.assetIndex:
                space.update({"bond_limit": hp.uniform("bond_limit", 0.05, 0.9)})
            if 'commodity' in self.assetIndex:
                space.update({"com_limit": hp.uniform("com_limit", 0.05, 0.9), })

            if self.control_method and self.control_method == 'xfc':
                space.update({"xfc_back_day": hp.randint("xfc_back_day", 20, 90)})
                space.update({"xfc_chage_rate": hp.uniform("xfc_chage_rate", 0.01, 2.50)})

        elif method == 'recyle':
            space = {"adjust_day_limit": hp.randint("adjust_day_limit", 3, 60),
                     "back_day_limit": hp.randint("back_day_limit", 3, 60),
                     "adjust_maxdown": hp.uniform("adjust_maxdown", 0.001, 0.4),
                     "max_index_value_limit": hp.uniform("max_index_value_limit", 0.001, 0.4),
                     "rolloing_date_num": hp.randint("rolloing_date_num", 5, 50),
                     "adjust_limit_day": hp.randint("adjust_limit_day", 3, 20)
                     }
        elif method == 'fix_rate':
            space = {"adjust_day_limit": hp.randint("adjust_day_limit", 10, 60),
                     "back_day_limit": hp.randint("back_day_limit", 10, 150),
                     "fix_stock_weight": hp.uniform("fix_stock_weight", 0.6, 0.9),
                     "fix_stock_zf": hp.uniform("fix_stock_zf", 0.1, 0.8),
                     }
        elif method=="recyle_update":
            space = {
                    "adjust_day_limit": hp.randint("adjust_day_limit", 2, 15),
                     "back_day_limit": hp.randint("back_day_limit", 3, 40),
                     "max_index_loss_limit": hp.uniform("max_index_loss_limit", 1, 1.20),
                     "poc_value_limit": hp.uniform("poc_value_limit", 0, 0.9),
                     # "max_index_value_limit": hp.uniform("max_index_value_limit", 0.001, 0.4),
                     }
        elif method=='industry_recyle':
            # old
            # space = {
            #     "adjust_day_limit": hp.randint("adjust_day_limit", 4, 10),
            #     "back_day_limit": hp.randint("back_day_limit", 3, 40),
            #     "max_index_loss_limit": hp.uniform("max_index_loss_limit", 1, 1.30),
            #     "poc_value_limit": hp.uniform("poc_value_limit", 0.1, 0.9),
            #     # "adjust_maxdown":hp.uniform("adjust_maxdown",0.05,0.20)
            #     # "max_index_value_limit": hp.uniform("max_index_value_limit", 0.001, 0.4),
            # }
            space={
                # "adjust_day_limit": hp.randint("adjust_day_limit", 4, 10),
                "back_day_limit": hp.randint("back_day_limit", 5, 30),
                "max_loss_limit" : hp.uniform("poc_value_limit", 0.03, 0.15),
                "corr_limit": hp.uniform("corr_limit", 0.80, 0.99),
                "up_max": hp.uniform("up_max", 0.1, 0.9),
                "up_day_num":hp.uniform("up_day_num", 0.1, 0.9),
                "down_max_num":hp.uniform("down_max_num", 0.1, 0.9),
                "judge_market": hp.randint("judge_market", 5, 60),
                "vol_rate": hp.uniform("vol_rate", 0.1, 0.9),
                "conti_up_day": hp.uniform("conti_up_day", 0.1, 0.9),
            }
        elif method=='industry_recyle_stock':
            space = {
                "adjust_day_limit": hp.randint("adjust_day_limit", 10, 50),
                "back_day_limit": hp.randint("back_day_limit", 10, 50),
            }
        elif method=='industry_recyle_mean_var_stock':
            space = {
                "adjust_day_limit": hp.randint("adjust_day_limit", 4, 10),
                "back_day_limit": hp.randint("back_day_limit", 20, 250),
            }
            # space.update({"xfc_back_day": hp.randint("xfc_back_day", 20, 90)})
            # space.update({"xfc_chage_rate": hp.uniform("xfc_chage_rate", 0.01, 2.50)})
        elif method == 'mean_var_self':
            space.update({"xfc_back_day": hp.randint("xfc_back_day", 20, 90)})
            space.update({"xfc_chage_rate": hp.uniform("xfc_chage_rate", 0.01, 2.50)})
        elif method=='recyle_full':
            space = {
                "adjust_day_limit": hp.randint("adjust_day_limit", 3, 20),
                "back_day_limit": hp.randint("back_day_limit", 3, 60),
                # "max_index_loss_limit": hp.uniform("max_index_loss_limit", 1, 1.30),
                # "poc_value_limit": hp.uniform("poc_value_limit", 0.4, 0.9),
                # "max_index_value_limit": hp.uniform("max_index_value_limit", 0.001, 0.4),
            }
        elif method=='industry_recyle_equ':
            space = {
                "adjust_day_limit": hp.randint("adjust_day_limit", 3, 10),
                "back_day_limit": hp.randint("back_day_limit", 3, 15),
                "poc_num": hp.randint("poc_num", 3,8),
            }
        return space

    def try_find_param(self, asset_index={}, control_method={},product_name_dic={},target='maxreturn'):
        self.start_time =time.time()
        self.product_name_dic = product_name_dic
        self.target = target
        self.find_param_self(asset_index, control_method)
        space = self.get_space_value()
        if not space:
            self.logger.error("获取space值失败，请检查")
            return

        algo = partial(tpe.suggest, n_startup_jobs=1)  # 定义随机搜索算法。搜索算法本身也有内置的参数决定如何去优化目标函数
        trials = Trials()
        best = fmin(self.find_param_main, space, algo=algo, max_evals=5000, trials=trials)  # 对定义的参数范围，调用搜索算法，对模型进行搜索
        result_se = pd.Series(trials.best_trial)
        result_se.name = self.method
        result_se.to_excel("%s最优参数.xlsx" % self.param_file_name)
        self.logger.info(best)

    def getProductResult(self, assetIndex, IndexWeightDf, totalPofolio,dic_product, file_str, result_path=''):
        # 投资组合绘图与风险指标计算
        # self.logger.info('生成目标基金产品池...... ')
        SetPortfolioDemo = SetPortfolio(assetIndex=assetIndex)
        total_date_list = IndexWeightDf.index.tolist()
        if not self.dic_product:
            dicResult, resultDf = SetPortfolioDemo.get_asset_fund(start_date=total_date_list[0],
                                                                  end_date=totalPofolio.index.tolist()[-1],product_name_dic=self.product_name_dic)
            dic_product['dicResult'] = dicResult
            dic_product['resultDf'] = resultDf
            self.dic_product = dic_product

        positionDf, usefulNetDf = self.getPortfolioWeightDf(IndexWeightDf, self.dic_product['dicResult'],
                                                            self.dic_product['resultDf'])

        portfolioSe = self.backPofolio(positionDf, usefulNetDf)
        if result_path:
            portfolioSe.to_excel(result_path + "\\" + file_str)
        return portfolioSe

    def find_param_main(self, argsDict):
        self.logger.info("%s调参" % self.param_file_name)
        # target_date = '2015-09-01'
        target_date = self.startDate
        file_str = ''
        for key, value in argsDict.items():
            file_str = file_str + key + ":" + str(np.round(value, 4))+','

        self.logger.info(file_str)
        risk_control = True
        if self.method == 'recyle':
            risk_control = True
        elif self.method == 'mean_var_self':
            self.method = 'mean_var'
        elif self.method == 'risk_parity_self':
            self.method = 'risk_parity'
        elif self.method=='industry_recyle_stock':
            risk_control = False
        elif self.method=='industry_recyle_mean_var_stock':
            risk_control = False

        if 'xfc_chage_rate' in argsDict:
            risk_control = True
            argsDict['control_method'] = 'xfc'

        # self.logger.info(self.assetIndex)
        # try:
        totalPofolio, IndexWeightDf, _ = self.CalcAssetAllocationDemo.calcAssetAllocation(self.method,
                                                                               IndexAllocationParam=argsDict,
                                                                               indexReturnDf=self.indexReturnDf,
                                                                               assetIndex=self.assetIndex,
                                                                               risk_control=risk_control)
        # self.logger.info('大类资产配置模型初始化完成！')
        if IndexWeightDf.empty:
            self.logger.info("当前参数下权重异常，跳过本次优化")
            return np.inf
        product_flag = False

        if product_flag:
            IndexWeightDf = IndexWeightDf[IndexWeightDf.index >= target_date]
            tempSe = self.getProductResult(self.assetIndex, IndexWeightDf, totalPofolio,self.dic_product, file_str='', result_path='')
        else:
            tempSe = totalPofolio[totalPofolio.index>=target_date]
        result = (1+tempSe).prod()
        self.logger.info('开始时间%s,截止时间%s' % (tempSe.index.tolist()[0],tempSe.index.tolist()[-1]))
        if self.target == 'maxreturn':
            self.logger.info('目标产品池回测完成！ 最优累计收益%s' % result)
        else:
            annual_return = result**(252/len(tempSe))-1
            annual_std = tempSe.std()*np.sqrt(252)
            result = (annual_return-0.02)/annual_std
            self.logger.info('目标产品池回测完成！ 最优夏普比率%s' % result)
        self.save_dic[file_str] = result
        if time.time() - self.start_time>=60:
            self.start_time = time.time()
            pd.Series(self.save_dic,name='中间运行结果').to_excel('行业短周期中间运行结果.xlsx')
        # except:
        #     result = np.inf
        return -result


if __name__ == '__main__':
    # FindBestParamDemo = FindBestParam(method='mean_var_self')
    FindBestParamDemo = FindBestParam(method='recyle_update')
    # asset_index = {'commodity': {'AU9999.SGE': u'黄金9999', 'SPSIOP.SPI': "标普石油天然气指数"},
    #                'stock': {'000300.SH': u'沪深300', '000905.SH': u'中证500', '000852.SH': "中证1000"},
    #                'bond': {'H00140.SH': u'上证五年期国债指数'}}
    # asset_index = {'commodity': {'AU9999.SGE': '黄金9999', 'SPSIOP.SPI': '标普石油天然气指数'},
    #                'stock': {'000300.SH': '沪深300', '000905.SH': '中证500', '000852.SH': '中证1000'},
    #                'bond': {'H00140.SH': '上证五年期国债指数'}}

    asset_index = {'commodity': {'AU9999.SGE': u'黄金9999', 'SPSIOP.SPI': "标普石油天然气指数"},
                   'stock': {'HSI.HI': '恒生指数', 'SPX.GI': '标普500', '000300.SH': u'沪深300', '000905.SH': u'中证500',
                             '000852.SH': "中证1000"}, 'bond': {'H00140.SH': u'上证五年期国债指数'}}
    control_method={'control':'xfc'}

    FindBestParamDemo.try_find_param(asset_index=asset_index)
