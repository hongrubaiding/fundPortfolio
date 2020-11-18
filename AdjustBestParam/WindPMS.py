# -- coding: utf-8 --


'''
windPMs模块标准化录入
'''

import pandas as pd
import numpy as np
import os
from datetime import datetime

class WindPMS:
    def __init__(self):
        pass

    def get_df(self):
        df = pd.read_excel("产品组合24仓位表.xlsx",index_col=0)
        self.calc_main(total_pos_df=df)


    def calc_main(self,total_pos_df,portfolio_num=''):
        sec_list = total_pos_df.columns.tolist()
        df_list = []
        for date_str in total_pos_df.index.tolist():
            if date_str>='2015-08-01':
                temp_df = pd.DataFrame()
                temp_df['证券代码'] = sec_list
                temp_df['持仓权重'] = total_pos_df.loc[date_str].tolist()
                # temp_df['调整日期'] = date_str
                temp_df['调整日期'] = datetime.strptime(date_str,"%Y-%m-%d")
                temp_df['证券类型'] = "基金"
                df_list.append(temp_df)
        total_format_df = pd.concat(df_list,axis=0,sort=True)
        total_format_df= total_format_df[['证券代码','持仓权重','调整日期','证券类型']]
        total_format_df.to_excel("%swindPMS格式数据.xlsx"%portfolio_num,index=False)

if __name__=="__main__":
    WindPMSDemo = WindPMS()
    # WindPMSDemo.calc_main()
    WindPMSDemo.get_df()