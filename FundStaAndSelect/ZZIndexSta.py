# -- coding: utf-8 --

'''
    统计本地数据库中，各类基金（行业、主题、规模、风格、策略）当前月的概况
'''

import pandas as pd
from datetime import datetime
import mylog as mylog
from GetAndSaveWindData.MysqlCon import MysqlCon
import numpy as np
from WindPy import w


class ZZIndexSta:
    def __init__(self):
        self.logger = mylog.set_log()
        mysql_con_demo = MysqlCon()
        self.engine = mysql_con_demo.getMysqlCon(flag='engine')
        w.start()

    def get_style_fund_info(self,df):
        file_path = r"D:\\工作文件\\"
        wind_df = pd.read_excel(file_path + "指数基金11月.xlsx")
        wind_improve_df = pd.read_excel(file_path+'增强指数基金11月.xlsx')
        wind_code_list = [code.split('.')[0] for code in wind_df['证券代码'].tolist()]
        wind_improve_code = [code.split('.')[0] for code in wind_improve_df['证券代码'].tolist()]
        dic_class_classify={}
        zz_lack_code=[]
        dic_result_classify = {}
        for code in wind_code_list:
            if code in df.index.tolist():
                if code not in wind_improve_code:
                    if code!='162714':
                        class_classify = df.loc[code]['class_classify']
                    else:
                        class_classify='规模'

                    dic_class_classify[class_classify] = dic_class_classify.get(class_classify, 0) + 1
                    dic_result_classify[class_classify] = dic_result_classify.get(class_classify, [])
                    dic_result_classify[class_classify].append(code)
            else:
                zz_lack_code.append(code)

        name_dic = {"fund_setupdate":"基金成立日","netasset_total":"基金规模(亿元)","fund_trackerror_threshold":"年化跟踪误差(%)",
                    "fund_corp_fundmanagementcompany":"基金管理人","fund_trackindexcode":"跟踪指数代码",
                    "nav":"单位净值","return_1m":"近1月(%)","return_3m":"近3月(%)","return_ytd":"今年以来(%)",
                   "return_1y":"近1年(%)","risk_returnyearly":"年化收益","risk_stdevyearly":"年化波动",
                "sec_name":"基金简称","return_6m":"近6月(%)","return_3y":"近3年(%)","risk_sharpe":"夏普比率","risk_maxdownside":"近一年最大回撤"}
        name_dic_reuslt = {key.upper():values for key,values in name_dic.items()}
        for class_classify,code_list in dic_result_classify.items():
            code_target = [code+'.OF' for code in code_list]
            fields = "sec_name,fund_setupdate,netasset_total,fund_corp_fundmanagementcompany,fund_trackindexcode," \
                     "return_1m,return_3m,return_6m,return_1y,return_3y,return_ytd,risk_sharpe,risk_maxdownside,risk_returnyearly,risk_stdevyearly"
            options_str = "unit=1;tradeDate=20201101;annualized=0;startDate=20191031;endDate=20201031;period=2;returnType=1;yield=1;riskFreeRate=1"
            wssdata = w.wss(codes=code_target,fields=fields,options=options_str)
            if wssdata.ErrorCode!=0:
                self.logger.info("获取wind数据错误%s"%wssdata.ErrorCode)
                return
            resultDf = pd.DataFrame(wssdata.Data, index=wssdata.Fields, columns=wssdata.Codes).T
            resultDf.index.name='基金代码'
            resultDf.rename(columns=name_dic_reuslt,inplace=True)
            resultDf['基金规模(亿元)'] = resultDf['基金规模(亿元)']/100000000
            resultDf.sort_values(by='基金规模(亿元)',ascending=False,inplace=True)
            resultDf.to_excel(file_path+'11月%s型指数基金.xlsx'%class_classify)

    def get_total_index_fund(self):
        sql_str = ''' SELECT t1.fund_code,t1.fund_type,t1.record_time,t1.product_type,t1.fund_name,t1.establish_date,t1.fund_company,
        t1.indx_sname,t2.class_classify,t2.index_code,t2.index_c_fullname,t1.asset_value FROM zzindex_product_info t1, zzindex_info t2 WHERE t1.indx_sname=t2.indx_sname 
        and t2.class_classify in ('规模','行业','风格','主题','策略','其他');
        '''
        df = pd.read_sql(sql=sql_str,con=self.engine).set_index('fund_code')
        df.drop_duplicates(keep='first', inplace=True)

        df_list = []
        for fund_code, temp_Df in df.groupby(by='fund_code'):
            if temp_Df.shape[0] == 1:
                df_list.append(temp_Df)
            else:
                df_list.append(temp_Df[temp_Df['record_time'] == temp_Df['record_time'].max()])
        df = pd.concat(df_list, axis=0, sort=True, )

        dead_fund_path = "D:\\工作文件\\"
        dead_fund_df = pd.read_excel(dead_fund_path+'清算基金.xlsx')
        dead_fund_code = [code.split('.')[0] for code in dead_fund_df['证券代码'].tolist()]
        total_code = list(set([code for code in df.index.tolist() if code not in dead_fund_code]))
        not_dead_df = df.loc[total_code]
        update_df_list = []
        for fund_name,temp_df in not_dead_df.groupby('fund_name'):
            if temp_df.shape[0]>1:
                inter_word = 0
                target_row = 0
                for row_num in range(len(temp_df)):
                    index_c_fullname = temp_df.iloc[row_num]['index_c_fullname']
                    temp_inter = len(set(index_c_fullname).intersection(set(fund_name)))
                    if temp_inter>inter_word:
                        inter_word=temp_inter
                        target_row=row_num
                temp_se=temp_df.iloc[target_row]
                temp_df = pd.DataFrame(temp_se,columns=[temp_df.index.tolist()[0]]).T


            update_df_list.append(temp_df)
        update_df = pd.concat(update_df_list,axis=0,sort=True)
        return update_df

    def get_main(self):
        df = self.get_total_index_fund()
        self.get_style_fund_info(df)


if __name__ == '__main__':
    ZZIndexStaDemo = ZZIndexSta()
    ZZIndexStaDemo.get_main()
