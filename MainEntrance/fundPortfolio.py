# -- coding: utf-8 --

'''
    该模块为主模块
    （1）调用AssetAllocationMain，对大类资产进行回测，得到回测期内的各部分权重
    （2）调用SetPortfolio，对公募基金池筛选，返回所对应的大类，及选中产品的历史净值
    （3）结合（1），（2），按照筛选后的具体产品，回测，绘图，统计相关风险收益指标
'''

import pandas as pd
import numpy as np
from datetime import datetime, date,timedelta
from AssetAllocation.AssetAllocationMain import AssetAllocationMain
from fundSelect.SetPortfolio import SetPortfolio
import matplotlib.pylab as plt
from GetAndSaveWindData.GetDataTotalMain import GetDataTotalMain

import mylog as mylog
from AssetAllocation.CalcRiskReturnToExcel import CalcRiskReturnToExcel
import os
import warnings
warnings.filterwarnings("ignore")


class fundPortfolio:
    def __init__(self, startDate='2015-09-01',file_path=''):
        self.startDate = startDate              #历史数据开始日期
        self.endDate = (datetime.today() - timedelta(days=0)).strftime('%Y-%m-%d')
        if not file_path:
            self.PathFolder = r'C:\\Users\\zouhao\\Desktop\\资产配置研究\\'
        else:
            self.PathFolder = r'C:\\Users\\zouhao\\Desktop\\资产配置研究\\' + file_path + '\\'
        self.logger = mylog.set_log()

    # 获取投资组合调仓期内的权重
    def getPortfolioWeightDf(self, IndexWeightDf, dicResult, result_return_df):
        # usefulNetDf = resultDf.dropna(axis=0)
        usefulNetDf = result_return_df
        timeList = usefulNetDf.index.tolist()

        # 找到第一个持仓日
        totalDate = IndexWeightDf.index.tolist()
        for assetDate in totalDate:
            if assetDate >= timeList[0]:
                if assetDate != timeList[0]:
                    assetPreDate = totalDate.index(assetDate) - 1
                    if assetPreDate == -1:
                        usefulIndexWeightDf = IndexWeightDf
                    else:
                        usefulIndexWeightDf = IndexWeightDf.iloc[assetPreDate:]
                else:
                    usefulIndexWeightDf = IndexWeightDf.loc[assetDate:]
                break
        else:
            self.logger.info('可用净值日期最小值，大于大类资产可用日期，请检查 ')
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
    def backPofolio(self, positionDf, usefulNetReturnDf):
        # usefulNetReturnDf = (usefulNetDf - usefulNetDf.shift(1)) / usefulNetDf.shift(1)
        usefulNetReturnDf.fillna(0, inplace=True)

        portfolioBackList = []
        positionDateList = positionDf.index.tolist()
        for dateNum in range(len(positionDateList)):
            if dateNum == 0:
                startDate = usefulNetReturnDf.index[0]
            else:
                startDate = positionDateList[dateNum]

            if dateNum + 1 < len(positionDateList):
                tempNetReturnDf = usefulNetReturnDf.loc[startDate:positionDateList[dateNum + 1]]
            else:
                tempNetReturnDf = usefulNetReturnDf.loc[startDate:]
            tempPorfolioReturn = (tempNetReturnDf * positionDf.loc[positionDateList[dateNum]]).sum(axis=1)

            if dateNum == 0:
                portfolioBackList.append(tempPorfolioReturn)
            else:
                portfolioBackList.append(tempPorfolioReturn[1:])

        portfolioSe = pd.concat(portfolioBackList, axis=0)
        portfolioSe.name = u'基金投资组合'
        return portfolioSe

    # 文件管理
    def fileMake(self, newFoldName):
        # 检查指定路径是否存在存放结果的文件夹，不存在就新建
        folder = os.path.exists(self.PathFolder)
        if not folder:
            os.makedirs(self.PathFolder)

        newFolder = self.PathFolder + newFoldName + "\\"
        if not os.path.exists(newFolder):
            os.makedirs(newFolder)
        return newFolder

    def getBigAsset(self, method, asset_index={}, best_param_dic={}):
        # 生成大类资产配置模块
        self.logger.info('大类资产配置模型 %s' % method)
        nameStr = method
        AssetAllocationMainDemo = AssetAllocationMain()
        totalPofolio, IndexWeightDf, equalPortfolio = AssetAllocationMainDemo.calcMain(startDate=self.startDate,endDate=self.endDate,method=method,
                                                                                       asset_index=asset_index,
                                                                                       best_param_dic=best_param_dic)
        self.logger.info('大类资产配置模型初始化完成！')
        return AssetAllocationMainDemo, totalPofolio, IndexWeightDf, equalPortfolio, nameStr

    def getFundPool(self, AssetAllocationMainDemo, IndexWeightDf, portfolio_df,method='mean_var',product_name_dic={},fund_type='ETF'):
        # 生成目标基金产品池模块
        self.logger.info('生成目标基金产品池...... ')

        SetPortfolioDemo = SetPortfolio(assetIndex=AssetAllocationMainDemo.assetIndex)
        total_date_list = portfolio_df.index.tolist()
        dicResult, resultDf = SetPortfolioDemo.get_asset_fund(start_date=total_date_list[0],
                                                              end_date=total_date_list[-1],product_name_dic=product_name_dic,fund_type=fund_type)
        self.logger.info('生成目标基金产品池完成！ ')

        # 目标产品池基于大类回测权重，再次回测
        self.logger.info('目标产品池回测... ')
        result_return_df = resultDf/resultDf.shift(1)-1
        if method in ['industry_recyle','industry_recyle_stock','industry_recyle_mean_var_stock']:
            temp_dic = {list(dic_data.keys())[0]: index_code for index_code, dic_data in dicResult.items()}
            indexReturnDf = AssetAllocationMainDemo.indexReturnDf
            for product_code in result_return_df.columns.tolist():
                temp_se = result_return_df[product_code]
                nan_se = temp_se[np.isnan(temp_se)]
                if not nan_se.empty:
                    temp_se[np.isnan(temp_se)] = indexReturnDf[temp_dic[product_code]].loc[nan_se.index.tolist()]

        positionDf, usefulNetReturnDf = self.getPortfolioWeightDf(IndexWeightDf, dicResult, result_return_df)
        portfolioSe = self.backPofolio(positionDf, usefulNetReturnDf)
        self.logger.info('目标产品池回测完成！累计收益%s '%(1+portfolioSe).prod())
        return portfolioSe, positionDf, dicResult, usefulNetReturnDf

    def riskAndReturnCalc(self, method, nameStr, pofolioAndBench, newFold):
        CalcRiskReturnToExcelDemo = CalcRiskReturnToExcel()
        filePath = newFold + '风险收益指标' + nameStr + '.xls'
        riskReturndf = CalcRiskReturnToExcelDemo.GoMain(pofolioAndBench, toExcelPath=filePath)
        self.logger.info("投资组合风险收益指标计算完成！")
        return riskReturndf

    def plotFigureResult(self, nameStr, pofolioAndBench, tempPositionDf, newFold, labels, asset_df):
        def historydownrate(tempdata):
            templist = []
            for k in range(len(tempdata)):
                downrate = tempdata.iloc[k] / tempdata.iloc[:k + 1].max() - 1
                templist.append(downrate)
            tempdf = pd.Series(templist, index=tempdata.index)
            tempdf.name = tempdata.name
            return tempdf

        downDf = (1 + pofolioAndBench).cumprod().apply(historydownrate)
        fig_down = plt.figure(figsize=(16, 9))
        ax_down = fig_down.add_subplot(111)
        downDf[['沪深300','基金投资组合']].plot.area(ax=ax_down, stacked=False)
        ax_down.set_title(u'回撤率走势图')
        plt.savefig(newFold + ('%s.png' % ('回撤率走势图')))

        fig = plt.figure(figsize=(16, 9))
        # fig.set_size_inches(6.4, 7.5)
        ax1 = fig.add_subplot(111)

        judge_date = '2018-01-01'
        pofolioAndBench_wai = pofolioAndBench[pofolioAndBench.index>=judge_date]

        pofolioAndBenchAcc_wai = (1 + pofolioAndBench_wai).cumprod()
        pofolioAndBenchAcc_wai[['基金投资组合','沪深300']].plot(ax=ax1)
        # pofolioAndBenchAcc.plot(ax=ax1)

        box = ax1.get_position()
        ax1.set_position([box.x0, box.y0, box.width * 1.02, box.height])
        # ax1.legend(bbox_to_anchor=(1.28, 0.8), ncol=1)
        ax1.grid()
        # ax1.set_title("策略净值走势")
        plt.savefig(newFold + ('%s.png' % ('策略净值走势')))

        color = ['#36648B', '#458B00', '#7A378B', '#8B0A50', '#8FBC8F', '#B8860B', '#FFF68F', '#FFF5EE', '#FFF0F5','#FFEFDB',
                 '#F4A460', '#A0522D', '#FFE4E1', '#BC8F8F', '#A52A2A', '#800000', '#F5F5F5', '#DCDCDC', '#808080','#000000',
                 '#FFA500', '#F5DEB3', '#DAA520', '#BDB76B', '#556B2F', '#006400', '#98FB98', '#7FFFAA', '#20B2AA','#F0FFFF',
                 '#191970', '#BA55D3', '#DDA0DD', '#4B0082', '#8FBC8F', '#B8860B', '#FFF68F', '#FFF5EE', '#FFF0F5','#FFEFDB',
                 '#36648B', '#458B00', '#7A378B', '#8B0A50', '#8FBC8F', '#B8860B', '#FFF68F', '#FFF5EE', '#FFF0F5','#FFEFDB']
        # fig = plt.figure(figsize=(16, 10))
        # # fig.set_size_inches(6.4, 7.5)
        # ax2 = fig.add_subplot(111)

        # tempPositionDf =  tempPositionDf[tempPositionDf.index>='2019-01-01']
        # datestrList = tempPositionDf.index.tolist()
        # for i in range(tempPositionDf.shape[1]):
        #     ax2.bar(datestrList, tempPositionDf.ix[:, i], color=color[i],
        #             bottom=tempPositionDf.ix[:, :i].sum(axis=1))

        # box = ax2.get_position()
        # ax2.set_position([box.x0, box.y0, box.width * 1.02, box.height])
        # ax2.legend(labels=labels, bbox_to_anchor=(1, 1), ncol=1,fontsize=10)
        # # ax2.set_title("仓位变化走势")
        # for tick in ax2.get_xticklabels():
        #     tick.set_rotation(90)
        # plt.savefig(newFold + ('%s.png' % (nameStr)))

        fig2 = plt.figure(figsize=(16, 9))
        # fig.set_size_inches(6.4, 7.5)
        ax3 = fig2.add_subplot(111)
        asset_df.plot.area(ax=ax3)
        box3 = ax3.get_position()
        ax3.set_position([box3.x0, box3.y0, box3.width * 1.02, box3.height])
        ax3.legend(labels=asset_df.columns.tolist(), bbox_to_anchor=(1, 0.8), ncol=1)
        plt.savefig(newFold + ('%s.png' % ('大类资产仓位占比')))
        plt.tight_layout()
        plt.show()

    def get_asset_weight(self, index_weight_df, asset_index):
        '''
        将资产按照大类权益，固收，商品，货币等，归类成新的DataFrame
        :param index_weight_df:
        :return:
        '''
        label_asset = {}
        name_dic = {"stock": "权益类", "bond": "固定收益类", "commodity": "商品类"}
        for code in index_weight_df.columns.tolist():
            for asset_style, index_dic in asset_index.items():
                if code in list(index_dic.keys()):
                    label_asset[asset_style] = label_asset.get(asset_style, [])
                    label_asset[asset_style].append(code)

        df_asset_list = []
        for asset_style, code_list in label_asset.items():
            asset_se = index_weight_df[code_list].sum(axis=1)
            asset_se.name = asset_style
            df_asset_list.append(asset_se)
        asset_df = pd.concat(df_asset_list, sort=True, axis=1)
        asset_df.rename(columns=name_dic, inplace=True)
        return asset_df

    def setMain(self, method='risk_parity', productFlag=True, asset_index={}, best_param_dic={},product_name_dic={},fund_type='ETF'):
        AssetAllocationMainDemo, totalPofolio, IndexWeightDf, equalPortfolio, nameStr = self.getBigAsset(method=method,
                                                                                                         asset_index=asset_index,
                                                                                                         best_param_dic=best_param_dic)
        totalPofolio.name = u'大类资产组合'
        equalPortfolio.name = u'等权重组合'
        # target_date = '2020-03-05'
        target_date = self.startDate
        totalPofolio = totalPofolio[totalPofolio.index >= target_date]
        IndexWeightDf = IndexWeightDf[IndexWeightDf.index >= target_date]
        equalPortfolio = equalPortfolio[equalPortfolio.index >= target_date]
        portfolio_df = pd.concat([totalPofolio, equalPortfolio], axis=1, sort=True)

        # 投资组合绘图与风险指标计算
        bench_code = '000300.SH'
        bench_name = '沪深300'
        if bench_code in AssetAllocationMainDemo.indexReturnDf:
            indexDf1 = pd.DataFrame()
            indexDf1['沪深300'] = AssetAllocationMainDemo.indexReturnDf['000300.SH']
        else:
            GetDataTotalMainDemo = GetDataTotalMain(data_resource='wind')
            indexDataDf1 = GetDataTotalMainDemo.get_hq_data(bench_code, start_date=self.startDate, end_date=self.endDate,
                                                        code_style='index')
            indexDataDf1.rename(columns={"close_price": bench_name}, inplace=True)
            indexDf1=indexDataDf1/indexDataDf1.shift(1)-1

        newFold = self.fileMake(newFoldName=method)
        asset_df = self.get_asset_weight(IndexWeightDf, AssetAllocationMainDemo.assetIndex)
        if productFlag:
            portfolioSe, positionDf, dicResult, usefulNetReturnDf = self.getFundPool(AssetAllocationMainDemo,
                                                                               IndexWeightDf, portfolio_df,method,product_name_dic=product_name_dic,fund_type=fund_type)

            pofolioAndBench = pd.concat([indexDf1, portfolioSe, portfolio_df], axis=1, join='inner')

            total_fund_name_dic = {}
            for index, dic in dicResult.items():
                total_fund_name_dic.update(dic)
            labels = [total_fund_name_dic[code] for code in positionDf.columns.tolist()]
            net_return_df = usefulNetReturnDf.copy()
            net_return_df.fillna(0, inplace=True)
            net_return_df.rename(columns=total_fund_name_dic, inplace=True)
            net_return_df = net_return_df[net_return_df.index >= target_date]
            self.riskAndReturnCalc(method=method, nameStr='基金产品风险收益指标', pofolioAndBench=net_return_df,
                                   newFold=newFold)
            tempPositionDf = positionDf
            # tempPositionDf.rename(columns=total_fund_name_dic,inplace=True)
        else:
            pofolioAndBench = pd.concat([indexDf1, portfolio_df], axis=1, join='inner')
            labels = [dic[code] for code in IndexWeightDf.columns.tolist() for
                      asset_style, dic in AssetAllocationMainDemo.assetIndex.items() if code in list(dic.keys())]
            tempPositionDf = IndexWeightDf

        asset_df.to_excel(newFold + "大类资产仓位表.xlsx")
        tempPositionDf.to_excel(newFold + "产品组合仓位表.xlsx")
        self.plotFigureResult(nameStr, pofolioAndBench, tempPositionDf, newFold, labels, asset_df)
        riskReturndf = self.riskAndReturnCalc(method=method, nameStr=nameStr, pofolioAndBench=pofolioAndBench,
                                              newFold=newFold)
        return


