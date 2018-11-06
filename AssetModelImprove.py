# -- coding: utf-8 --

'''
    该模块调用fundPortfolion,用以研究和优化fundProtfolio中的大类到产品组合，
    目前主要以优化target_maxdown,target_risk为主
'''

from PrintInfo import PrintInfo
from fundPortfolio import fundPortfolio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle

class AssetModelImprove:
    def __init__(self):
        self.PrintInfoDemo = PrintInfo()
        pass

    def Research_MaxDown(self):
        modelResult = {}
        fundPortfolioDemo = fundPortfolio()
        for rate in np.linspace(start=0,stop=0.5,num=5):
            modelResult['rate=' + str(rate)] = fundPortfolioDemo.setMain(method='target_maxdown', rate=rate)

    def Research_TargetRisk(self):
        modelResult = {}
        fundPortfolioDemo = fundPortfolio()
        timeBack = 0
        for rate in np.linspace(start=0, stop=0.8, num=50):
            timeBack +=1
            self.PrintInfoDemo.PrintLog('回测第%s次'%str(timeBack))
            modelResult['rate=' + str(rate)] = fundPortfolioDemo.setMain(method='target_risk', rate=rate)
        pickleFile = open('modelResult0_0.5z.pkl','wb')
        pickle.dump(modelResult,pickleFile)
        pickleFile.close()
        return modelResult

    def calcResearch(self):
        try:
            fileResult = open('modelResult0_0.5z.pkl','rb')
            modelResult = pickle.load(fileResult)
        except:
            modelResult = self.Research_TargetRisk()

        dflist = []
        dfReturnAndRisk = {}
        for keyRate in modelResult:
            tempSe = modelResult[keyRate]['pofolioAndBench']['IndexPortfolio']
            tempSe.name = keyRate
            dflist.append(tempSe)

            dfReturnAndRisk[keyRate] = modelResult[keyRate]['riskReturndf']['IndexPortfolio'][u'近一年'].to_dict()
        dflist.append(modelResult[keyRate]['pofolioAndBench']['000300.SH'])

        sortReturn = sorted(dfReturnAndRisk.items(),key=lambda item:item[0])
        rateList = []
        annualReturn = []
        annualStd = []
        maxDown = []
        sharpRate = []
        calmaRate = []
        for data in sortReturn:
            rateList.append(float(data[0][5:]))
            annualReturn.append(data[1][u'年化收益'])
            annualStd.append(data[1][u'年化波动'])
            maxDown.append(data[1][u'最大回撤'])
            sharpRate.append(data[1][u'夏普比率'])
            calmaRate.append(data[1][u'卡玛比率'])
        df = pd.DataFrame([annualReturn,annualStd,maxDown,sharpRate,calmaRate],columns=rateList,
                          index=['annualReturn','annualStd','maxDown','sharpRate','calmaRate']).T

        df['annualStd'].plot()
        plt.show()

        portFolioDf = pd.concat(dflist, axis=1)
        (1+portFolioDf.ix[:,[2,12,22,32,42,-1]]).cumprod().plot()
        plt.show()


if __name__=='__main__':
    AssetModelImproveDemo = AssetModelImprove()
    AssetModelImproveDemo.Research_TargetRisk()