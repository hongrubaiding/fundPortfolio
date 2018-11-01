# -- coding: utf-8 --

import pandas as pd
import numpy as np
from datetime import datetime, date
import AssetAllocation.AssetAllocationMain as AssetAllocationMain
from AssetAllocation.AssetAllocationMain import AssetAllocationMain
from fundSelect.SetPortfolio import SetPortfolio
import matplotlib.pylab as plt


class fundPortfolio:
    def __init__(self):
        backDate = date.today().strftime('%Y-%m-%d')

    # 获取投资组合调仓期内的权重
    def getPortfolioWeightDf(self, IndexWeightDf, dicResult, resultDf):
        usefulNetDf = resultDf.dropna(axis=0)
        timeList = [tempTime.strftime('%Y-%m-%d') for tempTime in usefulNetDf.index.tolist()]
        usefulNetDf = pd.DataFrame(usefulNetDf.values, index=timeList, columns=usefulNetDf.columns)

        # 找到第一个持仓日
        totalDate = IndexWeightDf.index.tolist()
        for assetDate in totalDate:
            if assetDate >= timeList[0]:
                try:
                    assetPreDate = totalDate.index(assetDate) - 1
                    usefulIndexWeightDf = IndexWeightDf.iloc[assetPreDate:]
                except:
                    usefulIndexWeightDf = IndexWeightDf.loc[assetDate:]
                break
        else:
            print('可用净值日期最小值，大于大类资产可用日期，请检查')
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

            # aa= positionDf.loc[positionDateList[dateNum]]
            tempPorfolioReturn = (tempNetReturnDf * positionDf.loc[positionDateList[dateNum]]).sum(axis=1)

            if dateNum == 0:
                portfolioBackList.append(tempPorfolioReturn)
            else:
                portfolioBackList.append(tempPorfolioReturn[1:])
        portfolioSe = pd.concat(portfolioBackList, axis=0)
        portfolioSe.name = 'portfolio'
        return portfolioSe

    def setMain(self):
        # 生成大类资产配置模块
        '''
        equal_weight min_variance,risk_parity，max_diversification，mean_var,target_maxdown,target_risk
        '''
        AssetAllocationMainDemo = AssetAllocationMain(method='min_variance')
        totalPofolio, IndexWeightDf = AssetAllocationMainDemo.calcMain()

        #生成目标基金产品池模块
        SetPortfolioDemo = SetPortfolio(assetIndex=AssetAllocationMainDemo.assetIndex,
                                        backDate=date.today().strftime('%Y-%m-%d'))
        dicResult, resultDf = SetPortfolioDemo.goMain()

        #目标产品池基于大类回测权重，再次回测
        positionDf, usefulNetDf = self.getPortfolioWeightDf(IndexWeightDf, dicResult, resultDf)
        portfolioSe = self.backPofolio(positionDf, usefulNetDf)

        #投资组合绘图与风险指标计算
        dateList = [dateFormat.strftime('%Y-%m-%d') for dateFormat in AssetAllocationMainDemo.indexReturnDf['000300.SH'].index]
        benchSe = pd.Series(AssetAllocationMainDemo.indexReturnDf['000300.SH'].values,index=dateList)
        benchSe.name = '000300.SH'

        pofolioAndBench = pd.concat([portfolioSe,benchSe], axis=1, join='inner')
        riskReturndf = AssetAllocationMainDemo.calcRiskReturnToExcel(pofolioAndBench)
        print(riskReturndf)

        fig = plt.figure(figsize=(16,9))
        ax1 = fig.add_subplot(111)
        pofolioAndBenchAcc = (1+pofolioAndBench).cumprod()
        pofolioAndBenchAcc.plot(ax=ax1)
        plt.show()


if __name__ == '__main__':
    fundPortfolioDemo = fundPortfolio()
    fundPortfolioDemo.setMain()
