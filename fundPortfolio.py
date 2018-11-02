# -- coding: utf-8 --

'''
    该模块为主模块
    （1）调用AssetAllocationMain，对大类资产进行回测，得到回测期内的各部分权重
    （2）调用SetPortfolio，对公募基金池筛选，返回所对应的大类，及选中产品的历史净值
    （3）结合（1），（2），按照筛选后的具体产品，回测，绘图，统计相关风险收益指标
'''

import pandas as pd
import numpy as np
from datetime import datetime, date
import AssetAllocation.AssetAllocationMain as AssetAllocationMain
from AssetAllocation.AssetAllocationMain import AssetAllocationMain
from fundSelect.SetPortfolio import SetPortfolio
import matplotlib.pylab as plt
from PrintInfo import PrintInfo
import os
import warnings
warnings.filterwarnings("ignore")


class fundPortfolio:
    def __init__(self):
        backDate = date.today().strftime('%Y-%m-%d')
        self.PrintInfoDemo = PrintInfo()     #日志信息模块
        self.PathFolder = r'C:\\Users\\lenovo\\Desktop\\资产配置研究\\' #存放回测结果的主文件夹

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
            self.PrintInfoDemo.PrintLog(infostr='可用净值日期最小值，大于大类资产可用日期，请检查 ')
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
            tempPorfolioReturn = (tempNetReturnDf * positionDf.loc[positionDateList[dateNum]]).sum(axis=1)

            if dateNum == 0:
                portfolioBackList.append(tempPorfolioReturn)
            else:
                portfolioBackList.append(tempPorfolioReturn[1:])
        portfolioSe = pd.concat(portfolioBackList, axis=0)
        portfolioSe.name = 'portfolio'
        return portfolioSe

    #文件管理
    def fileMake(self,newFoldName):
        #检查指定路径是否存在存放结果的文件夹，不存在就新建
        folder = os.path.exists(self.PathFolder)
        if not folder:
            os.makedirs(self.PathFolder)

        newFolder = self.PathFolder + newFoldName+"\\"
        if not os.path.exists(newFolder):
            os.makedirs(newFolder)
        return newFolder

    def setMain(self,method='risk_parity',**param):
        # 生成大类资产配置模块
        self.PrintInfoDemo.PrintLog(infostr='大类资产配置模型 ', otherInfo=method)
        if method == 'target_maxdown' or method == 'target_risk':
            if param:
                AllocationParam = param['rate']
            else:
                AllocationParam = 0.3
            nameStr = ' rate= '+str(AllocationParam)       #图片标题名称和excel的sheet名称
            AssetAllocationMainDemo = AssetAllocationMain(method=method,AllocationParam=AllocationParam)
        else:
            nameStr = method
            AssetAllocationMainDemo = AssetAllocationMain(method=method)

        totalPofolio, IndexWeightDf = AssetAllocationMainDemo.calcMain()
        self.PrintInfoDemo.PrintLog(infostr='大类资产配置模型初始化完成！')

        # 生成目标基金产品池模块
        self.PrintInfoDemo.PrintLog(infostr='生成目标基金产品池...... ')
        SetPortfolioDemo = SetPortfolio(assetIndex=AssetAllocationMainDemo.assetIndex,
                                        backDate=date.today().strftime('%Y-%m-%d'))
        dicResult, resultDf = SetPortfolioDemo.goMain()
        self.PrintInfoDemo.PrintLog(infostr='生成目标基金产品池完成！ ')

        # 目标产品池基于大类回测权重，再次回测
        self.PrintInfoDemo.PrintLog(infostr='目标产品池回测... ')
        positionDf, usefulNetDf = self.getPortfolioWeightDf(IndexWeightDf, dicResult, resultDf)
        portfolioSe = self.backPofolio(positionDf, usefulNetDf)
        self.PrintInfoDemo.PrintLog(infostr='目标产品池回测完成！ ')

        # 投资组合绘图与风险指标计算
        dateList = [dateFormat.strftime('%Y-%m-%d') for dateFormat in
                    AssetAllocationMainDemo.indexReturnDf['000300.SH'].index]
        benchSe = pd.Series(AssetAllocationMainDemo.indexReturnDf['000300.SH'].values, index=dateList)
        benchSe.name = '000300.SH'

        pofolioAndBench = pd.concat([portfolioSe, benchSe], axis=1, join='inner')
        riskReturndf = AssetAllocationMainDemo.calcRiskReturnToExcel(pofolioAndBench)

        newFold = self.fileMake(newFoldName=method)
        filePath = newFold+'风险收益指标'+nameStr+'.xls'
        riskReturndf.to_excel(filePath)
        self.PrintInfoDemo.PrintLog(infostr="投资组合风险收益指标: ",otherInfo=riskReturndf)

        fig = plt.figure(figsize=(16, 9))
        ax1 = fig.add_subplot(211)
        ax1.set_title(nameStr)
        pofolioAndBenchAcc = (1 + pofolioAndBench).cumprod()
        pofolioAndBenchAcc.plot(ax=ax1)

        ax2 = fig.add_subplot(212)
        color = ['#36648B', '#458B00', '#7A378B', '#8B0A50', '#8FBC8F', '#B8860B', '#FFF68F', '#FFF5EE', '#FFF0F5',
                 '#FFEFDB']
        for i in range(positionDf.shape[1]):
            ax2.bar(positionDf.index.tolist(), positionDf.ix[:, i], color=color[i],
                    bottom=positionDf.ix[:, :i].sum(axis=1))

        labels = [SetPortfolioDemo.dicProduct[code[:6]] for code in positionDf.columns.tolist()]
        ax2.legend(labels=labels, loc='best')
        for tick in ax2.get_xticklabels():
            tick.set_rotation(90)

        plt.savefig(newFold +('%s.png'%(nameStr)))
        # plt.show()


if __name__ == '__main__':
    methodList = ['equal_weight','min_variance','risk_parity','mean_var','target_risk']
    '''
       equal_weight min_variance,risk_parity，max_diversification，mean_var,target_maxdown,target_risk
    '''
    fundPortfolioDemo = fundPortfolio()
    # fundPortfolioDemo.setMain(method='risk_parity')
    fundPortfolioDemo.setMain(method='target_risk',rate=0.18)
