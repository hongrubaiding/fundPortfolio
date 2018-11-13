# -- coding: utf-8 --

'''
    该模块调用fundPortfolion,用以研究和优化fundProtfolio中的大类到产品组合，
    目前主要以优化target_maxdown,target_risk为主
'''

from PrintInfo import PrintInfo
from MainEntrance.fundPortfolio import fundPortfolio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from datetime import datetime,date
from AssetAllocation.CalcRiskReturnToExcel import CalcRiskReturnToExcel
from fundSelect.SetPortfolio import SetPortfolio

class AssetModelImprove:
    def __init__(self):
        self.PrintInfoDemo = PrintInfo()
        self.CalcRiskReturnToExcelDemo = CalcRiskReturnToExcel()

    def ResearchModel(self,calcNum=50,method='target_risk'):
        modelResult = {}
        fundPortfolioDemo = fundPortfolio()
        timeBack = 0
        for rate in np.linspace(start=0, stop=1, num=calcNum):
            timeBack += 1
            self.PrintInfoDemo.PrintLog('回测第%s次' % str(timeBack))
            modelResult['rate=' + str(rate)] = fundPortfolioDemo.setMain(method=method, rate=rate)
        pickleFile = open(method+'modelResult.pkl', 'wb')
        pickle.dump(modelResult, pickleFile)
        pickleFile.close()
        return modelResult

    #获取本地运行数据或运行程序
    def getData(self,method):
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
            dfReturnAndRisk[keyRate] = modelResult[keyRate]['riskReturndf'][u'投资组合'].to_dict()
        dflist.append(modelResult[keyRate]['pofolioAndBench'][u'60.0%沪深300+40.0%中债国债总财富指数'])

        returnAndRiskTotal = pd.DataFrame(dfReturnAndRisk)
        nameDic = {rateStr:float(rateStr[5:]) for rateStr in returnAndRiskTotal.columns}
        returnAndRiskTotal.rename(columns=nameDic,inplace=True)

        # 所有投资组合历史回测数据
        portFolioDf = pd.concat(dflist, axis=1)
        return returnAndRiskTotal,portFolioDf

    #绘制风险收益指标与rate走势图
    def researchRiskReturn(self,method,returnAndRiskTotal,newFolder):
        mulIndexList = returnAndRiskTotal.index.tolist()
        datePeriodList = list(np.unique([indexTu[0] for indexTu in mulIndexList]))
        riskReturnIndexList = list(np.unique([indexTu[1] for indexTu in mulIndexList]))

        for riskReturnIndex in riskReturnIndexList:
            fig = plt.figure(figsize=(16, 9))
            figCol = 2
            figRow = int(np.ceil(len(datePeriodList) / figCol))
            figTime = 0
            for datePeriod in datePeriodList:
                figTime = figTime + 1
                figNum = int(str(figRow) + str(figCol) + str(figTime))
                fig.tight_layout()
                axNum = fig.add_subplot(figNum)
                returnAndRiskTotal.loc[datePeriod].loc[riskReturnIndex].plot(ax=axNum)
                axNum.set_title(datePeriod)
                axNum.set_xlabel('rate')
                axNum.set_ylabel(riskReturnIndex)
                namePosition = newFolder + ('%s.png' % (method + riskReturnIndex))
            plt.savefig(namePosition)

    # 所有投资组合历史回测数据研究与绘图
    def researchTotalPortfolio(self,portFolioDf,method,newFolder):
        fig = plt.figure(figsize=(16, 9))
        ax1 = fig.add_subplot(111)
        seletFiveList = list(range(2, portFolioDf.shape[1], int(portFolioDf.shape[1] / 5)))  # 取5类组合
        seletFiveAndBenchList = seletFiveList + [-1]
        targetDf = portFolioDf.ix[:, seletFiveAndBenchList]

        self.CalcRiskReturnToExcelDemo.GoMain(targetDf, toExcelPath=newFolder + u'五类风险等级.xls')
        (1 + targetDf).cumprod().plot(ax=ax1)
        ax1.set_title(u'不同rate走势对比图')
        namePosition = newFolder + ('%s.png' % (method + '不同rate下投资组合走势对比图'))
        plt.savefig(namePosition)
        return targetDf

    #投资组合与产品对比研究
    def researchPortfolioFund(self,targetDf,usefulReturnDf,newFolder,method):
        fig = plt.figure(figsize=(16, 9))
        figCol = 2
        figRow = int(np.ceil(targetDf.shape[1] / figCol))

        figTime = 0
        for rateName in targetDf.columns:
            if rateName.find('rate')!=-1:
                figTime = figTime + 1
                figNum = int(str(figRow) + str(figCol) + str(figTime))
                fig.tight_layout()
                tempDf = pd.concat([targetDf[rateName],usefulReturnDf],axis=1,join='inner')
                if figTime!=targetDf.shape[1]-1:
                    axNum = fig.add_subplot(figNum)
                    (1+tempDf).cumprod().plot(ax=axNum,legend=False)
                else:
                    if figTime%2==1:
                        figNum = int(str(figRow) + str(figCol - 1) + str(figRow))
                        axNum = fig.add_subplot(figNum)
                    else:
                        axNum = fig.add_subplot(figNum)
                    upDateName = {colName:'rate' for colName in tempDf.columns if colName.find('rate')!=-1}
                    tempDf.rename(columns=upDateName,inplace=True)
                    (1 + tempDf).cumprod().plot(ax=axNum)
                    box = axNum.get_position()
                    axNum.set_position([box.x0, box.y0, box.width*0.5, box.height])
                    axNum.legend( bbox_to_anchor=(1.1, 1),ncol=1)
                nameStr = str(round(float(rateName[5:]),2))
                axNum.set_title('rate = '+nameStr)
        namePosition = newFolder + ('%s.png' % (method +u'不同投资组合与产品对比走势图'))
        plt.savefig(namePosition)
        # plt.show()

        #计算投资组合与产品历史风险收益指标
        fundNameList = [rateName for rateName in targetDf.columns if rateName.find('rate')!=-1]
        nameDic = {rateName:rateName[:5]+str(round(float(rateName[5:]),2)) for rateName in fundNameList}
        investAndFundDf = pd.concat([targetDf[fundNameList],usefulReturnDf],axis=1,join='inner')
        investAndFundDf.rename(columns=nameDic,inplace=True)
        self.CalcRiskReturnToExcelDemo.GoMain(investAndFundDf, toExcelPath=newFolder + u'五类风险等级与底层产品对比.xls')

    def calcResearch(self,method):
        #创建储存结果文件夹
        fundPortfolioDemo = fundPortfolio()
        newFolder = fundPortfolioDemo.fileMake(u'用户分层投资组合' + method)

        #获取底层产品历史净值数据
        SetPortfolioDemo = SetPortfolio()
        dicResult, resultDf = SetPortfolioDemo.goMain()
        nameDic = {keyName:SetPortfolioDemo.dicProduct[keyName[:-3]] for keyName in resultDf}
        resultDf.rename(columns=nameDic,inplace=True)
        usefulNetDf = resultDf.dropna(axis=0)
        usefulReturnDf = (usefulNetDf-usefulNetDf.shift(1))/usefulNetDf.shift(1)
        usefulReturnDf.fillna(0,inplace=True)

        #获取所有投资组合历史收益及风险指标
        returnAndRiskTotal, portFolioDf = self.getData(method=method)

        #获取五类风险等级走势，存储，并返回
        targetDf = self.researchTotalPortfolio(portFolioDf, method, newFolder)

        #五类风险等级与底层产品走势图，存储
        self.researchPortfolioFund(targetDf,usefulReturnDf,newFolder,method)

        #风险收益指标与rate走势图，存储
        self.researchRiskReturn(method=method, returnAndRiskTotal=returnAndRiskTotal, newFolder=newFolder)

        # plt.show()

if __name__=='__main__':
    import time
    aa = time.time()
    AssetModelImproveDemo = AssetModelImprove()
    AssetModelImproveDemo.calcResearch(method='risk_parity')
    print(u'总耗时：',time.time()-aa)
