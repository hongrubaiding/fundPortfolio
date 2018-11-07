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
from datetime import datetime

class AssetModelImprove:
    def __init__(self):
        self.PrintInfoDemo = PrintInfo()

    def ResearchModel(self,calcNum=50,methond='target_risk'):
        modelResult = {}
        fundPortfolioDemo = fundPortfolio()
        timeBack = 0
        for rate in np.linspace(start=0, stop=1, num=calcNum):
            timeBack += 1
            self.PrintInfoDemo.PrintLog('回测第%s次' % str(timeBack))
            modelResult['rate=' + str(rate)] = fundPortfolioDemo.setMain(method=methond, rate=rate)
        pickleFile = open(methond+'modelResult.pkl', 'wb')
        pickle.dump(modelResult, pickleFile)
        pickleFile.close()
        return modelResult


    def calcResearch(self,method):
        try:
            fileResult = open(method+'modelResult.pkl','rb')
            modelResult = pickle.load(fileResult)
        except:
            modelResult = self.ResearchModel(method=method)

        dflist = []
        dfReturnAndRisk = {}
        for keyRate in modelResult:
            tempSe = modelResult[keyRate]['pofolioAndBench'][u'投资组合']
            tempSe.name = keyRate
            dflist.append(tempSe)
            dfReturnAndRisk[keyRate] = modelResult[keyRate]['riskReturndf'][u'投资组合'][u'成立以来'].to_dict()
        dflist.append(modelResult[keyRate]['pofolioAndBench'][u'60.0%沪深300+40.0%中债国债总财富指数'])

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


        fig = plt.figure(figsize=(16,9))
        ax1 = fig.add_subplot(111)
        df['sharpRate'].plot(ax=ax1,style='r+')


        portFolioDf = pd.concat(dflist, axis=1)
        dateList = [datetime.strptime(dateStr,'%Y-%m-%d') for dateStr in portFolioDf.index]
        portFolioDf = pd.DataFrame(portFolioDf.values,index=dateList,columns=portFolioDf.columns)

        fig = plt.figure(figsize=(16, 9))
        ax2 = fig.add_subplot(111)
        (1+portFolioDf.ix[:,[2,12,22,32,42,-1]]).cumprod().plot(ax=ax2)
        ax2.set_title(u'不同rate走势对比图')
        plt.show()


if __name__=='__main__':
    import time
    aa = time.time()
    AssetModelImproveDemo = AssetModelImprove()
    AssetModelImproveDemo.calcResearch(method='risk_parity')
    print(u'总耗时：',time.time()-aa)
