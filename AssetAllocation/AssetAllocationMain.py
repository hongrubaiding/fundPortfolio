# -- coding: utf-8 --

'''
    大类资产配研究，基于卖方研报的优化改进
'''

import pandas as pd
import numpy as np
import AssetAllocation.IndexAllocation as IA
import matplotlib
from PrintInfo import PrintInfo
from AssetAllocation.GetIndexData import GetIndexData

matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['axes.unicode_minus'] = False


class AssetAllocationMain:
    def __init__(self):
        self.startDate = '2006-01-01'
        self.endDate = '2017-06-01'  # 回测截止时间

        self.plotFlag = False  # 是否绘图
        self.PrintInfoDemo = PrintInfo()  # 日志信息模块

    def getParam(self):
        # 获取初始参数
        assetIndex = {}  # 大类资产指数
        assetIndex['000016.SH'] = u'上证50'
        assetIndex['000300.SH'] = u'沪深300'
        assetIndex['000905.SH'] = u'中证500'
        # assetIndex['SPX.GI'] = u'标普500'
        assetIndex['CBA00601.CS'] = u'中债国债总财富指数'
        assetIndex['AU9999.SGE'] = u'黄金9999'
        return assetIndex

    # 回测资产配置
    def calcAssetAllocation(self,method,IndexAllocationParam={}):
        pofolioList = []  # 组合业绩表现
        weightList = []  # 组合各时间持仓
        self.PrintInfoDemo.PrintLog(infostr='回测大类资产配置组合...... ')
        for k in range(250, self.indexReturnDf.shape[0], 21):
            datestr = self.indexReturnDf.index.tolist()[k]
            # self.PrintInfoDemo.PrintLog(infostr='回测当前日期： ',otherInfo=datestr)
            tempReturnDF = self.indexReturnDf.iloc[k - 250:k]

            if k==250:
                initWeight = [1/tempReturnDF.shape[1]]*tempReturnDF.shape[1]
                initX = pd.Series(initWeight,index=tempReturnDF.columns)
            else:
                initX = weight

            if IndexAllocationParam:
                allocationParam = IndexAllocationParam['AllocationParam']
                weight = IA.get_smart_weight(returnDf=tempReturnDF, method=method,initX=initX ,wts_adjusted=False,allocationParam=allocationParam)
            else:
                weight = IA.get_smart_weight(returnDf=tempReturnDF, method=method,initX=initX, wts_adjusted=False)
            tempPorfolio = (weight * self.indexReturnDf.iloc[k:k + 21]).sum(axis=1)
            weight.name = datestr

            pofolioList.append(tempPorfolio)
            weightList.append(weight)
        totalPofolio = pd.concat(pofolioList, axis=0)
        totalPofolio.name = 'portfolio'
        weightDf = pd.concat(weightList, axis=1).T
        self.PrintInfoDemo.PrintLog(infostr='回测完成！ ')
        return totalPofolio, weightDf

    def calcMain(self,method='mean_var',**IndexAllocationParam):
        # 主函数入口
        self.assetIndex = self.getParam()
        GetIndexDataDemo = GetIndexData()
        indexDataDf = GetIndexDataDemo.getHisData(indexCodeList=list(self.assetIndex.keys()),startDate=self.startDate,endDate=self.endDate)

        # 收益率序列
        self.indexReturnDf = (indexDataDf - indexDataDf.shift(1)) / indexDataDf.shift(1)

        # 组合业绩回测
        totalPofolio, weightDf = self.calcAssetAllocation(method,IndexAllocationParam)
        return totalPofolio, weightDf

if __name__ == '__main__':
    AssetAllocationDemo = AssetAllocationMain()
    AssetAllocationDemo.calcMain()
