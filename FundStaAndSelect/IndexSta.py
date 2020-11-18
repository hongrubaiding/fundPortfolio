# -- coding: utf-8 --

'''
    统计wind导出的指数基金情况
'''

import pandas as pd
from datetime import datetime
import mylog as mylog
import numpy as np
from GetAndSaveWindData.GetIndexAndProduct import GetIndexAndProduct
from GetAndSaveWindData.GetDataTotalMain import GetDataTotalMain


class IndexSta:
    def __init__(self):
        self.logger = mylog.set_log()
        self.GetIndexAndProductDemo = GetIndexAndProduct()

    def calc_judge(self, temp_df):
        temp_dic = temp_df['市场综合3年评级'].dropna().to_dict()
        star_num = 0
        if temp_dic:
            for fund_code, star in temp_dic.items():
                star_num = star_num + (star - 0)
        return star_num

    def calc_company(self, company_df):
        score_dic = {}
        for col_name in company_df.columns:
            temp_se = company_df[col_name].sort_values(ascending=False)
            total_fund_code = temp_se.index.tolist()
            score_dic[col_name + '得分'] = {}
            if col_name in ['指数产品数量', '指数产品规模', '基金经理数', '基金经理平均年限', '最早指数产品成立年限', '指数增强型产品数量', '指数增强型产品规模', '市场综合评级',
                            '管理人成立年限', '基金管理人资产净值']:
                for fund_code in total_fund_code:
                    rank_score = (len(total_fund_code) - total_fund_code.index(fund_code)) / len(total_fund_code)
                    score_dic[col_name + '得分'][fund_code] = rank_score * 100
            elif col_name == '团队稳定性':
                for fund_code in total_fund_code:
                    rank_score = total_fund_code.index(fund_code) / len(total_fund_code)
                    score_dic[col_name + '得分'][fund_code] = rank_score * 100
            elif col_name == '基金经理成熟度':
                for fund_code in total_fund_code:
                    if temp_se[fund_code] == '老练':
                        rank_score = 100
                    elif temp_se[fund_code] == '稳重':
                        rank_score = 80
                    elif temp_se[fund_code] == '成熟':
                        rank_score = 60
                    elif temp_se[fund_code] == '青涩':
                        rank_score = 30
                    else:
                        rank_score = 50
                    score_dic[col_name + '得分'][fund_code] = rank_score
        score_df = pd.DataFrame(score_dic)
        score_df.to_excel("基金管理人评价指标得分.xlsx")
        return score_df

    def get_base_inf(self):
        file_path = r"D:\\工作文件\\策略说明报告\\"
        df = pd.read_excel(file_path + "指数基金评价.xlsx", index_col=0, converters={'基金管理人成立日期': str})
        improve_df = pd.read_excel(file_path + "指数基金评价.xlsx", index_col=0)
        dic_company = {}
        for company, temp_df in df.groupby('基金管理人中文名称'):
            dic_company[company] = {}
            dic_company[company]['指数产品数量'] = temp_df.shape[0]
            dic_company[company]['指数产品规模'] = temp_df['基金规模亿元'].sum()
            dic_company[company]['最早指数产品成立年限'] = (datetime.today() - temp_df['基金成立日'].min()).days / 365
            dic_company[company]['基金经理数'] = temp_df['基金经理数'].unique()[0]
            dic_company[company]['基金经理平均年限'] = temp_df['基金经理平均年限'].unique()[0]
            dic_company[company]['团队稳定性'] = temp_df['团队稳定性'].unique()[0]
            dic_company[company]['基金经理成熟度'] = temp_df['基金经理成熟度'].unique()[0]
            dic_company[company]['管理人成立年限'] = (datetime.today() - datetime.strptime(temp_df['基金管理人成立日期'].unique()[0],
                                                                                    "%Y%m%d")).days / 365

            dic_company[company]['基金管理人资产净值'] = temp_df['基金管理人资产净值合计'].unique()[0]
            dic_company[company]['市场综合评级'] = self.calc_judge(temp_df)
            improve_code_list = []
            for code in temp_df.index.tolist():
                if code in improve_df.index.tolist():
                    improve_code_list.append(code)
            if improve_code_list:
                temp_improve_df = temp_df.loc[improve_code_list]
                dic_company[company]['指数增强型产品数量'] = temp_improve_df.shape[0]
                dic_company[company]['指数增强型产品规模'] = temp_improve_df['基金规模亿元'].sum()
            else:
                dic_company[company]['指数增强型产品数量'] = 0
                dic_company[company]['指数增强型产品规模'] = 0
        company_df = pd.DataFrame(dic_company).T
        company_df.to_excel('基金管理人评价指标结果.xlsx')
        return company_df

    def calc_start_num(self,df,label=''):
        temp_df = df.sort_values(label,ascending=False)
        total_num = temp_df.shape[0]
        star_list = ['*****']*int(total_num * 0.125)
        star_list = star_list + ['****']*(int(total_num*0.35)-int(total_num*0.125))
        star_list = star_list + ['***']*(int(total_num*0.65)-int(total_num*0.35))
        star_list = star_list + ['**']*(int(total_num*0.875)-int(total_num*0.65))
        final_num = len(star_list)
        star_list_total =star_list+ ['*'] * (total_num - final_num)
        temp_df['综合星级评价'] = star_list_total
        return temp_df

    def calc_total_score(self, score_df):
        index_fund_weight = 0.5
        company_weight = 0.3
        team_weight = 0.2

        judge_flag = ['指数产品数量', '指数产品规模', '基金经理数', '基金经理平均年限', '最早指数产品成立年限', '指数增强型产品数量', '指数增强型产品规模', '市场综合评级',
                      '管理人成立年限', '基金管理人资产净值', '团队稳定性', '基金经理成熟度']
        dic_judge_weight = {}
        dic_judge_weight['指数产品数量得分'] = index_fund_weight * 0.3
        dic_judge_weight['指数产品规模得分'] = index_fund_weight * 0.3
        dic_judge_weight['最早指数产品成立年限得分'] = index_fund_weight * 0.2
        dic_judge_weight['指数增强型产品数量得分'] = index_fund_weight * 0.1
        dic_judge_weight['指数增强型产品规模得分'] = index_fund_weight * 0.1

        dic_judge_weight['管理人成立年限得分'] = company_weight * 0.2
        dic_judge_weight['基金管理人资产净值得分'] = company_weight * 0.5
        dic_judge_weight['市场综合评级得分'] = company_weight * 0.3

        dic_judge_weight['基金经理数得分'] = team_weight * 0.25
        dic_judge_weight['基金经理平均年限得分'] = team_weight * 0.25
        dic_judge_weight['基金经理成熟度得分'] = team_weight * 0.25
        dic_judge_weight['团队稳定性得分'] = team_weight * 0.25
        weight_flag_list = pd.Series(dic_judge_weight, name='评价指标权重')

        score = (score_df * weight_flag_list).sum(axis=1)
        score_df['基金管理人总得分'] = score
        score_df['旗下指数基金综合得分'] = score_df[['指数产品数量得分', '指数产品规模得分', '最早指数产品成立年限得分', '指数增强型产品数量得分', '指数增强型产品规模得分']].sum(
            axis=1)
        score_df['管理人概况综合得分'] = score_df[['管理人成立年限得分','基金管理人资产净值得分','市场综合评级得分']].sum(axis=1)
        score_df['旗下团队情况综合得分'] = score_df[['基金经理数得分','基金经理平均年限得分','团队稳定性得分','基金经理成熟度得分']].sum(axis=1)
        company_df = score_df[['旗下指数基金综合得分','管理人概况综合得分','旗下团队情况综合得分','基金管理人总得分']].sort_values('基金管理人总得分',ascending=False)
        company_df = self.calc_start_num(company_df,'基金管理人总得分')
        company_df.to_excel("基金管理人总得分.xlsx")
        return score

    def get_base_mangager_info(self, company_list=[]):
        if not company_list:
            file_path = r"D:\\工作文件\\策略说明报告\\"
            df = pd.read_excel(file_path + "指数基金评价.xlsx", index_col=0, converters={'基金管理人成立日期': str})
            dic_manager = {}
            for manager, temp_df in df.groupby('基金经理'):
                name_list = manager.split(',')
                if len(name_list) > 1:
                    for name in name_list:
                        new_df = temp_df.copy()
                        new_df['基金经理'] = name
                        manager_df = dic_manager.get(name, pd.DataFrame())
                        dic_manager[name] = pd.concat([manager_df, new_df], axis=0, sort=True)
                else:
                    manager_df = dic_manager.get(manager, pd.DataFrame())
                    dic_manager[manager] = pd.concat([manager_df, temp_df], axis=0, sort=True)

            dic_manager_judge = {}
            for manager_name, temp_manage_df in dic_manager.items():
                dic_manager_judge[manager_name] = {}
                dic_manager_judge[manager_name]['学历'] = temp_manage_df['学历'].unique()[0]
                dic_manager_judge[manager_name]['算术平均年化收益率'] = temp_manage_df['算术平均年化收益率'].unique()[0]
                dic_manager_judge[manager_name]['基金经理指数年化波动率'] = temp_manage_df['基金经理指数年化波动率'].unique()[0]
                dic_manager_judge[manager_name]['任职基金数'] = temp_manage_df['任职基金数'].unique()[0]
                dic_manager_judge[manager_name]['任职基金总规模'] = temp_manage_df['任职基金总规模'].unique()[0]
                dic_manager_judge[manager_name]['任职基金获奖记录'] = len(temp_manage_df['任职基金获奖记录'].dropna())
                dic_manager_judge[manager_name]['任职基金评级状况'] = self.calc_judge(temp_manage_df)
            manager_judge_df = pd.DataFrame(dic_manager_judge).T
            manager_judge_df.to_excel("基金经理评价指标结果.xlsx")
            return manager_judge_df

    def calc_manager(self, manager_judge_df):
        score_dic = {}
        for col_name in manager_judge_df.columns:
            temp_se = manager_judge_df[col_name].sort_values(ascending=False)
            total_fund_code = temp_se.index.tolist()
            score_dic[col_name + '得分'] = {}
            if col_name in ['任职基金数', '任职基金评级状况', ]:
                for fund_code in total_fund_code:
                    temp_value = temp_se[fund_code]
                    if np.isnan(temp_value):
                        temp_value = temp_se.mean()
                    rank_score = (temp_value - temp_se.min()) / (temp_se.max() - temp_se.min())
                    score_dic[col_name + '得分'][fund_code] = rank_score * 100
            elif col_name in ['算术平均年化收益率', '任职基金总规模', '基金经理指数年化波动率']:
                for fund_code in total_fund_code:
                    rank_score = (len(total_fund_code) - total_fund_code.index(fund_code)) / len(total_fund_code)
                    score_dic[col_name + '得分'][fund_code] = rank_score * 100
            elif col_name == '学历':
                for fund_code in total_fund_code:
                    temp_value = temp_se[fund_code]
                    if temp_value == '博士':
                        rank_score = 0.9
                    elif temp_value == '硕士':
                        rank_score = 0.7
                    else:
                        rank_score = 0.5
                    score_dic[col_name + '得分'][fund_code] = rank_score * 100
            elif col_name == '任职基金获奖记录':
                for fund_code in total_fund_code:
                    temp_value = temp_se[fund_code]
                    if temp_value >= 2:
                        rank_score = 0.9
                    elif temp_value == 1:
                        rank_score = 0.7
                    else:
                        rank_score = 0.5
                    score_dic[col_name + '得分'][fund_code] = rank_score * 100
        score_df = pd.DataFrame(score_dic)
        score_df.to_excel("基金经理评价指标得分.xlsx")
        return score_df

    def calc_total_manager_score(self, manager_score_df):
        base_info_weight = 0.5
        manage_fund_weight = 0.5

        dic_judge_weight = {}
        dic_judge_weight['任职基金数得分'] = manage_fund_weight * 0.3
        dic_judge_weight['任职基金评级状况得分'] = manage_fund_weight * 0.15
        dic_judge_weight['基金经理指数年化波动率得分'] = base_info_weight * 0.4
        dic_judge_weight['算术平均年化收益率得分'] = base_info_weight * 0.5
        dic_judge_weight['任职基金总规模得分'] = manage_fund_weight * 0.5

        dic_judge_weight['学历得分'] = base_info_weight * 0.1
        dic_judge_weight['任职基金获奖记录得分'] = manage_fund_weight * 0.05
        weight_flag_list = pd.Series(dic_judge_weight, name='评价指标权重')
        score = (manager_score_df * weight_flag_list).sum(axis=1).sort_values(ascending=False)
        manager_score_df['基金经理总得分'] = score
        manager_score_df['基本信息概况'] = manager_score_df[['学历得分','算术平均年化收益率得分','基金经理指数年化波动率得分']].sum(axis=1)
        manager_score_df['管理产品概况'] = manager_score_df[['任职基金数得分', '任职基金评级状况得分', '任职基金总规模得分','任职基金获奖记录得分']].sum(axis=1)
        manager_df = manager_score_df[['基本信息概况','管理产品概况','基金经理总得分']]
        manager_df = self.calc_start_num(manager_df, '基金经理总得分')
        score.name = '基金经理总得分'
        manager_df.to_excel("基金经理总得分.xlsx")
        return score

    def get_base_fund_info(self, company_list=[]):
        '''
        指数基金公共指标池评价
        :param company_list: 指定的基金管理人旗下产品评价，为空时默认评价全部
        :return:
        '''
        file_path = r"D:\\工作文件\\策略说明报告\\"
        df = pd.read_excel(file_path + "基金产品评价指标7月.xlsx", index_col=0, )
        improve_df = pd.read_excel(file_path + "增强指数基金7月.xlsx", index_col=0, )
        index_code_list = [code for code in df.index.tolist() if code not in improve_df.index.tolist()]
        fund_df = df.loc[index_code_list]
        if company_list:
            fund_df['证券代码'] = fund_df.index.tolist()
            fund_df.set_index(['基金管理人', '基金经理(现任)', '证券代码'], inplace=True, drop=False)
            fund_df = fund_df.loc[company_list]
        return fund_df

    def calc_fund(self, fund_judge_df):
        '''
        证券代码	证券简称	基金管理人	托管费率	跟踪误差(跟踪指数)	跟踪指数代码	基金经理(现任)	近3月回报	近6月回报	近1年回报	今年以来回报
        	近3月年化波动率	"近6月年化波动率   近1年年化波动率	今年以来年化波动率	基金规模(合计)	管理费率
        :param fund_judge_df:
        :return:
        '''
        score_dic = {}
        judge_list = ['跟踪误差(跟踪指数)', '近3月回报', '近6月回报', '近1年回报', '今年以来回报', '基金规模(合计)', '近3月年化波动率', '近6月年化波动率', '近1年年化波动率',
                      '今年以来年化波动率', '管理费率', '托管费率']
        for col_name in fund_judge_df.columns:
            if col_name not in judge_list:
                continue

            temp_new_se = fund_judge_df[col_name]
            if col_name == '跟踪误差(跟踪指数)':
                temp_se = temp_new_se.fillna(temp_new_se.mean())
            elif col_name in ['近3月回报', '近6月回报', '近1年回报', '今年以来回报', ]:
                temp_se = temp_new_se.fillna(-np.inf)
            elif col_name in ['近3月年化波动率', '近6月年化波动率', '近1年年化波动率', '今年以来年化波动率']:
                temp_se = temp_new_se.copy()
                rete_se = fund_judge_df[col_name[:col_name.index('年化')] + '回报']
                for index in rete_se.index.tolist():
                    if np.isnan(rete_se[index]):
                        temp_se[index] = np.nan
                temp_se = temp_se.fillna(np.inf)
            else:
                temp_se = temp_new_se.copy()

            temp_se = temp_se.sort_values(ascending=False)
            total_fund_code = temp_se.index.tolist()

            score_dic[col_name + '得分'] = {}
            if col_name in ['跟踪误差(跟踪指数)', '近3月回报', '近6月回报', '近1年回报', '今年以来回报', '基金规模(合计)']:

                for fund_code in total_fund_code:
                    if not np.isinf(temp_se[fund_code]):
                        rank_score = (len(total_fund_code) - total_fund_code.index(fund_code)) / len(total_fund_code)
                        score_dic[col_name + '得分'][fund_code] = rank_score * 100
                    else:
                        score_dic[col_name + '得分'][fund_code] = 0
            elif col_name in ['近3月年化波动率', '近6月年化波动率', '近1年年化波动率', '今年以来年化波动率']:
                for fund_code in total_fund_code:
                    if not np.isinf(temp_se[fund_code]):
                        rank_score = (total_fund_code.index(fund_code) + 1) / len(total_fund_code)
                        score_dic[col_name + '得分'][fund_code] = rank_score * 100
                    else:
                        score_dic[col_name + '得分'][fund_code] = 0
            elif col_name in ['管理费率', '托管费率']:
                if col_name == '托管费率':
                    for fund_code in total_fund_code:
                        if temp_se[fund_code] <= 0.05:
                            rank_score = 100
                        elif 0.05 < temp_se[fund_code] <= 0.1:
                            rank_score = 70
                        elif 0.1 < temp_se[fund_code] <= 0.15:
                            rank_score = 60
                        elif 0.15 < temp_se[fund_code] <= 0.18:
                            rank_score = 50
                        elif 0.18 < temp_se[fund_code] <= 0.2:
                            rank_score = 40
                        elif 0.2 < temp_se[fund_code] <= 0.22:
                            rank_score = 30
                        else:
                            rank_score = 10
                        score_dic[col_name + '得分'][fund_code] = rank_score
                elif col_name == '管理费率':
                    for fund_code in total_fund_code:
                        if temp_se[fund_code] <= 0.15:
                            rank_score = 100
                        elif 0.15 < temp_se[fund_code] <= 0.3:
                            rank_score = 80
                        elif 0.3 < temp_se[fund_code] <= 0.5:
                            rank_score = 60
                        elif 0.5 < temp_se[fund_code] <= 0.75:
                            rank_score = 50
                        elif 0.75 < temp_se[fund_code] <= 0.8:
                            rank_score = 40
                        else:
                            rank_score = 20
                        score_dic[col_name + '得分'][fund_code] = rank_score
        score_df = pd.DataFrame(score_dic)
        score_df.to_excel("基金产品角度评价指标得分.xlsx")
        return score_df

    def get_fund_index(self, fund_code):
        not_dead_df = self.GetIndexAndProductDemo.get_fund_index_info(fund_code=fund_code)
        update_df_list = []
        for fund_name, temp_df in not_dead_df.groupby('fund_name'):
            if temp_df.shape[0] > 1:
                inter_word = 0
                target_row = 0
                for row_num in range(len(temp_df)):
                    index_c_fullname = temp_df.iloc[row_num]['index_c_fullname']
                    temp_inter = len(set(index_c_fullname).intersection(set(fund_name)))
                    if temp_inter > inter_word:
                        inter_word = temp_inter
                        target_row = row_num
                temp_se = temp_df.iloc[target_row]
                temp_df = pd.DataFrame(temp_se, columns=[temp_df.index.tolist()[0]]).T
            update_df_list.append(temp_df)
        update_df = pd.concat(update_df_list, axis=0, sort=True)
        return update_df

    def calc_total_fund_score(self, fund_score_df):
        '''
        基金产品角度总得分
        :param fund_score_df:
        :return:
        '''

        '''
        托管费率得分	跟踪误差(跟踪指数)得分	近3月回报得分	近6月回报得分	近1年回报得分	今年以来回报得分	近3月年化波动率得分
        	近6月年化波动率得分	近1年年化波动率得分	今年以来年化波动率得分	基金规模(合计)得分	管理费率得分

        '''
        rate_weight = 0.25
        risk_weight = 0.25

        dic_judge_weight = {}
        dic_judge_weight['托管费率得分'] = 0.05
        dic_judge_weight['管理费率得分'] = 0.05
        dic_judge_weight['跟踪误差(跟踪指数)得分'] = 0.25
        dic_judge_weight['近3月回报得分'] = rate_weight * 0.1
        dic_judge_weight['近6月回报得分'] = rate_weight * 0.2
        dic_judge_weight['近1年回报得分'] = rate_weight * 0.4
        dic_judge_weight['今年以来回报得分'] = rate_weight * 0.3

        dic_judge_weight['近3月年化波动率得分'] = risk_weight * 0.1
        dic_judge_weight['近6月年化波动率得分'] = risk_weight * 0.2
        dic_judge_weight['近1年年化波动率得分'] = risk_weight * 0.4
        dic_judge_weight['今年以来年化波动率得分'] = risk_weight * 0.3

        dic_judge_weight['基金规模(合计)得分'] = 0.15
        weight_flag_list = pd.Series(dic_judge_weight, name='评价指标权重')
        score = (fund_score_df * weight_flag_list).sum(axis=1).sort_values(ascending=False)
        score.name = '基金产品角度总得分'
        score.sort_values(ascending=False, inplace=True)

        score_df = pd.DataFrame(score)
        total_code = [index_tuple[2].split('.')[0] for index_tuple in score.index.tolist()]
        score_df['数据库基金代码'] = total_code
        score_df['基金管理人'] = [index_tuple[0] for index_tuple in score.index.tolist()]
        score_df['基金经理'] = [index_tuple[1] for index_tuple in score.index.tolist()]
        score_df.set_index(keys='数据库基金代码', drop=False, inplace=True)

        fund_index_df = self.get_fund_index(fund_code=total_code)
        mysql_df = fund_index_df[
            ['fund_type', 'product_type', 'fund_name', 'establish_date', 'indx_sname', 'class_classify', 'index_code']]
        mysql_df.drop(['162714'],inplace=True)
        score_df.drop(['162714'], inplace=True)

        total_df = pd.concat([score_df, mysql_df], axis=1, sort=True)
        name_dic = {"fund_type": "基金类型", "product_type": "产品类型", "fund_name": "基金名称", "establish_date": "基金成立日",
                    "indx_sname": "跟踪指数名称", "class_classify": "跟踪指数类型", "index_code": "跟踪指数代码"}
        total_df.rename(columns=name_dic, inplace=True)
        total_df = self.get_lack_index_style(total_df)
        total_df['基金代码'] = total_df.index.tolist()
        writer = pd.ExcelWriter('基金产品角度总得分.xlsx')
        for index_style,temp_df in total_df.groupby('跟踪指数类型'):
            if index_style in ['规模','行业','主题','风格','策略']:
                temp_df = self.calc_start_num(temp_df, '基金产品角度总得分')
                temp_df.to_excel(writer, index=False,sheet_name='%s型'%index_style)
        writer.save()
        return

    def get_lack_index_style(self,total_df):
        GetDataTotalMainDemo = GetDataTotalMain(data_resource='wind')
        temp_se = total_df['跟踪指数类型']
        have_se = temp_se.dropna()
        lack_fund_code = [code for code in temp_se.index.tolist() if code not in have_se.index.tolist()]
        lack_code = [code+'.OF' for code in lack_fund_code]

        temp_df = GetDataTotalMainDemo.get_fund_base_info(fund_code_list=lack_code).sort_values('跟踪指数代码')
        temp_df['mysql_code'] = [code.split('.')[0] for code in temp_df.index.tolist()]
        temp_df['基金成立日'] = [datetime.strftime(date_str,'%y-%m-%d') for date_str in temp_df['基金成立日'].tolist()]
        temp_df.set_index('mysql_code',inplace=True,)
        taret_lack_df = total_df.loc[lack_fund_code]
        taret_lack_df['基金类型'] = temp_df['基金类型']
        taret_lack_df['产品类型'] = temp_df['产品类型']
        taret_lack_df['基金名称'] = temp_df['基金全称']
        taret_lack_df['基金成立日'] = temp_df['基金成立日']
        taret_lack_df['跟踪指数代码'] = temp_df['跟踪指数代码']

        index_code_list = [index_code.split('.')[0] for index_code in temp_df['跟踪指数代码'].tolist() if index_code]
        index_info_df = self.GetIndexAndProductDemo.get_index_code_info(index_code=index_code_list)

        index_style_list = []
        for index_code in taret_lack_df['跟踪指数代码']:
            if index_code:
                temp_code = index_code.split('.')[0]
                if temp_code in index_info_df.index.tolist():
                    class_classify = index_info_df.loc[temp_code]['class_classify']
                    if class_classify=='国证综合指数':
                        class_classify = '规模'
                    elif class_classify in ['定制指数','国证跨境未分类']:
                        class_classify = '主题'
                    index_style_list.append(class_classify)
                else:
                    if index_code.split('.')[1] in ['MI', 'CSI'] and index_code.split('.')[0][0] == '7':
                        if index_code.split('.')[0][:6] in ['707918', '714032', '714721', '718465']:
                            index_style_list.append('策略')
                        else:
                            index_style_list.append('规模')
                    elif index_code.split('.')[0] in ['399550', '980001', 'CSPSADRP', ]:
                        index_style_list.append('主题')
                    elif index_code.split('.')[0] in ['830009', 'HSI', 'FCAH50', 'SPCQVCP','136056L'] or index_code.split('.')[
                        1] == 'HI':
                        index_style_list.append('规模')
                    elif index_code.split('.')[0] in ['930793']:
                        index_style_list.append('行业')
                    elif index_code.split('.')[0] in ['930840', 'SPACEVCP', 'SPAHLVCP', 'SPCLLHCP']:
                        index_style_list.append('策略')
                    elif index_code.split('.')[0] in ['DCESMFI', 'IMCI']:
                        index_style_list.append('商品')
                    else:
                        self.logger.info("缺失未处理的指数:%s"%index_code)
            else:
                index_style_list.append('规模')
        taret_lack_df['跟踪指数类型'] = index_style_list
        result_df = pd.concat([total_df.loc[have_se.index.tolist()],taret_lack_df],axis=0,sort=True)
        return result_df

    def get_main(self):
        # 基金管理人得分
        # self.logger.info("管理人评价指标计算....")
        company_df = self.get_base_inf()
        company_score_df = self.calc_company(company_df)
        total_company_score = self.calc_total_score(company_score_df)
        #
        # # 基金经理得分
        # self.logger.info("基金经理评价指标计算....")
        # manager_judge_df = self.get_base_mangager_info()
        # manager_score_df = self.calc_manager(manager_judge_df)
        # total_manager_score = self.calc_total_manager_score(manager_score_df)

        # 基金产品角度得分
        self.logger.info("基金产品评价指标计算....")
        company_list = total_company_score.index.tolist()
        fund_judge_df = self.get_base_fund_info(company_list=company_list)
        fund_score_df = self.calc_fund(fund_judge_df)
        self.calc_total_fund_score(fund_score_df)


if __name__ == '__main__':
    IndexStaDemo = IndexSta()
    IndexStaDemo.get_main()
