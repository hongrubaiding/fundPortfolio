# -- coding: utf-8 --

import fundPool
from WindPy import w
import pandas as pd
import xlrd
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

class SetPortfolio:
    def __init__(self):
        self.dicProduct = fundPool.getFundPool()
        self.getInfoFlag = True

    # 获取基金池的基本信息
    def getFundInfo(self):
        try:
            fundInfoDf = pd.read_excel('fundInfoDf.xlsx')
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
            writer = pd.ExcelWriter('fundInfoDf.xlsx')
            fundInfoDf.to_excel(writer)
            writer.save()
            return fundInfoDf

    #获取基金池的历史净值数据
    def getFundNetValue(self,startTime):
        try:
            fundNetValueDF = pd.read_excel('fundNetValueDF.xlsx')
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
            writer = pd.ExcelWriter('fundNetValueDf.xlsx')
            fundNetValueDf.to_excel(writer)
            writer.save()
            return fundNetValueDf

    def firstSelect(self, fundInfoDf,fundNetValueUpdateDf):
        aa = fundInfoDf.sort_values(by=['FUND_RISKLEVEL', 'FUND_FUNDSCALE', 'FUND_SETUPDATE'])
        aa = 0

    #整理净值数据
    def settleFundNetValue(self,fundInfoDf,fundNetValueDf):
        def fifteData(tempSe):
            startDate = fundInfoDf.ix[tempSe.name, 'FUND_SETUPDATE']
            tempSe[tempSe.index<startDate] = np.nan
            return tempSe

        fundNetValueUpdateDf = fundNetValueDf.apply(fifteData)
        fundNetValueUpdateDf.dropna(how='all',inplace=True)

        # fig = plt.figure(figsize=(16,9))
        # ax = fig.add_subplot(111)
        # fundNetValueDf.plot(ax=ax)
        # plt.show()
        return fundNetValueUpdateDf


    def goMain(self):
        fundInfoDf = self.getFundInfo()
        startTime = fundInfoDf['FUND_SETUPDATE'].min()
        fundNetValueDf = self.getFundNetValue(startTime)
        fundNetValueUpdateDf = self.settleFundNetValue(fundInfoDf,fundNetValueDf)
        self.firstSelect(fundInfoDf,fundNetValueUpdateDf)


if __name__ == '__main__':
    SetPortfolioDemo = SetPortfolio()
    SetPortfolioDemo.goMain()
