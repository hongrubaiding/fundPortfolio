# -- coding: utf-8 --

'''
    代销公募基金基本信息和净值数据
'''

import pandas as pd
from datetime import datetime, date
import numpy as np
import mylog as mylog
from GetAndSaveWindData.GetDataTotalMain import GetDataTotalMain


class SetPortfolio:
    def __init__(self, assetIndex={}, ):
        self.assetIndex = assetIndex  # 大类资产指数
        self.logger = mylog.set_log()

    def get_fund(self, fund_type='ETF'):
        total_fund_df = pd.read_excel('被动指数型基金.xlsx')
        dic_asset_df = {}
        for bench_code, temp_df in total_fund_df.groupby(by='跟踪指数代码'):
            if bench_code in self.assetIndex['stock']:
                if fund_type == 'ETF':
                    dic_asset_df[bench_code] = temp_df

    # 再次处理基金池,返回大类对应的产品和基金净值数据
    def secondSelect(self, start_date, end_date, product_name_dic={},fund_type='ETF'):
        if not product_name_dic:
            dicResult = {}
            if fund_type=='ETF':
                dicResult['000300.SH'] = {"510300.SH": "300ETF"}
                dicResult['000905.SH'] = {"510500.SH": "500ETF"}
                dicResult['SPX.GI'] = {"513500.SH": "标普500"}
                dicResult['HSI.HI'] = {"159920.SZ": "恒生ETF"}
                dicResult['SPSIOP.SPI'] = {"162411.SZ": "华宝油气"}
                dicResult['AU9999.SGE'] = {'518800.SH': "黄金ETF"}
                dicResult['H00140.SH'] = {'511010.SH': "国债ETF "}
                dicResult['000852.SH'] = {'512100.SH': "1000ETF "}
            else:
                # dicResult['000300.SH'] = {"002987.OF": "广发沪深300ETF联接C"}
                dicResult['000300.SH'] = {"161207.OF": "国投瑞银瑞和沪深300指数"}
                # dicResult['000905.SH'] = {"002903.OF": "广发中证500ETF联接C类"}
                dicResult['000905.SH'] = {"006087.OF": "华泰柏瑞中证500ETF联接C"}
                dicResult['SPX.GI'] = {"050025.OF": "博时标普500ETF联接A"}
                dicResult['HSI.HI'] = {"000071.OF": "华夏恒生ETF联接A"}
                dicResult['SPSIOP.SPI'] = {"007844.OF": "华宝标普油气C人民币"}
                dicResult['AU9999.SGE'] = {'002610.OF': "博时黄金ETF联接A"}
                dicResult['H00140.SH'] = {'160602.OF': "鹏华普天债券A "}
                dicResult['000852.SH'] = {'006487.OF': "广发中证1000C "}
                dicResult['000906.SH'] = {'001588.OF':'天弘中证800A'}
                dicResult['399006.SZ'] = {'110026.OF': '易方达创业板ETF联接A'}
                dicResult['399005.SZ'] = {'161118.OF': '易方达中小板'}
        else:
            dicResult = product_name_dic

        total_fund_list = []
        for asset, dic in self.assetIndex.items():
            for index, index_name in dic.items():
                total_fund_list = total_fund_list + list(dicResult[index].keys())

        GetDataTotalMainDemo = GetDataTotalMain(data_resource='wind')

        df_list = []
        if fund_type=='ETF':
            for code in total_fund_list:
                temp_df = GetDataTotalMainDemo.get_hq_data(code, start_date=start_date, end_date=end_date,
                                                           code_style='etf_fund')
                temp_df.rename(columns={"close_price": code}, inplace=True)
                df_list.append(temp_df)
        else:
            for code in total_fund_list:
                temp_df = GetDataTotalMainDemo.get_hq_data(code, start_date=start_date, end_date=end_date,
                                                           code_style='fund',name_list=['net_value_adj'])
                temp_df.rename(columns={"net_value_adj": code}, inplace=True)
                df_list.append(temp_df)
        result_df = pd.concat(df_list, axis=1, sort=True)
        return dicResult, result_df

    def get_asset_fund(self, start_date='2019-01-01', end_date='2019-02-01', product_name_dic={},fund_type='ETF'):
        dicResult, result_df = self.secondSelect(start_date, end_date, product_name_dic,fund_type)
        return dicResult, result_df


if __name__ == '__main__':
    asset_index = {'stock': {'000018.SH': '180金融', '000038.SH': '上证金融', '000036.SH': '上证消费', '000037.SH': '上证医药',
                             '000928.SH': '中证能源', '000932.SH': '中证消费', '000933.SH': '中证医药', '000934.SH': '中证金融',
                             '000914.SH': '300金融', '000913.SH': '300医药', '000989.SH': '全指可选', 'H30021.CSI': '800食品',
                             'H30255.CSI': '500医药', '000991.SH': '全指医药', '000993.SH': '全指信息', '000992.SH': '全指金融',
                             'H30252.CSI': '500工业', 'H30251.CSI': '500原料', '000986.SH': '全指能源', '000987.SH': '全指材料',
                             'H30257.CSI': '500信息', '000990.SH': '全指消费', '399975.SZ': '证券公司', '000988.SH': '全指工业',
                             '399986.SZ': '中证银行', 'H30191.CSI': '有色金属', 'H30165.CSI': '房地产', 'H30184.CSI': '半导体',
                             '931160.CSI': '通信设备', '399998.SZ': '中证煤炭', '930606.CSI': '中证钢铁', '930697.CSI': '家用电器'},
                   'bond': {'H00140.SH': '上证五年期国债指数'}}
    SetPortfolioDemo = SetPortfolio(assetIndex=asset_index)
    SetPortfolioDemo.get_fund()
