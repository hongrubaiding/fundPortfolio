# -- coding: utf-8 --

'''
    统计本地数据库中，同花顺的主题类基金数量
'''

import pandas as pd
from datetime import datetime
import mylog as mylog
from GetAndSaveWindData.MysqlCon import MysqlCon
import numpy as np

class THSTopicSta:
    def __init__(self):
        self.logger = mylog.set_log()
        mysql_con_demo = MysqlCon()
        self.engine = mysql_con_demo.getMysqlCon(flag='engine')

    def get_index_info(self,index_fund_df):
        self.logger.info("从具体主题来看，指数基金涉及到的主题共%s个"%len(index_fund_df['topic_name'].unique()))
        dic_topic={}
        topic_fund_se = pd.Series(name='基金数量')
        for topic,temp_df in index_fund_df.groupby('topic_name'):
            dic_topic[topic]=temp_df
            topic_fund_se[topic]=temp_df.shape[0]
        topic_fund_se.sort_values(inplace=True,ascending=False)

        num_str = ''
        for num in range(5):
            num_str=num_str+'%s(%s只)，'%(topic_fund_se.index.tolist()[num],topic_fund_se.iloc[num])
        self.logger.info("主题涵盖基金数量排名靠前的有"+num_str)

        dic_company = {}
        company_fund_se = pd.Series(name='基金数量')
        for fund_company, temp_df in index_fund_df.groupby('fund_company'):
            dic_company[fund_company] = temp_df
            company_fund_se[fund_company] = temp_df.shape[0]
        company_fund_se.sort_values(inplace=True, ascending=False)
        self.logger.info("从管理人角度来看，所有主题类指数基金隶属于%s家管理人;"%len(index_fund_df['fund_company'].unique()))

        num_company_str = ''
        for num in range(5):
            num_company_str = num_company_str + '%s(%s只)，' % (company_fund_se.index.tolist()[num], company_fund_se.iloc[num])
        self.logger.info("管理主题类指数基金数量排名靠前的管理人有" + num_company_str)
        self.logger.info("其中浙商资管发布的主题类指数基金共%s只"%company_fund_se['浙商证券资管'])
        self.logger.info("所属主题为%s"%str(tuple(dic_company['浙商证券资管']['topic_name'].tolist())))

    def get_main(self):
        sql_str="select * from ths_topic_fund"
        total_df = pd.read_sql(sql=sql_str,con=self.engine)
        self.logger.info("按照同花顺主题类基金划分，全部主题类基金%s只;"%total_df.shape[0])

        index_fund_df = total_df[total_df['is_index_fund']=='是']
        self.logger.info("其中指数基金%s只，非指数基金%s只;"%(index_fund_df.shape[0],total_df.shape[0]-index_fund_df.shape[0]))
        index_graded_fund_df = index_fund_df[index_fund_df['is_graded_fund']=='是']

        not_graded_fund = index_fund_df[(index_fund_df['is_graded_fund']=='否')]
        etf_fund = index_fund_df[(index_fund_df['is_graded_fund']=='否')&(index_fund_df['etf_pub_date'])]
        otc_fund_num = not_graded_fund.shape[0]-etf_fund.shape[0]
        self.logger.info("主题指数基金中，分级基金%s只,场内基金(ETF、LOF)%s只,场外%s只；"%(index_graded_fund_df.shape[0],etf_fund.shape[0],otc_fund_num))

        self.get_index_info(index_fund_df)
        self.logger.info("涵盖主题数%s个;"%len(total_df['topic_name'].unique()))


if __name__=='__main__':
    THSTopicStaDemo = THSTopicSta()
    THSTopicStaDemo.get_main()