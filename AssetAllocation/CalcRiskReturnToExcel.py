# -- coding: utf-8 --

'''
    计算风险收益指标，并存入指定文件路径
'''

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
from PrintInfo import PrintInfo

class CalcRiskReturnToExcel:
    def __init__(self):
        calcDate = {}
        calcDate['OneMonth'] =(u'近一月',21)
        calcDate['ThreeMonths'] = (u'近三月', 21*3)
        calcDate['SixMonths'] = (u'近六月', 21 * 6)
        calcDate['OneYear'] = (u'近一年', 21 * 12)
        calcDate['TotalPeriod'] = (u'成立以来', np.inf)
        self.calcDate = calcDate
    
    def calcMaxdown(self,return_list):
        '''最大回撤率'''
        return_list = (return_list + 1).cumprod()
        return_list = return_list.values
        i = np.argmax(np.maximum.accumulate(return_list) - return_list)
        if i == 0:
            return 0
        j = np.argmax(return_list[:i])
        result = (return_list[j] - return_list[i]) / return_list[j]
        return result

    def formaData(self,tempSe, flagP=True):
        tempDic = tempSe.to_dict()
        if flagP:
            result = {key: str(round(round(value, 4) * 100, 2)) + '%' for key, value in tempDic.items()}
        else:
            result = {key: round(value, 2) for key, value in tempDic.items()}
        return result

    def GoMain(self,riskDf,toExcelPath=''):

        def formateDf(tempDfData,key,flag='Excel'):
            if flag == 'Excel':
                excelDF = tempDfData['toExcel']
            else:
                excelDF = tempDfData['rightDf']
            excelDF[u'统计周期'] = self.calcDate[key][0]
            return excelDF

        dflist =[]
        dfRightList = []
        for key in self.calcDate:
            dateLineNum = -self.calcDate[key][1]
            if key=='TotalPeriod':
                dateLineNum=0
            tempDf = riskDf.iloc[dateLineNum:]
            initDf = self.CalcMain(tempDf)

            excelDF = formateDf(initDf,key)
            rightDf = formateDf(initDf, key,flag='rightDf')

            dflist.append(excelDF)
            dfRightList.append(rightDf)

        excelResult = pd.concat(dflist,axis=0)
        excelResult[u'指标'] = excelResult.index
        excelResult = excelResult.set_index([u'统计周期',u'指标'],drop=True)
        excelResult.to_excel(toExcelPath)

        RightResult = pd.concat(dfRightList, axis=0)
        RightResult[u'指标'] = RightResult.index
        RightResult = RightResult.set_index([u'统计周期', u'指标'], drop=True)
        return RightResult

    def CalcMain(self,tempDf):
        dicResult = {}  # 存入excel表格中保留有效数字
        dicRightResult = {}  # 准确值

        assetAnnualReturn = tempDf.mean() * 250
        assetStd = tempDf.std() * np.sqrt(250)

        assetMaxDown = tempDf.dropna().apply(self.calcMaxdown)
        assetCalmar = assetAnnualReturn / assetMaxDown
        assetSharp = (assetAnnualReturn) / assetStd

        dicResult[u'年化收益'] = self.formaData(assetAnnualReturn)
        dicResult[u'年化波动'] = self.formaData(assetStd)
        dicResult[u'最大回撤'] = self.formaData(assetMaxDown)
        dicResult[u'夏普比率'] = self.formaData(assetSharp, flagP=False)
        dicResult[u'卡玛比率'] = self.formaData(assetCalmar, flagP=False)

        dicRightResult[u'年化收益'] = assetAnnualReturn
        dicRightResult[u'年化波动'] = assetStd
        dicRightResult[u'最大回撤'] = assetMaxDown
        dicRightResult[u'夏普比率'] = assetSharp
        dicRightResult[u'卡玛比率'] = assetCalmar

        dfexcel = pd.DataFrame(dicResult).T
        dfRight = pd.DataFrame(dicRightResult).T
        dfexcel.rename(columns={'000300.SH': u'沪深300', 'portfolio': u'投资组合'}, inplace=True)

        dfDic = {}
        dfDic['toExcel'] =dfexcel
        dfDic['rightDf'] = dfRight
        return dfDic
