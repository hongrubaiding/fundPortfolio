# -- coding: utf-8 --

'''
    大类资产配研究，基于卖方研报的优化改进
'''

import pandas as pd
import numpy as np
from AssetAllocation.AssetAllocationOptimization import AssetAllocationOptimization
import matplotlib
from datetime import date,datetime,timedelta
from GetAndSaveWindData.GetDataTotalMain import GetDataTotalMain
import mylog as mylog
from AssetAllocation.CalcAssetAllocation import CalcAssetAllocation

matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['axes.unicode_minus'] = False


class AssetAllocationMain:
    def __init__(self):
        self.plotFlag = False  # 是否绘图
        self.logger = mylog.set_log()

    def getParam(self, method='mean_var'):
        # 获取初始参数
        assetIndex = {}  # 大类资产指数
        if method == 'fix_rate':
            assetIndex['stock'] = {'000300.SH': u'沪深300', '000905.SH': u'中证500', "000852.SH": "中证1000"}
            # assetIndex['stock'] = {'000300.SH': u'沪深300'}
            assetIndex['bond'] = {'H00140.SH': u'上证五年期国债指数'}
        elif method == 'recyle':
            assetIndex['stock'] = {'000300.SH': u'沪深300', '000905.SH': u'中证500', "000852.SH": "中证1000"}
            # assetIndex['stock'] = {'000300.SH': u'沪深300'}
            assetIndex['bond'] = {'H00140.SH': u'上证五年期国债指数'}
            # assetIndex['commodity'] = {'AU9999.SGE': u'黄金9999'}

        else:
            assetIndex['stock'] = {'000300.SH': u'沪深300', '000905.SH': u'中证500', 'HSI.HI': '恒生指数', 'SPX.GI': '标普500'}
            assetIndex['bond'] = {'H00140.SH': u'上证五年期国债指数'}
            assetIndex['commodity'] = {'AU9999.SGE': u'黄金9999', 'SPSIOP.SPI': "标普石油天然气指数"}
        return assetIndex

    def getAssetIndexData(self,startDate,endDate):
        df_list = []
        GetDataTotalMainDemo = GetDataTotalMain(data_resource='wind')
        for asset_style, dic in self.assetIndex.items():
            for code in list(dic.keys()):
                index_df = GetDataTotalMainDemo.get_hq_data(code, start_date=startDate, end_date=endDate,
                                                            code_style='index')
                index_df.rename(columns={"close_price": code}, inplace=True)
                df_list.append(index_df)
        index_data_df = pd.concat(df_list, axis=1, sort=True)

        # if '000300.SH' not in index_data_df:
        #     bench_df = GetDataTotalMainDemo.get_hq_data('000300.SH', start_date=startDate, end_date=endDate,
        #                                                 code_style='index')
        #     bench_df.rename(columns={"close_price": '000300.SH'}, inplace=True)
        #     index_data_df = pd.concat([index_data_df,bench_df],axis=1,sort=True)
        index_data_df.fillna(method='pad', inplace=True)

        # 收益率序列
        indexReturnDf = (index_data_df - index_data_df.shift(1)) / index_data_df.shift(1)
        self.indexReturnDf = indexReturnDf
        return indexReturnDf

    def get_best_param(self, method):
        param_dic = {}
        if method == 'mean_var':
            param_dic = {'adjust_day_limit': 87, 'back_day_limit': 172, 'bond_limit': 0.010616510925441365,
                         'com_limit': 0.7860539304546363}
        elif method == 'risk_parity':
            param_dic={'adjust_day_limit': 10, 'back_day_limit': 33, 'bond_limit': 0.82550849050036, 'com_limit': 0.2151398996281533}
            # param_dic = {'adjust_day_limit': 40, 'back_day_limit': 50, 'bond_limit': 0.010969236016368823,
            #              'com_limit': 0.5481534375873586}
        elif method == 'fix_rate':
            param_dic = {'adjust_day_limit': 13, 'back_day_limit': 12, 'fix_stock_weight': 0.5208520751888874,
                         'fix_stock_zf': 0.7708961619778893}
        elif method == 'recyle':
            # param_dic = {'adjust_day_limit': 57, 'adjust_maxdown': 0.1837216808980371, 'back_day_limit': 116,
            #  'max_index_value_limit': 0.14759992099232416}
            # param_dic={'adjust_day_limit': 13, 'adjust_maxdown': 0.14985207050237745, 'back_day_limit': 81,'rolloing_date_num':10,
            #  'max_index_value_limit': 0.01803163980221814}
            # param_dic = {'adjust_day_limit': 24, 'adjust_limit_day': 19, 'adjust_maxdown': 0.37094824727718684,
            #              'back_day_limit': 99, 'max_index_value_limit': 0.0018198718505196155, 'rolloing_date_num': 32}
            param_dic={'adjust_day_limit': 24, 'adjust_limit_day': 9, 'adjust_maxdown': 0.3554704778203696, 'back_day_limit': 123,
             'max_index_value_limit': 0.010098416882222521, 'rolloing_date_num': 32}

        return param_dic

    def calcMain(self, startDate,endDate,method='mean_var',asset_index={},best_param_dic={}):
        # 主函数入口
        if not asset_index:
            # 未指定大类资产时，采用默认参数
            self.assetIndex = self.getParam(method)
        else:
            self.assetIndex =asset_index

        self.logger.info("---------------------asset_index------------------>")
        self.logger.info(self.assetIndex)

        if not best_param_dic:
            # 未指定优化参数，采用默认参数
            model_param = self.get_best_param(method)
        else:
            model_param = best_param_dic
        indexReturnDf = self.getAssetIndexData(startDate=startDate,endDate=endDate)

        self.logger.info("---------------------model_param------------------>")
        self.logger.info(model_param)

        CalcAssetAllocationDemo = CalcAssetAllocation()

        # 默认是否风控
        risk_control = False
        if method in ['recyle','industry_recyle']:
            risk_control = True
        elif 'xfc_chage_rate' in model_param:
            risk_control =True
            model_param['control_method'] = 'xfc'
        totalPofolio, weightDf, equalPortfolio = CalcAssetAllocationDemo.calcAssetAllocation(method, model_param,
                                                                                             indexReturnDf,
                                                                                             self.assetIndex,
                                                                                             risk_control=risk_control)
        return totalPofolio, weightDf, equalPortfolio


if __name__ == '__main__':
    AssetAllocationDemo = AssetAllocationMain()
    AssetAllocationDemo.calcMain()
