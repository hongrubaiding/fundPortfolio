# -- coding: utf-8 --

import pandas as pd
from GetAndSaveWindData.MysqlCon import MysqlCon
from GetAndSaveWindData.GetDataTotalMain import GetDataTotalMain
import numpy as np


class IndustryRecyle:
    def __init__(self):
        MysqlConDemo = MysqlCon()
        self.engine = MysqlConDemo.getMysqlCon('engine')
        self.GetDataTotalMainDemo = GetDataTotalMain(data_resource='wind')
        self.industry_trade_limit = 20000000

    def remove_deadline_product(self, df):
        '''
            过滤已清算的基金
        :param df:
        :return:
        '''
        remove_df = pd.read_excel("清算基金.xlsx")
        temp_df = df.set_index('fund_code', drop=True)
        remove_code = list(set(remove_df['证券代码'].tolist()).intersection(df['fund_code'].tolist()))
        target_code = [code for code in df['fund_code'].tolist() if code not in remove_code]
        result_df = temp_df.loc[target_code]
        result_df['fund_code'] = result_df.index.tolist()
        return result_df

    def remove_index_same_name(self, df):
        '''
        过滤因指数简称相同而带来的bug
        :param df:
        :return:
        '''
        remove_index_c_fullname = []
        for fund_code, temp_df in df.groupby('fund_code'):
            if temp_df.shape[0] > 1:
                for num in range(temp_df.shape[0]):
                    index_c_fullname = temp_df.iloc[num]['index_c_fullname']
                    fund_name = temp_df.iloc[num]['fund_name']
                    if fund_name.find(index_c_fullname) == -1:
                        remove_index_c_fullname.append(index_c_fullname)

        num_list = []
        if remove_index_c_fullname:
            for index_num in range(df.shape[0]):
                if df.iloc[index_num]['index_c_fullname'] not in remove_index_c_fullname:
                    num_list.append(index_num)
            result = df.iloc[num_list]
        else:
            result = df
        return result

    def code_last_add(self, fund_type, df, label=''):
        code_list = df[label].tolist()
        if fund_type == 'ETF':
            fund_code_list = []
            for code in code_list:
                if code[0] == '5':
                    code = code + '.SH'
                elif code[0] == '1':
                    code = code + '.SZ'
                fund_code_list.append(code)
        elif fund_type == 'OTC':
            fund_code_list = [code + '.OF' for code in code_list]
        elif fund_type == 'index':
            fund_code_list = []
            for code in code_list:
                if code[0] == '0':
                    # if code in ['000859','000861','000860','000922','000978','000171','000824']:
                    if code in ['000859', '000860', '000861', '000922', '000963', '000978', '000964',
                                '000969', '000961', '000979', '000806']:
                        code = code + '.CSI'
                    else:
                        code = code + '.SH'
                elif code[0] == '3':
                    code = code + '.SZ'
                elif code[0] == 'H' or code[:2] in ['93', '95', '99']:
                    code = code + '.CSI'
                elif code == '980017':
                    code = code + '.CNI'
                elif code[:2] == 'CN':
                    code = code + '.CNI'
                fund_code_list.append(code)
        return fund_code_list

    def get_index_product_dic(self, df, fund_type='ETF'):
        temp_total_df = df.copy()
        index_name_dic = {}
        product_name_dic = {}
        size_df = self.GetDataTotalMainDemo.get_fund_size(code_list=df['fund_code'].tolist())
        if fund_type == 'ETF':
            for index_code, temp_df in df.groupby('index_code'):
                # trade_max = size_df['日均成交额'].loc[temp_df.index.tolist()].max()
                trade_max = size_df.loc[temp_df.index.tolist()].max()
                if np.isnan(trade_max) or trade_max < self.industry_trade_limit:
                    continue
                # product_code = size_df['日均成交额'].loc[temp_df.index.tolist()].argmax()
                product_code = size_df.loc[temp_df.index.tolist()].argmax()
                index_name_dic[index_code] = temp_df.iloc[0]['indx_sname']
                product_name_dic[index_code] = {product_code: temp_df.loc[product_code]['fund_name']}
        else:
            for index_code, temp_df in df.groupby(by='index_code'):
                if temp_df['establish_date'].min() >= '2018-01-01':
                    continue
                target_df = temp_df[temp_df['establish_date'] == temp_df['establish_date'].min()]

                if target_df.shape[0] == 1:
                    index_name_dic[index_code] = temp_df.iloc[0]['indx_sname']
                    product_name_dic[index_code] = {target_df.iloc[0]['fund_code']: target_df.iloc[0]['fund_name']}
                    continue
                elif target_df.shape[0] == 3:
                    for code in target_df['fund_code'].tolist():
                        if code[:2] == '16':
                            index_name_dic[index_code] = target_df.loc[code]['indx_sname']
                            product_name_dic[index_code] = {
                                target_df.loc[code]['fund_code']: target_df.loc[code]['fund_name']}
                            continue

                index_name_dic[index_code] = temp_df.iloc[0]['indx_sname']
                for name in target_df['fund_name'].tolist():
                    if name.find('分级') != -1 and name.find('A') == -1 and name.find('B') == -1:
                        product_code = target_df['fund_code'].tolist()[target_df['fund_name'].tolist().index(name)]
                        product_name_dic[index_code] = {product_code: name}
                        # break
                    elif name.find('联接C') != -1 or name.find('联接ETFC') != -1:
                        product_code = target_df['fund_code'].tolist()[target_df['fund_name'].tolist().index(name)]
                        product_name_dic[index_code] = {product_code: name}
                    elif name.find('指数C') != -1:
                        product_code = target_df['fund_code'].tolist()[target_df['fund_name'].tolist().index(name)]
                        product_name_dic[index_code] = {product_code: name}
                    elif name.find('C') != -1:
                        product_code = target_df['fund_code'].tolist()[target_df['fund_name'].tolist().index(name)]
                        product_name_dic[index_code] = {product_code: name}
                    elif name.find('分级B') != -1:
                        product_code = target_df['fund_code'].tolist()[target_df['fund_name'].tolist().index(name)]
                        product_name_dic[index_code] = {product_code: name}
                    # elif name.find('中证细分医药交易A')!=-1:
                    #     product_code = target_df['fund_code'].tolist()[target_df['fund_name'].tolist().index(name)]
                    #     product_name_dic[index_code] = {product_code: name}
                    # elif name.find('增强C')!=-1:
                    #     product_code = target_df['fund_code'].tolist()[target_df['fund_name'].tolist().index(name)]
                    #     product_name_dic[index_code] = {product_code: name}
                    elif name.find('金瑞') != -1:
                        product_code = target_df['fund_code'].tolist()[target_df['fund_name'].tolist().index(name)]
                        product_name_dic[index_code] = {product_code: name}
                    elif name.find('100A'):
                        product_code = target_df['fund_code'].tolist()[target_df['fund_name'].tolist().index(name)]
                        product_name_dic[index_code] = {product_code: name}
        return index_name_dic, product_name_dic

    def get_fund_index(self, fund_type='ETF', style_flag='行业'):
        if len(style_flag) > 2:
            style_flag = tuple(['行业', '主题'])
        else:
            style_flag = "('%s')" % style_flag

        if fund_type == 'ETF':
            sqlstr = '''SELECT t1.fund_code,t1.record_time, t1.fund_name,t1.establish_date,t1.indx_sname,t2.class_classify,t2.index_code,t2.index_c_fullname
             FROM zzindex_product_info t1,zzindex_info t2 WHERE t1.product_type="ETF" and t1.indx_sname=t2.indx_sname 
             and t2.class_classify in %s''' % str(style_flag)
        else:
            sqlstr = '''SELECT t1.fund_code, t1.record_time,t1.product_type,t1.fund_name,t1.establish_date,t1.indx_sname,t2.index_c_fullname,
            t2.class_classify,t2.index_code FROM zzindex_product_info t1,zzindex_info t2 WHERE t1.product_type!="ETF" 
            and t1.indx_sname=t2.indx_sname and t2.class_classify in %s''' % str(style_flag)

        df_init = pd.read_sql(sqlstr, self.engine)
        df_list = []
        for fund_code, temp_Df in df_init.groupby(by='fund_code'):
            if temp_Df.shape[0] == 1:
                df_list.append(temp_Df)
            else:
                df_list.append(temp_Df[temp_Df['record_time'] == temp_Df['record_time'].max()])

        df = pd.concat(df_list, axis=0, sort=True, )
        df['fund_code'] = self.code_last_add(fund_type=fund_type, df=df, label='fund_code')
        df = self.remove_index_same_name(df)
        df = self.remove_deadline_product(df)
        df['index_code'] = self.code_last_add(fund_type='index', df=df, label='index_code')
        index_name_dic, product_name_dic = self.get_index_product_dic(df, fund_type=fund_type)
        return index_name_dic, product_name_dic


if __name__ == '__main__':
    IndustryRecyleDemo = IndustryRecyle()
    IndustryRecyleDemo.get_fund_index(fund_type='ETF')
