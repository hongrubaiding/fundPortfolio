# -- coding: utf-8 --

'''
    大类资产配研究，获取具体产品历史数据
'''

import pandas as pd
from iFinDPy import *
from WindPy import w
from datetime import datetime
import numpy as np
import mylog as mylog

class GetProductData:
    def __init__(self):
        self.logger = mylog.logger

    # 获取基金池的基本信息
    def getFundInfo(self,productList=[]):
        if not productList:
            self.logger.info('未传入指数参数，请检查！')
            return

        try:
            fundInfoDf = pd.read_excel(
                r"C:\\Users\\lenovo\\PycharmProjects\\fundPortfolio\\GetHistoryData\\fundInfoDf.xlsx")
            self.logger.info('本地读取基金历史信息数据 fundInfoDf')
            return fundInfoDf
        except:
            w.start()
            self.PrintInfoDemo.PrintLog(infostr='wind读取基金历史信息数据 fundInfoDf')
            codeList = [code + '.OF' for code in productList]
            filedList = ['fund_setupdate', 'fund_fundscale', 'fund_scaleranking', 'fund_mgrcomp', 'fund_type',
                         'fund_fundmanager', 'fund_structuredfundornot',
                         'fund_firstinvesttype', 'fund_investtype', 'fund_risklevel', 'fund_similarfundno',
                         'fund_manager_geometricavgannualyieldoverbench', 'risk_sharpe',
                         'fund_managementfeeratio', 'fund_fullname', 'fund_custodianfeeratio',
                         'NAV_periodicannualizedreturn', 'fund_manager_managerworkingyears', 'fund_benchmark',
                         'fund_benchindexcode',
                         'fund_initial']
            options = "fundType=3;order=1;returnType=1;startDate=20180813;endDate=20180913;period=2;riskFreeRate=1"
            fundInfo = w.wss(codes=codeList, fields=filedList, options=options)
            if fundInfo.ErrorCode != 0:
                self.PrintInfoDemo.PrintLog(infostr='wind读取基金历史信息数据失败，错误代码：', otherInfo=fundInfo.ErrorCode)
                return pd.DataFrame()
            fundInfoDf = pd.DataFrame(fundInfo.Data, index=fundInfo.Fields, columns=codeList).T
            writer = pd.ExcelWriter(r"C:\\Users\\lenovo\\PycharmProjects\\fundPortfolio\\GetHistoryData\\fundInfoDf.xlsx")
            fundInfoDf.to_excel(writer)
            writer.save()
            self.logger.info('wind读取基金历史信息数据成功，写入本地文件fundInfoDf.xlsx')
            return fundInfoDf

        # 获取基金池的历史净值数据
    def getFundNetValue(self, startTime,productList=[]):
        if not productList:
            self.PrintInfoDemo.PrintLog('未传入指数参数，请检查！')
            return

        try:
            fundNetValueDF = pd.read_excel(
                r"C:\\Users\\lenovo\\PycharmProjects\\fundPortfolio\\GetHistoryData\\fundNetValueDF.xlsx")
            self.PrintInfoDemo.PrintLog(infostr='本地读取基金净值数据 fundNetValueDF')
            return fundNetValueDF
        except:
            w.start()
            self.PrintInfoDemo.PrintLog(infostr='wind读取基金净值数据 fundNetValueDF')
            codeList = [code + '.OF' for code in productList]
            filed = 'NAV_adj'  # 复权单位净值
            fundNetValue = w.wsd(codes=codeList, fields=filed, beginTime=startTime, endTime=datetime.today(),
                                 options='Fill=Previous')

            if fundNetValue.ErrorCode != 0:
                self.PrintInfoDemo.PrintLog(infostr='wind读取基金净值数据失败，错误代码： ', otherInfo=fundNetValue.ErrorCode)
                return pd.DataFrame()
            fundNetValueDf = pd.DataFrame(fundNetValue.Data, index=fundNetValue.Codes, columns=fundNetValue.Times).T
            fundNetValueDf[fundNetValueDf == -2] = np.nan
            writer = pd.ExcelWriter(
                r"C:\\Users\\lenovo\\PycharmProjects\\fundPortfolio\\GetHistoryData\\fundNetValueDF.xlsx")
            fundNetValueDf.to_excel(writer)
            writer.save()
            self.PrintInfoDemo.PrintLog(infostr='wind读取基金净值数据成功，写入本地文件fundNetValueDF.xlsx ')
            return fundNetValueDf


if __name__ == '__main__':
    GetProductDataDemo = GetProductData()
    GetProductDataDemo.getHisData()