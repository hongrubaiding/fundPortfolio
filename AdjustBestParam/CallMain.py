# -- coding: utf-8 --

from AdjustBestParam.FindBestParam import FindBestParam
import pandas as pd
import mylog as mylogdemo
from MainEntrance.fundPortfolio import fundPortfolio
from AdjustBestParam.WindPMS import WindPMS
import numpy as np
from AdjustBestParam.industry_recyle import IndustryRecyle


class CallMain:
    def __init__(self):
        self.logger = mylogdemo.set_log()

    def get_PMS_format(self, file_path, param_str):
        product_df = pd.read_excel(file_path + '产品组合仓位表.xlsx', index_col=0)
        WindPMSDemo = WindPMS()
        WindPMSDemo.calc_main(total_pos_df=product_df, portfolio_num=param_str)

    def fix_portfolio_best_param(self):
        # param_str = "组合31号"  # 大类资产轮动
        # param_str='组合32号'       #风格轮动
        # param_str = '行业'
        # param_str='主题'
        param_str = '行业主题'

        fund_type = 'ETF'
        # fund_type = 'OTC'

        file_str = param_str + fund_type
        total_df = pd.read_excel("组合明细.xlsx", index_col=0)
        if fund_type == 'ETF':
            if param_str == "组合32号":
                best_param_dic = {'adjust_day_limit': 9, 'back_day_limit': 7,
                                  'max_index_loss_limit': 1.0336336758278335,
                                  'poc_value_limit': 0.4002284797771605}  # 组合32号短周期场内
            elif param_str == "组合31号":
                best_param_dic = {'adjust_day_limit': 6, 'max_index_loss_limit': 1.0427257786765352,
                                  'poc_value_limit': 0.5181759212161646}
            elif param_str in ['行业', '主题', '行业主题']:
                if param_str == '行业':
                    best_param_dic = {'adjust_day_limit': 9, 'back_day_limit': 6,
                                      'max_index_loss_limit': 1.003732683071061,
                                      'poc_value_limit': 0.8918295289003106}  # 场内短周期最优参数

                    # best_param_dic = {'adjust_day_limit': 5, 'back_day_limit': 7, 'max_index_loss_limit': 1.0438246646746496,
                    #                   'poc_value_limit': 0.8998182356292519}
                elif param_str == '主题':
                    best_param_dic = {'adjust_day_limit': 11, 'back_day_limit': 10,
                                      'max_index_loss_limit': 1.0981107733412536,
                                      'poc_value_limit': 0.8809468667158603}
                else:
                    best_param_dic = {'adjust_day_limit': 11, 'adjust_maxdown': 0.06745476221138974,
                                      'back_day_limit': 7, 'poc_value_limit': 0.7115231344778375,
                                      }  # 投顾产品
                    best_param_dic = {'back_day_limit': 6, 'corr_limit': 0.9871519191133329,
                                      'max_loss_limit': 0.07901894294893107}  # 新止损优化
                    # best_param_dic = {'back_day_limit': 9, 'corr_limit': 0.9860977873659047, 'max_loss_limit': 0.06353494612453964}
                    # best_param_dic={'adjust_day_limit': 6, 'back_day_limit': 7, 'poc_num': 3}
                    best_param_dic = {'back_day_limit': 14, 'corr_limit': 0.8327902772212527,
                                      'down_max_num': 0.447583290105109, 'judge_market': 52,
                                      'max_loss_limit': 0.057219432873010984, 'up_day_num': 0.8399154687488591,
                                      'up_max': 0.2705637796307785, 'vol_rate': 0.7675222487190907}
                    best_param_dic = {'back_day_limit': 17, 'conti_up_day': 0.10402050680807062,
                                      'corr_limit': 0.9434849921258115, 'down_max_num': 0.6632983776945698,
                                      'judge_market': 30, 'max_loss_limit': 0.051185163625393305,
                                      'up_day_num': 0.8997744660289387, 'up_max': 0.8479220579989855,
                                      'vol_rate': 0.10309199514290202}
                method = 'industry_recyle'
                # method='industry_recyle_equ'
                IndustryRecyleDemo = IndustryRecyle()
                # industry_index_name_dic, product_name_dic = IndustryRecyleDemo.get_ZZmain(fund_type=fund_type)
                industry_index_name_dic, product_name_dic = IndustryRecyleDemo.get_fund_index(fund_type=fund_type,
                                                                                              style_flag=param_str)
                asset_index = {'stock': industry_index_name_dic, 'bond': {'H00140.SH': u'上证五年期国债指数'}}
                if 'H00140.SH' not in product_name_dic:
                    product_name_dic['H00140.SH'] = {'511880.SH': "银华日利ETF "}
                fundPortfolioDemo = fundPortfolio(startDate='2015-09-01', file_path=param_str)
                # fundPortfolioDemo = fundPortfolio(startDate='2019-01-01', file_path=param_str)
                fundPortfolioDemo.setMain(method=method, productFlag=True, asset_index=asset_index,
                                          best_param_dic=best_param_dic, product_name_dic=product_name_dic,
                                          fund_type=fund_type)
                reslut_file_loc = fundPortfolioDemo.PathFolder + method + '\\'
                self.get_PMS_format(file_path=reslut_file_loc, param_str=file_str)
                return
        else:
            if param_str == '组合31号':
                best_param_dic = {'adjust_day_limit': 54, 'back_day_limit': 29,
                                  'max_index_loss_limit': 1.1330075022050305,
                                  'poc_value_limit': 0.8914724483780754}
            elif param_str == '组合32号':
                best_param_dic = {'adjust_day_limit': 9, 'back_day_limit': 7,
                                  'max_index_loss_limit': 1.0336336758278335,
                                  'poc_value_limit': 0.4002284797771605}  # 组合32号短周期场内
            elif param_str in ['行业', '主题', '行业主题']:
                # method = 'industry_recyle'
                # method = 'industry_recyle_stock'
                method = 'industry_recyle_mean_var_stock'
                if method == 'industry_recyle_stock':
                    best_param_dic = {'adjust_day_limit': 42, 'back_day_limit': 29}
                elif method == 'industry_recyle':
                    best_param_dic = {'adjust_day_limit': 33, 'back_day_limit': 17,
                                      'max_index_loss_limit': 1.0087987474146602,
                                      'poc_value_limit': 0.402127727489241}  # 场外最优参数
                elif method == 'industry_recyle_mean_var_stock':
                    # best_param_dic = {'adjust_day_limit': 49, 'back_day_limit': 114}
                    # best_param_dic = {'adjust_day_limit': 18, 'back_day_limit': 40}
                    # best_param_dic = {'adjust_day_limit': 39, 'back_day_limit': 34}  # 行业
                    best_param_dic = {'adjust_day_limit': 24, 'back_day_limit': 30}  # 主题

                IndustryRecyleDemo = IndustryRecyle()
                industry_index_name_dic, product_name_dic = IndustryRecyleDemo.get_fund_index(fund_type=fund_type,
                                                                                              style_flag=param_str)
                if method not in ['industry_recyle_stock', 'industry_recyle_mean_var_stock']:
                    asset_index = {'stock': industry_index_name_dic, 'bond': {'H00140.SH': u'上证五年期国债指数'}}
                    if 'H00140.SH' not in product_name_dic:
                        product_name_dic['H00140.SH'] = {'000088.OF': "嘉实中期国债ETF联接C "}
                else:
                    asset_index = {'stock': industry_index_name_dic, }
                fundPortfolioDemo = fundPortfolio(startDate='2013-09-01', file_path=param_str)
                fundPortfolioDemo.setMain(method=method, productFlag=True, asset_index=asset_index,
                                          best_param_dic=best_param_dic, product_name_dic=product_name_dic,
                                          fund_type=fund_type)
                reslut_file_loc = fundPortfolioDemo.PathFolder + method + '\\'
                self.get_PMS_format(file_path=reslut_file_loc, param_str=file_str)
                return

        asset_index = eval(total_df.loc[param_str]['模型参数'])
        method = total_df.loc[param_str]['配置模型']
        self.logger.info("----------------------best_param----------------->")
        fundPortfolioDemo = fundPortfolio(startDate='2015-09-01', file_path=param_str)
        fundPortfolioDemo.setMain(method=method, productFlag=True, asset_index=asset_index,
                                  best_param_dic=best_param_dic, fund_type=fund_type)
        reslut_file_loc = fundPortfolioDemo.PathFolder + method + '\\'
        self.get_PMS_format(file_path=reslut_file_loc, param_str=file_str)
        return

    def get_portfoio_with_best_param(self, param_str=''):
        if not param_str:
            param_str = "组合34号"
        param_df = pd.read_excel("%s最优参数.xlsx" % param_str, index_col=0)
        # param_df = pd.read_excel("组合31号最优参长调仓日期.xlsx", index_col=0)
        total_df = pd.read_excel("组合明细.xlsx", index_col=0)
        asset_index = eval(total_df.loc[param_str]['模型参数'])
        method = total_df.loc[param_str]['配置模型']

        # method = 'industry_recyle'
        param_info_dic = eval(param_df.loc['misc'][method])
        best_param_dic = {}
        for param_key, param_values in param_info_dic['vals'].items():
            best_param_dic[param_key] = param_values[0]
        # best_param_dic = {'adjust_day_limit': 26, 'back_day_limit': 16, 'max_index_loss_limit': 1.0163546802363896, 'poc_value_limit': 0.8998090608862988}#组合33阶段参数
        # best_param_dic={'adjust_day_limit': 73, 'back_day_limit': 100, 'bond_limit': 0.07325363231739307, 'com_limit': 0.7055617284378413, 'xfc_back_day': 30, 'xfc_chage_rate': 1.1837053863199578, 'control_method': 'xfc'}
        # best_param_dic={'adjust_day_limit': 9, 'back_day_limit': 7, 'max_index_loss_limit': 1.0336336758278335, 'poc_value_limit': 0.4002284797771605}#组合32号短周期场内
        self.logger.info("----------------------best_param----------------->")
        fundPortfolioDemo = fundPortfolio(startDate='2015-09-01', file_path=param_str)
        # fund_type = 'ETF'
        fund_type = 'OTC'
        fundPortfolioDemo.setMain(method=method, productFlag=True, asset_index=asset_index,
                                  best_param_dic=best_param_dic, fund_type=fund_type)
        reslut_file_loc = fundPortfolioDemo.PathFolder + method + '\\'
        self.get_PMS_format(file_path=reslut_file_loc, param_str=param_str)

    def get_industry_recyle(self):
        '''
        行业轮动、主题轮动
        :return:
        '''

        # fund_type = 'OTC'
        fund_type = 'ETF'

        # style_flag = '主题'
        # style_flag = '行业'
        style_flag = '行业主题'
        # style_flag = '策略'

        method = 'industry_recyle'
        # method ="industry_recyle_equ"
        # method = 'industry_recyle_stock'
        # method = 'industry_recyle_mean_var_stock'
        # method = 'mean_var'

        IndustryRecyleDemo = IndustryRecyle()
        industry_index_name_dic, product_name_dic = IndustryRecyleDemo.get_fund_index(fund_type=fund_type,
                                                                                      style_flag=style_flag)
        portfolio_str = '%s轮动组合99%s+%s' % (style_flag, fund_type, method)  # 1到14
        if method == 'industry_recyle':
            asset_index = {'stock': industry_index_name_dic, 'bond': {'H00140.SH': u'上证五年期国债指数'}}
            if 'H00140.SH' not in product_name_dic:
                if fund_type == 'ETF':
                    product_name_dic['H00140.SH'] = {'511010.SH': "国债ETF "}
                else:
                    product_name_dic['H00140.SH'] = {'000088.OF': "嘉实中期国债ETF联接C "}
        else:
            asset_index = {'stock': industry_index_name_dic, }

        FindBestParamDemo = FindBestParam(method, param_file_name=portfolio_str)
        target = 'maxreturn'
        # self.logger = mylogdemo.set_log(portfolio_str + '行业短周期有风控')
        self.logger = mylogdemo.set_log(portfolio_str + method)
        FindBestParamDemo.try_find_param(asset_index, control_method={}, product_name_dic=product_name_dic,
                                         target=target)

    def get_portfolio_industry_recyle_param(self):
        param_str = "行业轮动"
        add_str = ''
        param_str = param_str + add_str
        method = 'industry_recyle'
        IndustryRecyleDemo = IndustryRecyle()
        fund_type = 'ETF'
        # fund_type='OTC'
        industry_index_name_dic, product_name_dic = IndustryRecyleDemo.get_main(fund_type=fund_type)
        asset_index = {'stock': industry_index_name_dic, 'bond': {'H00140.SH': u'上证五年期国债指数'}}
        if 'H00140.SH' not in product_name_dic:
            if fund_type == 'ETF':
                product_name_dic['H00140.SH'] = {'511010.SH': "国债ETF "}
            else:
                product_name_dic['H00140.SH'] = {'000088.OF': "嘉实中期国债ETF联接C "}
        # best_param_dic ={'adjust_day_limit': 59, 'back_day_limit': 22, 'max_index_loss_limit': 1.0658809306041392, 'poc_value_limit': 0.795065864572404}#回撤阈值0.15，长周期参数1

        # best_param_dic={'adjust_day_limit': 43, 'back_day_limit': 7, 'max_index_loss_limit': 1.0588023004774523, 'poc_value_limit': 0.6781040531662471} #场内长周期adjust!=back，长周期参数2
        best_param_dic = {'adjust_day_limit': 9, 'back_day_limit': 6, 'max_index_loss_limit': 1.003732683071061,
                          'poc_value_limit': 0.8918295289003106}  # 场内短周期最优参数
        # best_param_dic={'adjust_day_limit': 33, 'back_day_limit': 17, 'max_index_loss_limit': 1.0087987474146602, 'poc_value_limit': 0.402127727489241}#场外最优参数
        fundPortfolioDemo = fundPortfolio(startDate='2015-09-01', file_path=param_str)
        fundPortfolioDemo.setMain(method=method, productFlag=True, asset_index=asset_index,
                                  best_param_dic=best_param_dic, product_name_dic=product_name_dic, fund_type=fund_type)
        reslut_file_loc = fundPortfolioDemo.PathFolder + method + '\\'
        self.get_PMS_format(file_path=reslut_file_loc, param_str=param_str)

    #
    def calc_much_porfolio(self):
        for portfolio_num in list(range(1, 26)):
            param_str = "组合%s号" % portfolio_num
            try:
                self.get_portfoio_with_best_param(param_str)
            except:
                self.logger.info(param_str + '运行异常，检查！')

    def get_pre_data(self, target='maxreturn'):
        total_df = pd.read_excel("组合明细.xlsx", index_col=0)
        portfolio_str = '组合34号'
        portfolio_total_str = portfolio_str  # 1到14
        self.logger = mylogdemo.set_log(portfolio_total_str + '长周期')
        asset_index = eval(total_df.loc[portfolio_str]['模型参数'])

        control_method = {}
        # control_method = total_df.loc[portfolio_str]['风控参数']
        # if np.isnan(control_method):
        #     control_method = {}
        # else:
        #     control_method = eval(total_df.loc[portfolio_str]['风控参数'])
        # control_method = eval(total_df.loc[portfolio_str]['风控参数'])
        method = total_df.loc[portfolio_str]['配置模型']
        # method='industry_recyle'
        FindBestParamDemo = FindBestParam(method, param_file_name=portfolio_total_str)
        FindBestParamDemo.try_find_param(asset_index, control_method, target=target)

    def call_find_best_param(self, method):
        FindBestParamDemo = FindBestParam(method)
        FindBestParamDemo.try_find_param()


if __name__ == "__main__":
    CallMainDemo = CallMain()
    # CallMainDemo.call_find_best_param(method='risk_parity')
    # CallMainDemo.get_pre_data()
    # CallMainDemo.get_portfoio_with_best_param()
    # CallMainDemo.calc_much_porfolio()
    # CallMainDemo.calc_format_portfolio()
    # CallMainDemo.get_industry_recyle()
    # CallMainDemo.get_portfolio_industry_recyle_param()
    CallMainDemo.fix_portfolio_best_param()
