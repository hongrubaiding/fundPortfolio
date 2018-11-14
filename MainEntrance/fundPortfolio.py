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
from AssetAllocation.AssetAllocationMain import AssetAllocationMain
from fundSelect.SetPortfolio import SetPortfolio
import matplotlib.pylab as plt
from PrintInfo import PrintInfo
from AssetAllocation.CalcRiskReturnToExcel import CalcRiskReturnToExcel
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
        timeList = usefulNetDf.index.tolist()

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
        portfolioSe.name = u'投资组合'
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

    def getBigAsset(self,method,param):
        # 生成大类资产配置模块
        self.PrintInfoDemo.PrintLog(infostr='大类资产配置模型 ', otherInfo=method)
        defineFlag = False
        if method == 'target_maxdown' or method == 'target_risk':
            if param:
                AllocationParam = param['rate']
            else:
                AllocationParam = 0.3
            nameStr = ' rate= ' + str(AllocationParam)  # 图片标题名称和excel的sheet名称
            defineFlag = True

        elif method == 'risk_parity':
            if param:
                AllocationParam = param['rate']
            else:
                AllocationParam = 'equal'
            nameStr = ' rate= ' + str(AllocationParam)  # 图片标题名称和excel的sheet名称
            defineFlag = True
        else:
            nameStr = method

        AssetAllocationMainDemo = AssetAllocationMain()
        if defineFlag:
            totalPofolio, IndexWeightDf = AssetAllocationMainDemo.calcMain(method=method,AllocationParam=AllocationParam)
        else:
            totalPofolio, IndexWeightDf = AssetAllocationMainDemo.calcMain(method=method,)
        self.PrintInfoDemo.PrintLog(infostr='大类资产配置模型初始化完成！')
        return AssetAllocationMainDemo,totalPofolio,IndexWeightDf,nameStr

    def getFundPool(self,AssetAllocationMainDemo,IndexWeightDf):
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
        return portfolioSe,positionDf,SetPortfolioDemo,usefulNetDf

    def riskAndReturnCalc(self,method,nameStr,pofolioAndBench,newFold):
        CalcRiskReturnToExcelDemo = CalcRiskReturnToExcel()
        filePath = newFold + '风险收益指标' + nameStr + '.xls'
        riskReturndf = CalcRiskReturnToExcelDemo.GoMain(pofolioAndBench, toExcelPath=filePath)
        self.PrintInfoDemo.PrintLog(infostr="投资组合风险收益指标: ", otherInfo=riskReturndf)
        return riskReturndf

    def plotFigureResult(self,nameStr,pofolioAndBench,tempPositionDf,newFold,labels):
        fig = plt.figure(figsize=(16,9))
        # fig.set_size_inches(6.4, 7.5)
        ax1 = fig.add_subplot(211)
        pofolioAndBenchAcc = (1 + pofolioAndBench).cumprod()
        pofolioAndBenchAcc.plot(ax=ax1)

        box = ax1.get_position()
        ax1.set_position([box.x0, box.y0, box.width*1.02, box.height])
        ax1.legend(bbox_to_anchor=(1.28, 0.8), ncol=1)
        ax1.grid()
        ax1.set_title(nameStr)

        ax2 = fig.add_subplot(212)
        color = ['#36648B', '#458B00', '#7A378B', '#8B0A50', '#8FBC8F', '#B8860B', '#FFF68F', '#FFF5EE', '#FFF0F5',
                 '#FFEFDB']

        datestrList = [datetime.strftime(dateStr, '%Y-%m-%d') for dateStr in tempPositionDf.index.tolist()]
        for i in range(tempPositionDf.shape[1]):
            ax2.bar(datestrList, tempPositionDf.ix[:, i], color=color[i],
                    bottom=tempPositionDf.ix[:, :i].sum(axis=1))

        box = ax2.get_position()
        ax2.set_position([box.x0, box.y0, box.width * 1.02, box.height])
        ax2.legend(labels=labels,bbox_to_anchor=(1, 0.8), ncol=1)

        for tick in ax2.get_xticklabels():
            tick.set_rotation(90)

        plt.tight_layout()
        plt.savefig(newFold + ('%s.png' % (nameStr)))
        plt.show()



    def setMain(self,method='risk_parity',productFlag=True,**param):
        result = {}  # 保留结果
        AssetAllocationMainDemo, totalPofolio, IndexWeightDf, nameStr = self.getBigAsset(method=method,param=param)
        totalPofolio.name = u'大类资产组合'

        # 投资组合绘图与风险指标计算
        indexReturnDf = AssetAllocationMainDemo.indexReturnDf
        indexDf1 = indexReturnDf[['000300.SH', 'CBA00601.CS']]
        indexDf1.rename(columns={'000300.SH': u'沪深300', 'CBA00601.CS': u'中债国债总财富指数'},inplace=True)

        weightSe = pd.Series([0.6, 0.4], index=['000300.SH', 'CBA00601.CS'])
        indexDf2 = (indexReturnDf[['000300.SH', 'CBA00601.CS']] * weightSe).sum(axis=1)
        indexDf2.name = u"%s沪深300+%s中债国债总财富指数" % ( str(weightSe['000300.SH'] * 100) + '%', str(weightSe['CBA00601.CS'] * 100) + '%')
        indexDf = pd.concat([indexDf1, indexDf2], axis=1, join='inner').fillna(0)

        newFold = self.fileMake(newFoldName=method)
        if productFlag:
            portfolioSe, positionDf,SetPortfolioDemo,usefulNetDf = self.getFundPool(AssetAllocationMainDemo,IndexWeightDf)
            pofolioAndBench = pd.concat([indexDf,portfolioSe,totalPofolio], axis=1, join='inner')
            labels = [SetPortfolioDemo.dicProduct[code[:6]] for code in positionDf.columns.tolist()]
            tempPositionDf = positionDf
        else:
            pofolioAndBench = pd.concat([indexDf,totalPofolio], axis=1, join='inner')
            labels = [AssetAllocationMainDemo.assetIndex[code] for code in IndexWeightDf.columns.tolist()]
            tempPositionDf = IndexWeightDf

        self.plotFigureResult(nameStr, pofolioAndBench, tempPositionDf, newFold,labels)
        riskReturndf = self.riskAndReturnCalc(method=method,nameStr=nameStr,pofolioAndBench=pofolioAndBench,newFold=newFold)

        result['pofolioAndBench'] = pofolioAndBench
        result['riskReturndf'] = riskReturndf
        result['positionDf'] = tempPositionDf
        return result


if __name__ == '__main__':
    methodList = ['equal_weight','min_variance','risk_parity','mean_var','target_risk']
    '''
       equal_weight min_variance,risk_parity，max_diversification，mean_var,target_maxdown,target_risk
    '''
    productFlag = True             #是否到具体产品
    fundPortfolioDemo = fundPortfolio()
    # fundPortfolioDemo.setMain(method='risk_parity')
    fundPortfolioDemo.setMain(method='risk_parity', productFlag=productFlag,rate=0.97777)


