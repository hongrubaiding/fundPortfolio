# -- coding: utf-8 --

'''
    代销公募基金基本信息和净值数据
'''

from fundSelect import fundPool
import pandas as pd
from datetime import datetime,date
import numpy as np
from PrintInfo import PrintInfo
from GetHistoryData.GetProductData import GetProductData

class SetPortfolio:
    def __init__(self,assetIndex={},backDate=date.today().strftime('%Y-%m-%d')):
        self.dicProduct = fundPool.getFundPool()
        self.getInfoFlag = True
        self.backDate = backDate
        self.assetIndex = assetIndex    #大类资产指数
        self.PrintInfoDemo = PrintInfo()  # 日志信息模块

    #初步过滤基金池，并对基金池归类
    def firstSelect(self, fundInfoDf):
        def dateFormat(tempSe):
            tempList = [tempSe[k].strftime('%Y-%m-%d') for k in tempSe.index.tolist()]
            resutlt = pd.Series(tempList,index=tempSe.index)
            return resutlt

        #过滤掉成立日期小于指定日期的基金
        fundInfoDf['FUND_SETUPDATE'] = dateFormat(fundInfoDf['FUND_SETUPDATE'])
        fundDf = fundInfoDf.loc[fundInfoDf['FUND_SETUPDATE']<=self.backDate]

        #过滤掉定期开放的基金
        fundDf['nameFlag'] = [name.find(u'定期开放') for name in fundDf['FUND_FULLNAME'].tolist()]
        fundDf = fundDf[fundDf['nameFlag']==-1]
        fundDf.drop(labels=['nameFlag'],axis=1,inplace=True)

        #按照基金的二级分类，对基金池划分
        dicFundStyle = {}
        for typeName,tempDf in fundDf.groupby(['FUND_INVESTTYPE']):
            dicFundStyle[typeName] = tempDf
        return dicFundStyle

    #再次处理基金池,返回大类对应的产品和基金净值数据
    def secondSelect(self,dicFundDf,fundNetValueUpdateDf):
        dicResult = {}
        # if u'被动指数型基金' in dicFundDf:
        #     tempETFDf = dicFundDf[u'被动指数型基金']

        dicResult['000016.SH'] =['110020.OF']
        dicResult['000300.SH'] = ['270010.OF']
        dicResult['000905.SH'] = ['162711.OF','110026.OF']
        dicResult['SPX.GI'] = ['270042.OF']
        dicResult['CBA00601.CS'] = ['001021.OF']
        # dicResult['AU9999.SGE'] = ['002610.OF']
        dicResult['AU9999.SGE'] = ['518800.OF']

        totalSelectList = []
        for key,value in dicResult.items():
            totalSelectList = totalSelectList+value
        resultDf = fundNetValueUpdateDf[totalSelectList]
        return dicResult,resultDf

    #整理净值数据
    def settleFundNetValue(self,fundInfoDf,fundNetValueDf):
        def fifteData(tempSe):
            startDate = fundInfoDf.ix[tempSe.name, 'FUND_SETUPDATE']
            tempSe[tempSe.index<startDate] = np.nan
            return tempSe

        fundNetValueUpdateDf = fundNetValueDf.apply(fifteData)
        fundNetValueUpdateDf.dropna(how='all',inplace=True)
        return fundNetValueUpdateDf

    def goMain(self):
        GetProductDataDemo = GetProductData()
        fundInfoDf = GetProductDataDemo.getFundInfo(productList=list(self.dicProduct.keys()))
        startTime = fundInfoDf['FUND_SETUPDATE'].min()
        fundNetValueDf = GetProductDataDemo.getFundNetValue(startTime,productList=list(self.dicProduct.keys()))
        fundNetValueUpdateDf = self.settleFundNetValue(fundInfoDf,fundNetValueDf)
        dicFundDf = self.firstSelect(fundInfoDf)
        dicResult, resultDf = self.secondSelect(dicFundDf,fundNetValueUpdateDf)
        return dicResult, resultDf

if __name__ == '__main__':
    SetPortfolioDemo = SetPortfolio()
    SetPortfolioDemo.goMain()