if __name__ == '__main__':
    methodList = ['equal_weight', 'min_variance', 'risk_parity', 'mean_var', 'target_risk', "fix_rate", "recyle","recye_update"]
    '''
       equal_weight min_variance,risk_parity，max_diversification，mean_var,target_maxdown,target_risk
    '''
    productFlag = True  # 是否到具体产品
    fundPortfolioDemo = fundPortfolio()
    fundPortfolioDemo.setMain(method='risk_parity',productFlag=productFlag,fund_type='OTC')
    # fundPortfolioDemo.setMain(method='recye_update', productFlag=productFlag, )

    # fundPortfolioDemo.setMain(method='fix_rate', productFlag=productFlag,)
    # fundPortfolioDemo.setMain(method='recyle', productFlag=productFlag,)
    # param_dic = {'adjust_day_limit': 20, 'back_day_limit': 154, 'bond_limit': 0.73761507961522}
    # param_dic = {'adjust_day_limit': 27, 'back_day_limit': 10, 'max_index_loss_limit': 1.1233227454395853, 'poc_value_limit': 7.49884250939969e-07}
    # param_dic = {'adjust_day_limit': 12, 'back_day_limit': 11, 'max_index_loss_limit': 1.0754639827433492, 'poc_value_limit': 0.0014094411098240604}
    # asset_index = {'stock': {'000300.SH': '沪深300', '000905.SH': '中证500'}}       #风格轮动不含债

    param_dic = {'adjust_day_limit': 15, 'back_day_limit': 3, 'max_index_loss_limit': 1.1370817829344184,
     'poc_value_limit': 0.8761773229137094}
    param_dic = {'adjust_day_limit': 15, 'back_day_limit': 5, 'max_index_loss_limit': 1.1642873017666255,
     'poc_value_limit': 0.8759698978397606}

    param_dic={'adjust_day_limit': 15, 'back_day_limit': 5, 'max_index_loss_limit': 1.0002646566102376, 'poc_value_limit': 0.8999219087682704}
    param_dic = {'adjust_day_limit': 15, 'back_day_limit': 5, 'max_index_loss_limit': 1.0000377884594276,
     'poc_value_limit': 0.8999913935687771}
    asset_index ={'stock': {'000300.SH': '沪深300', '000905.SH': '中证500'}, 'bond': {'H00140.SH': '上证五年期国债指数'}}
    # 风格轮动含债
    # fundPortfolioDemo.setMain(method='recyle_update', best_param_dic=param_dic,productFlag=True,
    #                           asset_index=asset_index)
