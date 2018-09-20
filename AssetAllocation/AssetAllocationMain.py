# -- coding: utf-8 --

'''
    大类资产配置：基于20170725-光大证券-光大证券FOF专题系列报告之三：量化资产配置与FOF投资
'''

import pandas as pd
import numpy as np
from WindPy import w
from datetime import datetime
# from AssetAllocation.IndexAllocation import get_smart_weight
import AssetAllocation.IndexAllocation as IA

class AssetAllocationMain:
    def __init__(self):
        self.assetIndex = self.getParam()
        self.startDate = '2016-01-01'
        self.endDate = '2017-06-01'  # datetime.today()

    def getParam(self):
        # 获取初始参数
        assetIndex = {}  # 大类资产指数
        assetIndex['000016.SH'] = u'上证50'
        assetIndex['000300.SH'] = u'沪深300'
        assetIndex['000905.SH'] = u'中证500'
        assetIndex['SPX.GI'] = u'标普500'
        assetIndex['CBA00601.CS'] = u'中债国债总财富指数'
        assetIndex['AU9999.SGE'] = u'黄金9999'
        return assetIndex

    def getHisData(self):
        # 本地或wind获取大类资产历史数据
        try:
            indexDataDf = pd.read_excel('indexDataDf.xlsx')
            print('本地读取indexDataDf')
            return indexDataDf
        except:
            print('wind读取indexDataDf')
            w.start()
            indexData = w.wsd(codes=list(self.assetIndex.keys()), fields=['close'], beginTime=self.startDate,
                              endTime=self.endDate)
            if indexData.ErrorCode != 0:
                print('wind获取指数数据失败，错误代码：', indexData.ErrorCode)
                return

            indexDataDf = pd.DataFrame(indexData.Data, index=indexData.Codes, columns=indexData.Times).T
            writer = pd.ExcelWriter('indexDataDf.xlsx')
            indexDataDf.to_excel(writer)
            writer.save()



    def calcMain(self):
        indexDataDf = self.getHisData()


if __name__ == '__main__':
    AssetAllocationDemo = AssetAllocationMain()
    AssetAllocationDemo.calcMain()
