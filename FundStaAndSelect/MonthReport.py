# -- coding: utf-8 --


'''

'''

import pandas as pd
from datetime import datetime
import mylog as mylog
import numpy as np
from GetAndSaveWindData.GetIndexAndProduct import GetIndexAndProduct
from GetAndSaveWindData.MysqlCon import MysqlCon

class MonthReport:
    def __init__(self):
        self.start_date = '2020-07-01'
        self.end_date = '2020-07-31'
        self.file_path = r"D:\\工作文件\\指数基金月报\\培训PPT\\0821\\"
        MysqlConDemo = MysqlCon()
        self.engine = MysqlConDemo.getMysqlCon('engine')
        self.name_dic={'fund_code':'基金代码','fund_type':'基金类型','product_type':'产品类型','fund_name':'基金名称',
                       'establish_date':'基金成立日','indx_sname':'跟踪指数','class_classify':'跟踪指数类型',
                       'index_code':'跟踪指数代码'}
        self.logger = mylog.set_log()

    def get_new_fund(self):
        sql_str = '''  SELECT t1.fund_code,t1.fund_type,t1.product_type,t1.fund_name,t1.establish_date,t2.is_custom,t1.indx_sname,t2.class_classify,
        t2.index_c_fullname,t2.index_code,t1.asset_value FROM zzindex_product_info t1, zzindex_info t2 WHERE t1.indx_sname=t2.indx_sname and
         t2.class_classify in ('规模','行业','风格','主题','策略','其他') ;'''
        df = pd.read_sql(sql=sql_str,con=self.engine)

        new_df = df[(df['establish_date']>=self.start_date)&(df['establish_date']<=self.end_date)]
        new_df = new_df[list(self.name_dic.keys())]
        new_df.rename(columns=self.name_dic,inplace=True)
        new_df.sort_values('基金成立日',ascending=False).to_excel(self.file_path+'新成立基金概况.xlsx')

        df.rename(columns=self.name_dic, inplace=True)
        remove_df = pd.read_excel(self.file_path + '清算基金.xlsx')
        remove_code_list = [code.split('.')[0] for code in remove_df['证券代码'].tolist()]
        total_code = [code for code in df['基金代码'].tolist() if code not in remove_code_list]
        self.logger.info('所有指数基金%s' % len(total_code))

        df.set_index('基金代码', inplace=True)
        df = df.loc[total_code]
        improve_num = 0
        for fund_name in df['基金名称'].tolist():
            if fund_name.find('增强') != -1:
                improve_num += 1
        self.logger.info('指数增强型基金%s' % improve_num)

        for index_style,temp_df in df.groupby('跟踪指数类型'):
            temp_df.sort_values('asset_value',ascending=False).to_excel(self.file_path+index_style+'型基金.xlsx')
            self.logger.info('%s型，共%s'%(index_style,temp_df.shape[0]))


    def get_detail_fund(self):
        sql_str='select fund_code,fund_name from zzindex_product_info;'
        df = pd.read_sql(sql=sql_str, con=self.engine)
        remove_df = pd.read_excel(self.file_path+'清算基金.xlsx')
        remove_code_list = [code.split('.')[0] for code in remove_df['证券代码'].tolist()]
        total_code = [code for code in df['fund_code'].tolist() if code not in remove_code_list]
        self.logger.info('所有指数基金%s'%len(total_code))

        df.set_index('fund_code',inplace=True)
        improve_num = 0
        for fund_name in df.loc[total_code]['fund_name'].tolist():
            if fund_name.find('增强')!=-1:
                improve_num+=1
        self.logger.info('指数增强型基金%s' % improve_num)




if __name__=='__main__':
    MonthReportDemo = MonthReport()
    MonthReportDemo.get_new_fund()
    MonthReportDemo.get_detail_fund()