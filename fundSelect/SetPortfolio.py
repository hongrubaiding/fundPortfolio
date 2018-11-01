# -- coding: utf-8 --

'''
    代销公募基金基本信息和净值数据
'''

from fundSelect import fundPool
from WindPy import w
import pandas as pd
from datetime import datetime,date
import numpy as np
import matplotlib.pylab as plt

class SetPortfolio:
    def __init__(self,assetIndex={},backDate=date.today().strftime('%Y-%m-%d')):
        self.dicProduct = fundPool.getFundPool()
        self.getInfoFlag = True
        self.backDate = backDate
        self.assetIndex = assetIndex    #大类资产指数

    # 获取基金池的基本信息
    def getFundInfo(self):
        try:

            fundInfoDf = pd.read_excel(r"C:\\Users\\lenovo\\PycharmProjects\\fundPortfolio\\fundSelect\\fundInfoDf.xlsx")
            print('本地读取fundInfoDf')
            return fundInfoDf
        except:
            w.start()
            print('wind读取fundInfoDf')
            codeList = list(self.dicProduct.keys())
            codeList = [code + '.OF' for code in codeList]
            filedList = ['fund_setupdate', 'fund_fundscale', 'fund_scaleranking', 'fund_mgrcomp', 'fund_type',
                         'fund_fundmanager', 'fund_structuredfundornot',
                         'fund_firstinvesttype', 'fund_investtype', 'fund_risklevel', 'fund_similarfundno',
                         'fund_manager_geometricavgannualyieldoverbench', 'risk_sharpe',
                         'fund_managementfeeratio', 'fund_fullname', 'fund_custodianfeeratio',
                         'NAV_periodicannualizedreturn', 'fund_manager_managerworkingyears', 'fund_benchmark',
                         'fund_benchindexcode',
                         'fund_initial']
            '''https://github.com/hongrubaiding/fundPortfolio'''
            options = "fundType=3;order=1;returnType=1;startDate=20180813;endDate=20180913;period=2;riskFreeRate=1"
            fundInfo = w.wss(codes=codeList, fields=filedList, options=options)
            if fundInfo.ErrorCode != 0:
                print('获取fundInfo失败：', fundInfo.ErrorCode)
                return pd.DataFrame()
            fundInfoDf = pd.DataFrame(fundInfo.Data, index=fundInfo.Fields, columns=codeList).T
            writer = pd.ExcelWriter(r"C:\\Users\\lenovo\\PycharmProjects\\fundPortfolio\\fundSelect\\fundInfoDf.xlsx")
            fundInfoDf.to_excel(writer)
            writer.save()
            return fundInfoDf

    #获取基金池的历史净值数据
    def getFundNetValue(self,startTime):
        try:
            fundNetValueDF = pd.read_excel(r"C:\\Users\\lenovo\\PycharmProjects\\fundPortfolio\\fundSelect\\fundNetValueDF.xlsx")
            print('本地读取fundNetValueDF')
            return fundNetValueDF
        except:
            w.start()
            print('wind读取fundNetValueDF')
            codeList = list(self.dicProduct.keys())
            codeList = [code + '.OF' for code in codeList]
            filed = 'nav'
            fundNetValue = w.wsd(codes=codeList,fields=filed,beginTime=startTime,endTime=datetime.today(),options='Fill=Previous')

            if fundNetValue.ErrorCode != 0:
                print('获取fundInfo失败：', fundNetValue.ErrorCode)
                return pd.DataFrame()
            fundNetValueDf = pd.DataFrame(fundNetValue.Data, index=fundNetValue.Codes, columns=fundNetValue.Times).T
            fundNetValueDf[fundNetValueDf==-2] = np.nan
            writer = pd.ExcelWriter(r"C:\\Users\\lenovo\\PycharmProjects\\fundPortfolio\\fundSelect\\fundNetValueDF.xlsx")
            fundNetValueDf.to_excel(writer)
            writer.save()
            return fundNetValueDf

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
        dicResult['CBA00601.CS'] = ['050011.OF']
        dicResult['AU9999.SGE'] = ['002610.OF']

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
        fundInfoDf = self.getFundInfo()
        startTime = fundInfoDf['FUND_SETUPDATE'].min()
        fundNetValueDf = self.getFundNetValue(startTime)
        fundNetValueUpdateDf = self.settleFundNetValue(fundInfoDf,fundNetValueDf)
        dicFundDf = self.firstSelect(fundInfoDf)
        dicResult, resultDf = self.secondSelect(dicFundDf,fundNetValueUpdateDf)
        return dicResult, resultDf

if __name__ == '__main__':
    SetPortfolioDemo = SetPortfolio()
    SetPortfolioDemo.goMain()
