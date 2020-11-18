# -- coding: utf-8 --


'''
获取指数与产品相关的接口数据
'''

import pandas as pd
from GetAndSaveWindData.MysqlCon import MysqlCon


class GetIndexAndProduct:
    def __init__(self):
        MysqlConDemo = MysqlCon()
        self.engine = MysqlConDemo.getMysqlCon('engine')

    def get_bench_product(self, bench_code='000905.SH',product_type='ETF',remove_finish=False):
        '''
        根据指数代码，查找跟踪的产品
        :param bench_code:
        :return:
        '''
        mysql_code = bench_code[:6]
        sql_str = "SELECT t1.fund_code,t1.fund_type,t1.product_type,t1.fund_name,t1.establish_date,t1.indx_sname," \
                  "t2.class_classify,t2.index_code,t1.asset_value FROM zzindex_product_info t1, zzindex_info t2" \
                  " WHERE t1.indx_sname=t2.indx_sname and t2.index_code='%s'"%mysql_code
        df = pd.read_sql(sql=sql_str,con=self.engine).set_index('fund_code')
        if product_type=='ETF':
            result_df = df[df['product_type']=='ETF']
        elif product_type=='OTC':
            result_df = df[df['product_type']!='ETF']
        elif product_type=='联接基金':
            result_df = df[df['product_type'] == '联接基金']

        if remove_finish:
            remove_df = pd.read_excel("清算基金.xlsx")
            remove_df['myql_product_code']=[code[:6] for code in remove_df['证券代码'].tolist()]
            target_code_list = [fund_code for fund_code in result_df.index.tolist() if fund_code not in remove_df['myql_product_code'].tolist()]
            result_df = result_df.loc[target_code_list]
        return result_df

    def get_fund_index_info(self,fund_code=[]):
        sql_str = ''' SELECT t1.fund_code,t1.fund_type,t1.product_type,t1.fund_name,t1.establish_date,t2.is_custom,t1.indx_sname,t2.class_classify,t2.index_c_fullname,t2.index_code,t1.asset_value 
 FROM zzindex_product_info t1, zzindex_info t2 WHERE t1.indx_sname=t2.indx_sname 
 and t2.class_classify in ('规模','行业','风格','主题','策略','其他') and t1.fund_code in %s'''%str(tuple(fund_code))
        df = pd.read_sql(sql=sql_str, con=self.engine).set_index('fund_code')
        return df

    def get_index_code_info(self,index_code=[]):
        sql_str = '''select indx_sname,index_code,class_classify from zzindex_info where index_code in %s;'''%str(tuple(index_code))
        df = pd.read_sql(sql=sql_str, con=self.engine).set_index('index_code')
        return df



if __name__ == '__main__':
    GetIndexAndProductDemo = GetIndexAndProduct()
    GetIndexAndProductDemo.get_bench_product(product_type='联接基金',remove_finish=True)
