import folium
import streamlit as st
from streamlit_folium import st_folium
import os
import time
import requests
import numpy as np
import re
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import struct
import socket
import random

def read_files_split(df):
    # 重命名列名
    id_sent_list = []
    id_sent_dic = {
        '17': 1, '33': 2, '49': 3, '65': 4, '81': 5, '97': 6, '113': 7, '129': 8, '145': 9, '161': 10,
        '18': 11, '34': 12, '50': 13, '66': 14, '82': 15, '98': 16, '114': 17, '130': 18, '146': 19, '162': 20,
        '19': 21, '35': 22, '51': 23, '67': 24, '83': 25, '99': 26, '115': 27, '131': 28, '147': 29, '163': 30,
        '20': 31, '36': 32, '52': 33, '68': 34, '84': 35, '100': 36, '116': 37, '132': 38, '148': 39, '164': 40,
        '21': 41, '37': 42, '53': 43, '69': 44, '85': 45, '101': 46, '117': 47, '133': 48, '149': 49, '165': 50,
        '15': 55,
    }

    #  df = df[df.loc[:, 1].isin(list(map(int, list(n_e_dic.keys()))))]
    mask = df.loc[:, 1].isin(list(map(int, list(id_sent_dic.keys()))))
    # 获取不符合条件的行索引
    indexes_to_drop = df[~mask].index
    # 删除不符合条件的行
    df.drop(indexes_to_drop, inplace=True)
    df.reset_index(drop=True, inplace=True)
    # df.drop(['index'], axis=1)

    # 将列数据按冒号分割成三列
    df[['T', 'E', 'N']] = df[13].str.split(':', expand=True)
    # 将第二列和第三列的数据除以100，并转换为浮点数
    df[['E', 'N']] = df[['E', 'N']].astype(float) / 100

    for tme in range(len(df[0])):
        # 获取今天日期
        today = datetime.datetime.utcnow().date()
        # 构造今天早上8点的UTC时间
        target_time = datetime.datetime.combine(today, datetime.datetime.min.time()) + datetime.timedelta(hours=8)
        # 将target_time与05357.000相加
        result_time = target_time + datetime.timedelta(seconds=float(df['T'][tme]))
        # 将结果转换为UTC时间格式
        result_time_utc = result_time.strftime('%Y-%m-%d %H:%M:%S')
        # 使用.loc进行赋值操作
        df.loc[tme, 'T'] = result_time_utc
        id_sent_list.append(id_sent_dic[str(df[1][tme])])

    df['Id'] = id_sent_list

    df.columns = ['Frame', 'Id_Real', 'X_Mag', 'Y_Mag', 'Z_Mag', 'X_Gyro', 'Y_Gyro', 'Z_Gyro', 'X_Accel', 'Y_Accel',
                  'Z_Accel',
                  'Audio', 'Audio_VAD', 'Location', 'T', 'E', 'N', 'Id']
    # 删除Location列
    df['Audio'] = df['Audio'].apply(lambda x: x / 100)
    # df['N'] = df['N'].apply(lambda x: float(x) / 100)
    # df['E'] = df['E'].apply(lambda x: float(x) / 100)
    df1 = df.drop(['Location'], axis=1)
    return df1


def process_udp_to_df(data):
    k = 0
    final_var_list = []
    while True:
        if data[0 + k * 60:k * 60 + 1] == b'':
            # obj.close()
            break
        if data[0 + k * 60:k * 60 + 1] == b'\xbb' and data[k * 60 + 1:k * 60 + 2] == b'\xbb':
            if data[2 + k * 60:k * 60 + 3] == b'\x3c':
                data_id = ord(data[k * 60 + 3:k * 60 + 4])  # int(data[k * 60 + 3:k * 60 + 4], 16)              # 修改代码
                data_sensor = data[k * 60 + 4:k * 60 + 26]  # fp.read(22)
                count = len(data_sensor) / 2
                var = struct.unpack('h' * int(count), data_sensor)
                print(k, data_id, var)
                data_sensor_next = data[k * 60 + 26:k * 60 + 58]  # fp.read(32)
                # var0 = "T:"
                var1 = data_sensor_next.decode('utf-8')     # 修改
                var_list = list(var)
                var_list.insert(0, data_id)     # 修改
                var_list.insert(0, k)       # 修改
                var_list.append(var1)    # 修改
                # print(var_list)
                final_var_list.append(var_list)     # 修改
            elif data[2 + k * 60:k * 60 + 3] == b'\xaa' or data[2 + k * 60:k * 60 + 3] == b'\xAA':
                if data[3 + k * 60:k * 60 + 4] == b'\x01':
                    var_list = [k, 15, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    final_var_list.append(var_list)
                elif data[3 + k * 60:k * 60 + 4] == b'\x02':
                    var_list = [k, 15, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    final_var_list.append(var_list)
                elif data[3 + k * 60:k * 60 + 4] == b'\x03':
                    var_list = [k, 15, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    final_var_list.append(var_list)
                elif data[3 + k * 60:k * 60 + 4] == b'\x04':
                    var_list = [k, 15, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    final_var_list.append(var_list)
        k += 1
    final_var_df = pd.DataFrame(final_var_list)
    print("已生成txt数据文件！")
    return final_var_df

# 定义一个自定义排序函数，按照文件名中的数字序号排序
def sort_by_number(filename):
    return int(re.findall(r'\d+', filename)[0])


def mean_percentile(percent, df, column_name):
    # percentile = 0.8
    q1, q2 = np.percentile(df[column_name], [100 * (0.5 - percent / 2), 100 * (0.5 + percent / 2)])
    mean80 = df[(df[column_name] >= q1) & (df[column_name] <= q2)][column_name].mean()
    return mean80


def read_files_split1(df):
    # 将经纬度和时间分割成三个变量
    df['T'] = df[11].str.split('T:', expand=True)[1].str.split('N:', expand=True)[0]
    df['N'] = df[11].str.split('T:', expand=True)[1].str.split('N:', expand=True)[1].str.split('E:', expand=True)[0]
    df['E'] = df[11].str.split('T:', expand=True)[1].str.split('N:', expand=True)[1].str.split('E:', expand=True)[1]
    # 重命名列名
    df.columns = ['Frame', 'X_Accel', 'Y_Accel', 'Z_Accel', 'X_Gyro', 'Y_Gyro', 'Z_Gyro', 'X_Mag', 'Y_Mag', 'Z_Mag',
                  'Audio', 'Location', 'T', 'N', 'E']
    # 删除Location列
    df['Audio'] = df['Audio'].apply(lambda x: x / 100)
    df['N'] = df['N'].apply(lambda x: float(x) / 100)
    df['E'] = df['E'].apply(lambda x: float(x) / 100)
    df1 = df.drop('Location', axis=1)
    return df1

def progress_bar(progress_text, duration, column):
    # st.spinner(text=progress_text)
    my_bar = column.progress(0)
    for percent_complete in range(1, 101):
        time.sleep(duration / 100)
        my_bar.progress(percent_complete / 100)
        # column.success('完成！')

def app1():
    st.sidebar.success("已选择：🌍  主监测页面")

    # 本地IP地址和端口号
    LOCAL_IP = ""
    # LOCAL_PORT = 0  # 选择一个空闲端口，系统会自动分配

    # 服务器IP地址和端口号
    UDP_IP = "10.10.21.96"  # 51.51.51.50
    UDP_PORT = 1438

    # 指令数据
    command_real_time = bytearray([0x55, 0xAA, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xAA, 0x55])
    command_history = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xAA, 0x55])
    sj_mode_control = bytearray([0x55, 0xAA, 0x10, 0x02, 0x01, 0x01, 0x00])
    zz_mode_control = bytearray([0x55, 0xAA, 0x20, 0x02, 0x02, 0x02, 0x00])

    st.markdown(
        f'''
            <style>
                .reportview-container .sidebar-content {{
                    padding-top: {0}rem;
                }}
                .appview-container .main .block-container {{
                    {f'max-width: 100%;'}
                    padding-top: {0}rem;
                    padding-right: {1}rem;
                    padding-left: {1}rem;
                    padding-bottom: {0}rem;
                    overflow: auto;
                }}
            </style>
            ''',
        unsafe_allow_html=True,
    )

    st.subheader("  ")

    colmns0 = st.columns(3, gap="medium")

    # st.container()
    # page_button = st.sidebar.selectbox('请选择', ['选项1', '选项2', '选项3'])
    # if page_button:
    #     option = st.sidebar.selectbox('请选择', ['选项1', '选项2', '选项3'])
    #     st.write('你选择了：', option)

    with colmns0[1]:
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold">传感器目标识别服务</p></nobr>', unsafe_allow_html=True)
    # with colmns0[0]:
    #     timestr = (datetime.datetime.now()+datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    #     st.metric(label='时间', value=timestr, label_visibility='collapsed') # visible hidden collapsed

    # 添加地图信息
    locations = [[39.91667, 116.41667 ],[31.231706, 121.472644], [30.58435, 114.29857],
                 [28.19409, 112.982279], [30.659462, 104.065735], [23.16667, 113.23333]]
    customers = ['北京', '上海', '武汉', '长沙', '成都', '广州']

    colmns = st.columns([2,5,2], gap="small")
    with colmns[1]:
        m = folium.Map(location=[34.90960, 145.39722], # 145.39722
                       tiles=None,
                       zoom_start=3.2,
                       control=False,
                       control_scale=True)

        folium.TileLayer(tiles='http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
                         attr="&copy; <a href=http://ditu.amap.com/>高德地图</a>",
                         min_zoom=0,
                         max_zoom=19,
                         control=True,
                         show=True,
                         overlay=False,
                         name='baseLayer',
                         opacity=1.0
                         ).add_to(m)


        # add marker and link tooltip
        for c_idx in np.arange(0,len(customers)):
            #print(locations[c_idx])
            marker = folium.Marker(
                locations[c_idx],
                # popup = customers[c_idx], # app_links[c_idx]
                tooltip = customers[c_idx],
                icon=folium.Icon(icon="cloud"),
                # icon = folium.features.CustomIcon("https://i.gifer.com/9C4G.gif", icon_size=(14, 14))
            )
            marker.add_to(m)
        st_data = st_folium(m, width=1500, height=350)



    visitor_clicked = colmns[0].button(label="🚀 刷新页面", help="刷新", key=None,
                                on_click=None, args=None, kwargs=None)
    # 按钮字体
    st.markdown("""<style>p, ol, ul, dl
    {
    margin: 0px 0px 1rem;
    padding: 0px;
    font-size: 1.0rem;
    font-weight: 1000;
    }
    </style>""", unsafe_allow_html=True)

    col1, col2, col3 = colmns[0].columns(3, gap="small")

    button2 = col2.button(' 获取实时数据 ')
    button3 = col2.button(' 获取历史数据 ')
    button4 = col2.button(' 开始识别 ')

    if not button4 and not button3:
        if button2:
            st.session_state.parameters = {}
            print('执行Button2')

            # 创建UDP套接字
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((LOCAL_IP, UDP_PORT))
            # obj_txt = open("./sensors_data.txt", 'w')

            sock.setblocking(False)
            # 设置接收超时时间为 1 秒
            sock.settimeout(1)

            # 发送获取实时数据指令
            sock.sendto(command_real_time, (UDP_IP, UDP_PORT))
            # sock.sendto(command_real_time, (UDP_IP, UDP_PORT))
            start_time2 = time.time()
            received_data = b''
            # received_data = b'\xbb\xbb<\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00j7\x00\x00\x00\xc1\xcd\xbb\xbb<A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00=R\xbb\xbb<Q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x96\xa8\xbb\xbb<a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00h\xe7\xbb\xbb<q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc3\x1d\xbb\xbb<\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6-\xbb\xbb<\x91\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00m\xd7\xbb\xbb<\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00?\x82\xbb\xbb<!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc1\xcd\xbb\xbb<1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00j7\xbb\xbb<A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00=R\xbb\xbb<Q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x96\xa8\xbb\xbb<a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00h\xe7\xbb\xbb<q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc3\x1d\xbb\xbb<\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6-\xbb\xbb<\x91\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00m\xd7\xbb\xbb<\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00?\x82\xbb\xbb<!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc1\xcd\xbb\xbb<1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00j7\xbb\xbb<A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00=R\xbb\xbb<Q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x96\xa8\xbb\xbb<a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00h\xe7\xbb\xbb<q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc3\x1d\xbb\xbb<\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6-\xbb\xbb<\x91\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00m\xd7\xbb\xbb<\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00?\x82\xbb\xbb<!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc1\xcd\xbb\xbb<1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00j7\xbb\xbb<A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00=R\xbb\xbb<Q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x96\xa8\xbb\xbb<a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00h\xe7\xbb\xbb<q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc3\x1d\xbb\xbb<\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6-\xbb\xbb<\x91\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00m\xd7\xbb\xbb<\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00?\x82\xbb\xbb<!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc1\xcd\xbb\xbb<1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00j7\xbb\xbb<A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00=R\xbb\xbb<Q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x96\xa8\xbb\xbb<a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00h\xe7\xbb\xbb<q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc3\x1d\x00\x00h\xe7\xbb\xbb<\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6-\xbb\xbb<\x91\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00m\xd7\xbb\xbb<\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00?\x82\xbb\xbb<!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc1\xcd\xbb\xbb<1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00j7\xbb\xbb<A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00=R\xbb\xbb<Q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x96\xa8\xbb\xbb<a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00h\xe7\xbb\xbb<q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc3\x1d\xbb\xbb<\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6-\xbb\xbb<\x91\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00m\xd7\x00\x00\xc6-\xbb\xbb<\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00?\x82\xbb\xbb<!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc1\xcd\xbb\xbb<1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00j7\xbb\xbb<A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00=R\xbb\xbb<Q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x96\xa8\xbb\xbb<a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00h\xe7\xbb\xbb<q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc3\x1d\xbb\xbb<\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6-\xbb\xbb<\x91\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00m\xd7\x00\x00\xc6-\xbb\xbb<\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00?\x82\xbb\xbb<!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc1\xcd\xbb\xbb<1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00j7\xbb\xbb<A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00=R\xbb\xbb<Q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x96\xa8\xbb\xbb<a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00h\xe7\xbb\xbb<q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc3\x1d\xbb\xbb<\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6-\xbb\xbb<\x91\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6-\xbb\xbb<\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00?\x82\xbb\xbb<!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc1\xcd\xbb\xbb<1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00j7\xbb\xbb<A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00=R\xbb\xbb<Q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x96\xa8\xbb\xbb<a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00h\xe7\xbb\xbb<q\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc3\x1d\xbb\xbb<\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6-'
            # received_data = b"\xbb\xbb<!\xc9\xec\xc9\xf5\x9b\x04\xf9\xff\xfd\xff\x05\x00k\xfb\xbe\xfeb\xc1\xc8\x16\x07\x00::NGGA,073451.000,,,,,0,00,25.5,L\x17\xbb\xbb<\x11\xd9\xf71\xf6u\x03\xb4\xfe\xef\x03\xa0\x00\x08\xe2\x991\xba\xed\x89 P\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc4_\xbb\xbb<!\xe1\xec\xc1\xf5\x9d\x04\xf8\xff\xfd\xff\x04\x00~\xfb\xc4\xfe_\xc1\xf1\x15\x07\x00::NGGA,073451.000,,,,,0,00,25.5,>\xff\xbb\xbb<\x11\x89\xf7\xf9\xf5\x7f\x03l\x00\xb0\xf3\xd7\xfb\t\xfc\xc1/\x1d\xe3\x07\x1fP\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x92\x80\xbb\xbb<!\xc9\xec\xd1\xf5\x9b\x04\xf7\xff\xfe\xff\x04\x00w\xfb\xbb\xfew\xc1'\x17\x0c\x00::NGGA,073451.000,,,,,0,00,25.5,\xf3r\xbb\xbb<\x11\xb1\xf7\t\xf6\x89\x03F\xff\xc5\x00g\x00\x8b\xefs4+\xe4v\x1a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x15\xbe\xbb\xbb<!\xd1\xec\xf1\xf5\x99\x04\xf8\xff\xfb\xff\x05\x00\x9c\xfb\xc5\xfe^\xc1\x89\x16\x07\x00::NGGA,073451.000,,,,,0,00,25.5,z\x8b\xbb\xbb<\x11\xd9\xf5\x19\xfb\x07\x04\xfd\xe5\x0f\xfa\xba\xf8o\xc6a\xf7\xa0\xef\xb6 \n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0cx\xbb\xbb<\x11i\xf6y\xf5c\x03\xcf\xfc\xd5\t\xa5\xf9F\xe5\xe1\xf9r?\x19\x18\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xcen"
            st.markdown("""<style> div.stButton > button:first-child {
            background-color: white;
            color: black;
            height:3em;
            width:8em;
            border-radius:10px 10px 10px 10px;
            border: 3px solid #008CBA;
            }
            </style>""", unsafe_allow_html=True)
            st.markdown("""<style>
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(5) > div > div.css-c6gdys.edb2rvg0 > div > p {
            font-size: 4px;
            }
            </style>""", unsafe_allow_html=True)
            st.markdown("""<style>
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(4) > div > div.css-c6gdys.edb2rvg0 > div > p {
            font-size: 4px;
            }
            </style>""", unsafe_allow_html=True)
            st.markdown("""<style>
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(6) > div > div > div > div > div > div > p {
            font-size: 4px;
            }
            </style>""", unsafe_allow_html=True)
            cyc_num = 1
            progress_container = col2.empty()
            while True:
                print(f'第{cyc_num}次执行Button1第二层循环')
                cyc_num += 1
                # print(cyc_num)
                elapsed_time = time.time() - start_time2
                # print(elapsed_time)
                if elapsed_time >= 20:
                    print("已完成20秒数据接收，退出循环")
                    break
                else:
                    # 第一个进度条
                    progress_text = "获取实时数据命令已发送至空基通信平台，等待实时数据传输..."
                    my_bar = progress_container.progress(0, text=progress_text)
                    my_bar.progress(elapsed_time / 25, text=progress_text)

                    try:
                        data, addr = sock.recvfrom(30000)
                        if len(data) == 8 and data[0] == 0xAA and data[1] == 0x55 and data[4] == 0x01 and \
                                data[5] == 0x01:
                            # 重新发送指令
                            print("服务器无数据")
                        else:
                            received_data += data

                            # print(data_udp)
                        if len(received_data) != 0:
                            print(received_data)
                        # break  # 接收到数据后跳出循环
                    except socket.timeout:
                        # 处理未接收到数据的情况
                        print("未接收到数据，重新发送...")
                        sock.sendto(command_real_time, (UDP_IP, UDP_PORT))
                        continue  # 继续下一次循环
                    except BlockingIOError:
                        # 处理非阻塞模式下未接收到数据的情况
                        print("未接收到数据，退出循环...")
                        break  # 打破当前循环
                    except OSError as e:
                        if e.errno == 10048:
                            # 处理端口已被占用的情况
                            sock.close()
                            print("端口已被占用，退出循环...")
                            break  # 打破当前循环

            print('处理数据')
            read_file_df = process_udp_to_df(received_data)

            # 关闭套接字
            sock.close()
            print('关闭套接字')
            if len(read_file_df) > 0:
                # 读取文件，解析数据
                # read_file_df = pd.read_csv('./sensors_data.txt', sep=',', header=None)
                final_read_file_df = read_files_split(read_file_df)

                sensor_dfs = {}

                # 获取id列中的唯一值
                unique_ids = final_read_file_df['Id'].unique()
                unique_ids = sorted(unique_ids)
                for id_value in unique_ids:
                    # 根据id值筛选数据
                    subset = final_read_file_df[final_read_file_df['Id'] == id_value]
                    subset.reset_index(drop=False, inplace=True)
                    # 将分割后的数据框存储到字典中
                    sensor_dfs[id_value] = subset

                st.session_state.parameters['final_read_file_df'] = final_read_file_df
                st.session_state.parameters['unique_ids'] = unique_ids
                st.session_state.parameters['sensor_dfs'] = sensor_dfs
                # 删除第一个元素
                progress_container.empty()
                col2.success("请点击开始识别按钮启动目标识别操作!")
                print('**** 可点击其他按钮 ****')
                time.sleep(1)

            else:
                print("未接收到传感器数据")
                final_read_file_df = pd.DataFrame(np.array([]))
                sensor_dfs = {}
                unique_ids = []

                st.session_state.parameters['final_read_file_df'] = final_read_file_df
                st.session_state.parameters['unique_ids'] = unique_ids
                st.session_state.parameters['sensor_dfs'] = sensor_dfs

                # 删除第一个元素
                progress_container.empty()
                col2.warning("⚠ 未接收到传感器数据,请重新获取!")
                print('**** 可点击其他按钮 ****')
                time.sleep(1)

            text_area_height = 450
        else:
            if hasattr(st.session_state, "parameters"):
                print('存在数据，无需初始化')
            else:
                # print('Yes')
                st.session_state.parameters = {}
                final_read_file_df = pd.DataFrame(np.array([]))
                sensor_dfs = {}
                unique_ids = []
                st.session_state.parameters['final_read_file_df'] = final_read_file_df
                st.session_state.parameters['unique_ids'] = unique_ids
                st.session_state.parameters['sensor_dfs'] = sensor_dfs
            text_area_height = 600
    elif not button4 and not button2:
        if button3:
            # # Run external Python program using subprocess
            # subprocess.run(["python", r"E:\2项目资料\工作项目\目标识别软件编程\Target recognition software\App_0_0_2\UDP_Receive.py"])
            # col2.success("开始获取实时数据")
            progress_container = col2.empty()
            # 第一个进度条
            progress_text = "获取历史数据命令已发送至空基通信平台，等待历史数据传输..."

            st.markdown("""<style> div.stButton > button:first-child {
            background-color: white;
            color: black;
            height:3em; 
            width:8em; 
            border-radius:10px 10px 10px 10px;
            border: 3px solid #008CBA;
            }
            </style>""", unsafe_allow_html=True)

            st.markdown("""<style> 
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(5) > div > div.css-c6gdys.edb2rvg0 > div > p {
            font-size: 4px;
            }
            </style>""", unsafe_allow_html=True)
            st.markdown("""<style> 
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(4) > div > div.css-c6gdys.edb2rvg0 > div > p {
            font-size: 4px;
            }
            </style>""", unsafe_allow_html=True)

            st.markdown("""<style> 
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(6) > div > div > div > div > div > div > p {
            font-size: 4px;
            }
            </style>""", unsafe_allow_html=True)

            my_bar = progress_container.progress(0, text=progress_text)
            for percent_complete in range(1, 11):
                time.sleep(1)
                my_bar.progress(percent_complete / 10, text=progress_text)
            # 删除第一个元素
            progress_container.empty()

            progress_container = col2.empty()
            # 第二个进度条
            progress_text2 = "已获取布撒式传感器历史数据，报文请参见以下数据..."
            my_bar = progress_container.progress(0, text=progress_text2)
            for percent_complete2 in range(1, 11):
                time.sleep(1)
                my_bar.progress(percent_complete2 / 10, text=progress_text2)

            # 删除第二个元素
            progress_container.empty()
            col2.success("请点击开始识别按钮启动目标识别操作!")
            text_area_height = 450
        else:
            text_area_height = 600
    else:
        text_area_height = 600

    # First Columns
    with colmns[0]:
        st.markdown("""<style>.css-16idsys p
        {
        word-break: break-word;
        margin-bottom: 10px;
        font-size: 18px;
        }
        </style>""", unsafe_allow_html=True)

        txt_name_time = []

        if hasattr(st.session_state, "parameters") and ('unique_ids' in st.session_state.parameters):
            if len(st.session_state.parameters['unique_ids']) != 0:
                for tmp_id in st.session_state.parameters['unique_ids']:
                    txt_name_time.append(
                        "●  节点2023" + str(tmp_id).zfill(3) + "于" + str(st.session_state.parameters['sensor_dfs'][tmp_id]['T'][0]) + "识别到振动信号")
                txt_name_time_df = pd.DataFrame({'txt': txt_name_time})

                # txt = st.dataframe(txt_name_time_df, height=650)
                multi_line_str = "\n".join(txt_name_time)
            else:
                multi_line_str = '无'
        else:
            multi_line_str = '无'
        txt2 = st.text_area(label="实时报文监测", value=multi_line_str, height=text_area_height)


    with colmns[2]:
        st.markdown("已部署环境传感器")
        sensors_num = len(st.session_state.parameters['unique_ids'])
        st.markdown('<p style="font-family:sans sarif; text-align: center;color:#38a800; font-size: 30px; font-weight: bold">{}</p>'.format(sensors_num), unsafe_allow_html=True)
        # st.metric(label="已部署环境传感器", value=99)
        st.markdown("###")
        st.markdown("正常工作率")
        # st.metric(label="正常工作率", value='99%')
        if sensors_num!=0:
            sensors_work_percent = "100%"
        else:
            sensors_work_percent = "0%"
        st.markdown('<p style="font-family:sans sarif; text-align: center;color:#ff4500; font-size: 30px; font-weight: bold">{}</p>'.format(sensors_work_percent), unsafe_allow_html=True)
        st.markdown("###")
        st.markdown("节点状态列表")
        # parameters = st.expander("", True)

        # 将传感器编号左填补为001，002
        files_str_nums = [str(num).zfill(3) for num in st.session_state.parameters['unique_ids']]
        # 获取传感器序列号2023001，2023002
        sensors_label = ['2023' + str(num1) for num1 in files_str_nums]
        st.session_state.parameters['sensors_label'] = sensors_label
        curr_status = []
        curr_power = []
        for labels in range(len(sensors_label)):
            curr_status.append('通信正常')
            curr_power.append('正常')
        sensors_label_df = pd.DataFrame({'节点序列号': sensors_label, '当前状态': curr_status, '电量': curr_power})

        # df1 = pd.read_csv("Node status_list-1.csv",sep=',', encoding='GBK') #, header=None
        sensors_label_df = sensors_label_df.apply(lambda x: x.astype(str))
        # 重置行索引为默认整数索引
        sensors_label_df = sensors_label_df.reset_index(drop=True)
        # 修改行索引从 1 开始
        sensors_label_df.index = range(1, len(sensors_label_df) + 1)
        # st.table(df1)
        st.dataframe(sensors_label_df, width = 400, height=610)


    col_sub_1, col_sub_2, col_sub_3 = colmns[1].columns([2.5,1,1], gap="small")

    col_sub_2.markdown("###")
    # col_sub_2.markdown("###")
    sensor_node_select = col_sub_2.selectbox('选择节点：', st.session_state.parameters['sensors_label'])
    if sensor_node_select is not None:
        sensor_node = int(sensor_node_select[-3:])
    # st.markdown(st.session_state.parameters['sensors_label'])
    # st.markdown(st.session_state.parameters['unique_ids'])
    # st.markdown(st.session_state.parameters['final_read_file_df'])
    col_sub_2.markdown("###")
    col_sub_2.markdown("###")
    col_sub_2.markdown("###")
    col_sub_2.write("识别结果")

    with col_sub_3:
        st.markdown("###")
        st.checkbox('动态时间规整', value=True)
        st.checkbox('决策树')
        st.checkbox('神经网络')
        # st.markdown("###")
        st.markdown("###")
        # st.markdown("###")
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; '
                    'font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; '
                    'font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        # st.markdown("###")
        st.write("广播警告")

        # st.markdown("###")
        st.markdown("###")
    warning_container = col_sub_3.container()
    # warning_container.image("pic2-2.png", width=150)
    # st.image("pic2.png", width=150)
    col_sub_3.markdown("###")
    col_sub_3.markdown("###")

    st.markdown("""<style> 
    #bui10__anchor > button > div > p:first-child {
    background-color: white;
    color: black;
    height:2em; 
    width:10em; 
    border-radius:5px 5px 5px 5px;
    border: 3px solid #008CBA;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown("""<style> 
    #bui10__anchor > button > div > p:hover {
    background-color: #008CBA;
    color: white;
    }
    </style>""", unsafe_allow_html=True)
    st.markdown("""<style>
    #bui10__anchor > button
    {
    padding-top:0px;
    padding-bottom:0px;
    padding-right:0px;
    padding-left:0px;
    border-top-width:0px;
    border-bottom-width:0px;
    border-right-width:0px;
    border-left-width:0px;
    }
    </style>""", unsafe_allow_html=True)

    button5 = col_sub_3.button('发送数据至服务器', help="发送数据",)

    if button4:  # 开始识别按钮
        if len(st.session_state.parameters['final_read_file_df']) != 0 \
                and len(st.session_state.parameters['sensor_dfs']) != 0 \
                and len(st.session_state.parameters['unique_ids']) != 0:
            # 通过50振动传感器信号阈值识别目标
            if 55 not in st.session_state.parameters['unique_ids']:
                # 通过传感器信号阈值识别目标
                target_mblb_tmp = {}
                for tmp_id in st.session_state.parameters['unique_ids']:  # 检测所有传感器
                    # if (sensor_dfs[tmp_id]['Audio'] >= 100).any() or (
                    #         (sensor_dfs[tmp_id]['X_Accel'] >= 5000).any() and sensor_dfs[tmp_id]['X_Accel'] <= 10000).any()  \
                    #         or (sensor_dfs[tmp_id]['X_Mag'] >= 20000).any():
                    #     target_mblb_tmp.update(
                    #         {
                    #             tmp_id: '无' # 车辆
                    #         }
                    #     )
                    if (st.session_state.parameters['sensor_dfs'][tmp_id]['Audio'] >= 60).any() or \
                            (st.session_state.parameters['sensor_dfs'][tmp_id]['X_Accel'] >= 2500).any():
                        target_mblb_tmp.update(
                            {
                                tmp_id: '人员'
                            }
                        )
                    else:
                        target_mblb_tmp.update(
                            {
                                tmp_id: '无'
                            }
                        )

                # 判断是否全为 '无'
                if all(value == '无' for value in target_mblb_tmp.values()):
                    print("未识别到目标")
                    warning_container.empty()
                    warning_container.image("pic2-2.png", width=150)
                else:
                    # 统计人员和车辆的数量
                    person_count = sum(value == '人员' for value in target_mblb_tmp.values())
                    vehicle_count = sum(value == '人员' for value in target_mblb_tmp.values())

                    # 根据数量判断目标类型
                    if person_count > vehicle_count:
                        target_mblb = '人员'
                        id_list = [str(key) for key, value in target_mblb_tmp.items() if value == '人员']
                        col_sub_2.image("pic1.png", width=120)
                    else:
                        target_mblb = '人员'
                        id_list = [str(key) for key, value in target_mblb_tmp.items() if value == '人员']
                        col_sub_2.image("pic1.png", width=120) # pic3 车辆

                    warning_container.empty()
                    warning_container.image("pic2.png", width=150)
                    trans_data_1 = {}
                    trans_data_1.update(
                        {
                            'JDMIN': st.session_state.parameters['final_read_file_df']['N'].min(),
                            'JDMAX': st.session_state.parameters['final_read_file_df']['N'].max(),
                            'WDMIN': st.session_state.parameters['final_read_file_df']['E'].min(),
                            'WDMAX': st.session_state.parameters['final_read_file_df']['E'].max(),
                            'MBLB': target_mblb,
                            'MBGS': str(1),
                            'SBXH': '振动',
                            'FXSJ': st.session_state.parameters['final_read_file_df']['T'][0],
                            'IDLIST': id_list
                        }
                    )
                    url = 'http://51.51.51.15:9011/api/WLW_MLFW/sendTargetInfo'
                    # response = requests.post(url, json=trans_data_1)
                    print(trans_data_1)

                    # st.markdown(trans_data_1)
            else:  # 通过50振动传感器信号
                if (st.session_state.parameters['sensor_dfs'][55]['X_Mag'] == 1).any():
                    target_mblb = '人员'
                    id_list = ['1']
                elif (st.session_state.parameters['sensor_dfs'][55]['X_Mag'] == 2).any():
                    target_mblb = '人员'
                    id_list = ['2']
                elif (st.session_state.parameters['sensor_dfs'][55]['X_Mag'] == 3).any():
                    target_mblb = '人员'
                    id_list = ['3']
                elif (st.session_state.parameters['sensor_dfs'][55]['X_Mag'] == 4).any():
                    target_mblb = '人员'
                    id_list = ['4']
                else:
                    target_mblb = '无'
                    id_list = []

                if target_mblb != '无':
                    trans_data_1 = {}
                    trans_data_1.update(
                        {
                            'JDMIN': st.session_state.parameters['final_read_file_df']['N'].min(),
                            'JDMAX': st.session_state.parameters['final_read_file_df']['N'].max(),
                            'WDMIN': st.session_state.parameters['final_read_file_df']['E'].min(),
                            'WDMAX': st.session_state.parameters['final_read_file_df']['E'].max(),
                            'MBLB': target_mblb,
                            'MBGS': str(1),
                            'SBXH': '振动',
                            'FXSJ': st.session_state.parameters['final_read_file_df']['T'][0],
                            'IDLIST': id_list
                        }
                    )
                    url = 'http://51.51.51.15:9011/api/WLW_MLFW/sendTargetInfo'
                    # response = requests.post(url, json=trans_data_1)
                    print(trans_data_1)
                    # st.markdown(trans_data_1)

            for sensID in st.session_state.parameters['unique_ids']:
                if sensID != 55:
                    trans_data_tmp = {}
                    trans_data_tmp.update(
                        {
                            'CGQID': str(sensID),
                            'JD': st.session_state.parameters['sensor_dfs'][sensID]['N'].iloc[0],
                            'WD': st.session_state.parameters['sensor_dfs'][sensID]['E'].iloc[0],
                            'SBSJ': st.session_state.parameters['sensor_dfs'][sensID]['T'].iloc[0],
                            'SZJSD': list(abs(st.session_state.parameters['sensor_dfs'][sensID]['X_Accel'])),
                            'CTL': list(abs(st.session_state.parameters['sensor_dfs'][sensID]['X_Mag'])),
                            'ZS': list(abs(st.session_state.parameters['sensor_dfs'][sensID]['Audio'])),
                        }
                    )
                    url = 'http://51.51.51.15:9011/api/WLW_MLFW/sendSensorInfo'
                    # response_tmp = requests.post(url, json=trans_data_tmp)
                    print(trans_data_tmp)
                    # st.markdown(trans_data_tmp)

            # 创建X,Y,Z轴加速度散点图
            trace1_1 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['X_Accel'],
                mode='lines',
                marker=dict(
                    color='black',
                    size=10,
                    line=dict(
                        color='black',
                        width=1
                    )
                ),
                name='X_Accel'
            )

            trace1_2 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['Y_Accel'],
                mode='lines',
                marker=dict(
                    color='blue',
                    size=10,
                    line=dict(
                        color='blue',
                        width=1
                    )
                ),
                name='Y_Accel'
            )

            trace1_3 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['Z_Accel'],
                mode='lines',
                marker=dict(
                    color='red',
                    size=10,
                    line=dict(
                        color='red',
                        width=1
                    )
                ),
                name='Z_Accel'
            )

            # 创建声频散点图
            trace2 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['Audio'],
                mode='lines',
                marker=dict(
                    color='black',
                    size=10,
                    line=dict(
                        color='black',
                        width=1
                    )
                ),
                name='dB'
            )

            # 创建X,Y,Z轴磁场散点图
            trace3_1 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['X_Mag'],
                mode='lines',
                marker=dict(
                    color='black',
                    size=10,
                    line=dict(
                        color='black',
                        width=1
                    )
                ),
                name='X_Mag'
            )
            trace3_2 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['Y_Mag'],
                mode='lines',
                marker=dict(
                    color='blue',
                    size=10,
                    line=dict(
                        color='blue',
                        width=1
                    )
                ),
                name='Y_Mag'
            )
            trace3_3 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['Z_Mag'],
                mode='lines',
                marker=dict(
                    color='red',
                    size=10,
                    line=dict(
                        color='red',
                        width=1
                    )
                ),
                name='Z_Mag'
            )

            layout = go.Layout(
                width=300,
                height=150,
            )

            # 将两个散点图放在同一个坐标系中
            fig1 = go.Figure(data=[trace1_1, trace1_2, trace1_3], layout=layout)
            fig2 = go.Figure(data=[trace2], layout=layout)

            fig3 = make_subplots(specs=[[{"secondary_y": True}]])
            fig3.add_trace(trace3_1, secondary_y=False)
            fig3.add_trace(trace3_2, secondary_y=False)
            fig3.add_trace(trace3_3, secondary_y=True)

            fig1.update_layout(
                margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
                # title="",
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                # xaxis_title='时间 - [秒]',
                yaxis_title='振动信号',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    # yanchor="bottom",
                    y=1.5,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),
                yaxis=dict(

                    showline=True,
                    showgrid=True,
                    mirror=True,
                    nticks=11,
                    showticklabels=True,
                ),
            )
            fig2.update_layout(
                margin=dict(l=0,r=10,t=0,b=0),  # margin=dict(l=5, r=5, t=5, b=5)
                # title="",
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                # xaxis_title='时间 - [秒]',
                yaxis_title='声频信号',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    # yanchor="bottom",
                    y=1.5,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),
                yaxis=dict(
                    showline=True,
                    showgrid=True,
                    mirror=True,
                    nticks=8,
                    showticklabels=True,
                ),
            )

            fig3.update_yaxes(title_text="X,Y轴磁场信号", nticks=11, secondary_y=False)
            fig3.update_yaxes(title_text="Z轴磁场信号",
                              showline=True,
                              showgrid=True,
                              mirror=True,
                              nticks=11,
                              showticklabels=True,
                              secondary_y=True)
            fig3.update_layout(
                # title="",
                width=300,
                height=200,
                margin=dict(l=0, r=10, t=0, b=0),
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                xaxis_title='时间 - [秒]',
                # yaxis_title='质量累计含量R(x) - [%]',
                showlegend=True,
                legend=dict(
                    font=dict(size=12),
                    orientation="h",
                    # yanchor="bottom",
                    y=1.4,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),

            )

            col_sub_1.plotly_chart(fig1, use_container_width=True)
            col_sub_1.plotly_chart(fig2, use_container_width=True)
            col_sub_1.plotly_chart(fig3, use_container_width=True)

        else:  # 没有数据
            warning_container.empty()
            warning_container.image("pic2-2.png", width=150)
            layout = go.Layout(
                width=300,
                height=150,
            )
            layout1 = go.Layout(
                width=300,
                height=180,
            )
            # 将两个散点图放在同一个坐标系中
            fig1 = go.Figure(data=[], layout=layout)
            fig2 = go.Figure(data=[], layout=layout)
            fig3 = go.Figure(data=[], layout=layout1)

            fig1.update_layout(
                margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
                # title="",
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                # xaxis_title='时间 - [秒]',
                yaxis_title='振动信号',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    # yanchor="bottom",
                    y=1.5,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),
                yaxis=dict(

                    showline=True,
                    showgrid=True,
                    mirror=True,
                    nticks=11,
                    showticklabels=True,
                ),
            )
            fig2.update_layout(
                margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
                # title="",
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                # xaxis_title='时间 - [秒]',
                yaxis_title='声频信号',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    # yanchor="bottom",
                    y=1.5,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),
                yaxis=dict(

                    showline=True,
                    showgrid=True,
                    mirror=True,
                    nticks=11,
                    showticklabels=True,
                ),
            )
            fig3.update_layout(
                margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
                # title="",
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                xaxis_title='时间 - [秒]',
                yaxis_title='磁场信号',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    # yanchor="bottom",
                    y=1.5,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),
                yaxis=dict(

                    showline=True,
                    showgrid=True,
                    mirror=True,
                    nticks=11,
                    showticklabels=True,
                ),
            )

            col_sub_1.plotly_chart(fig1, use_container_width=True)
            col_sub_1.plotly_chart(fig2, use_container_width=True)
            col_sub_1.plotly_chart(fig3, use_container_width=True)

    elif not button5:
        warning_container.empty()
        warning_container.image("pic2-2.png", width=150)
        layout = go.Layout(
            width=300,
            height=150,
        )
        layout1 = go.Layout(
            width=300,
            height=180,
        )
        # 将两个散点图放在同一个坐标系中
        fig1 = go.Figure(data=[], layout=layout)
        fig2 = go.Figure(data=[], layout=layout)
        fig3 = go.Figure(data=[], layout=layout1)

        fig1.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            # xaxis_title='时间 - [秒]',
            yaxis_title='振动信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )
        fig2.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            # xaxis_title='时间 - [秒]',
            yaxis_title='声频信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )
        fig3.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            yaxis_title='磁场信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )


        col_sub_1.plotly_chart(fig1, use_container_width=True)
        col_sub_1.plotly_chart(fig2, use_container_width=True)
        col_sub_1.plotly_chart(fig3, use_container_width=True)

    if button5: # 报警按钮
        # 将字典转换为JSON格式
        # warning_container.empty()
        # warning_container.image("pic2.png", width=150)

        if len(st.session_state.parameters['final_read_file_df']) != 0 \
                and len(st.session_state.parameters['sensor_dfs']) != 0 \
                and len(st.session_state.parameters['unique_ids']) != 0:
            # 通过50振动传感器信号阈值识别目标
            if 55 not in st.session_state.parameters['unique_ids']:
                # 通过传感器信号阈值识别目标
                target_mblb_tmp = {}
                for tmp_id in st.session_state.parameters['unique_ids']:  # 检测所有传感器
                    # if (sensor_dfs[tmp_id]['Audio'] >= 100).any() or (
                    #         (sensor_dfs[tmp_id]['X_Accel'] >= 5000).any() and sensor_dfs[tmp_id]['X_Accel'] <= 10000).any()  \
                    #         or (sensor_dfs[tmp_id]['X_Mag'] >= 20000).any():
                    #     target_mblb_tmp.update(
                    #         {
                    #             tmp_id: '无' # 车辆
                    #         }
                    #     )
                    if (st.session_state.parameters['sensor_dfs'][tmp_id]['Audio'] >= 60).any() or \
                            (st.session_state.parameters['sensor_dfs'][tmp_id]['X_Accel'] >= 2500).any():
                        target_mblb_tmp.update(
                            {
                                tmp_id: '人员'
                            }
                        )
                    else:
                        target_mblb_tmp.update(
                            {
                                tmp_id: '无'
                            }
                        )

                # 判断是否全为 '无'
                if all(value == '无' for value in target_mblb_tmp.values()):
                    print("未识别到目标")
                    warning_container.empty()
                    warning_container.image("pic2-2.png", width=150)
                else:
                    # 统计人员和车辆的数量
                    person_count = sum(value == '人员' for value in target_mblb_tmp.values())
                    vehicle_count = sum(value == '人员' for value in target_mblb_tmp.values())

                    # 根据数量判断目标类型
                    if person_count > vehicle_count:
                        target_mblb = '人员'
                        id_list = [str(key) for key, value in target_mblb_tmp.items() if value == '人员']
                        col_sub_2.image("pic1.png", width=120)
                    else:
                        target_mblb = '人员'
                        id_list = [str(key) for key, value in target_mblb_tmp.items() if value == '人员']
                        col_sub_2.image("pic1.png", width=120) # pic3 车辆

                    warning_container.empty()
                    warning_container.image("pic2.png", width=150)
                    trans_data_1 = {}
                    trans_data_1.update(
                        {
                            'JDMIN': st.session_state.parameters['final_read_file_df']['N'].min(),
                            'JDMAX': st.session_state.parameters['final_read_file_df']['N'].max(),
                            'WDMIN': st.session_state.parameters['final_read_file_df']['E'].min(),
                            'WDMAX': st.session_state.parameters['final_read_file_df']['E'].max(),
                            'MBLB': target_mblb,
                            'MBGS': str(1),
                            'SBXH': '振动',
                            'FXSJ': st.session_state.parameters['final_read_file_df']['T'][0],
                            'IDLIST': id_list
                        }
                    )
                    url = 'http://51.51.51.15:9011/api/WLW_MLFW/sendTargetInfo'
                    response = requests.post(url, json=trans_data_1)
                    print(trans_data_1)

                    # st.markdown(trans_data_1)
            else:  # 通过50振动传感器信号
                if (st.session_state.parameters['sensor_dfs'][55]['X_Mag'] == 1).any():
                    target_mblb = '人员'
                    id_list = ['1']
                elif (st.session_state.parameters['sensor_dfs'][55]['X_Mag'] == 2).any():
                    target_mblb = '人员'
                    id_list = ['2']
                elif (st.session_state.parameters['sensor_dfs'][55]['X_Mag'] == 3).any():
                    target_mblb = '人员'
                    id_list = ['3']
                elif (st.session_state.parameters['sensor_dfs'][55]['X_Mag'] == 4).any():
                    target_mblb = '人员'
                    id_list = ['4']
                else:
                    target_mblb = '无'
                    id_list = []

                if target_mblb != '无':
                    trans_data_1 = {}
                    trans_data_1.update(
                        {
                            'JDMIN': st.session_state.parameters['final_read_file_df']['N'].min(),
                            'JDMAX': st.session_state.parameters['final_read_file_df']['N'].max(),
                            'WDMIN': st.session_state.parameters['final_read_file_df']['E'].min(),
                            'WDMAX': st.session_state.parameters['final_read_file_df']['E'].max(),
                            'MBLB': target_mblb,
                            'MBGS': str(1),
                            'SBXH': '振动',
                            'FXSJ': st.session_state.parameters['final_read_file_df']['T'][0],
                            'IDLIST': id_list
                        }
                    )
                    url = 'http://51.51.51.15:9011/api/WLW_MLFW/sendTargetInfo'
                    response = requests.post(url, json=trans_data_1)
                    print(trans_data_1)
                    # st.markdown(trans_data_1)

            for sensID in st.session_state.parameters['unique_ids']:
                if sensID != 55:
                    trans_data_tmp = {}
                    trans_data_tmp.update(
                        {
                            'CGQID': str(sensID),
                            'JD': st.session_state.parameters['sensor_dfs'][sensID]['N'].iloc[0],
                            'WD': st.session_state.parameters['sensor_dfs'][sensID]['E'].iloc[0],
                            'SBSJ': st.session_state.parameters['sensor_dfs'][sensID]['T'].iloc[0],
                            'SZJSD': list(abs(st.session_state.parameters['sensor_dfs'][sensID]['X_Accel'])),
                            'CTL': list(abs(st.session_state.parameters['sensor_dfs'][sensID]['X_Mag'])),
                            'ZS': list(abs(st.session_state.parameters['sensor_dfs'][sensID]['Audio'])),
                        }
                    )
                    url = 'http://51.51.51.15:9011/api/WLW_MLFW/sendSensorInfo'
                    response_tmp = requests.post(url, json=trans_data_tmp)
                    print(trans_data_tmp)
                    # st.markdown(trans_data_tmp)

            # 创建X,Y,Z轴加速度散点图
            trace1_1 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['X_Accel'],
                mode='lines',
                marker=dict(
                    color='black',
                    size=10,
                    line=dict(
                        color='black',
                        width=1
                    )
                ),
                name='X_Accel'
            )

            trace1_2 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['Y_Accel'],
                mode='lines',
                marker=dict(
                    color='blue',
                    size=10,
                    line=dict(
                        color='blue',
                        width=1
                    )
                ),
                name='Y_Accel'
            )

            trace1_3 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['Z_Accel'],
                mode='lines',
                marker=dict(
                    color='red',
                    size=10,
                    line=dict(
                        color='red',
                        width=1
                    )
                ),
                name='Z_Accel'
            )

            # 创建声频散点图
            trace2 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['Audio'],
                mode='lines',
                marker=dict(
                    color='black',
                    size=10,
                    line=dict(
                        color='black',
                        width=1
                    )
                ),
                name='dB'
            )

            # 创建X,Y,Z轴磁场散点图
            trace3_1 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['X_Mag'],
                mode='lines',
                marker=dict(
                    color='black',
                    size=10,
                    line=dict(
                        color='black',
                        width=1
                    )
                ),
                name='X_Mag'
            )
            trace3_2 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['Y_Mag'],
                mode='lines',
                marker=dict(
                    color='blue',
                    size=10,
                    line=dict(
                        color='blue',
                        width=1
                    )
                ),
                name='Y_Mag'
            )
            trace3_3 = go.Scatter(
                x=st.session_state.parameters['sensor_dfs'][sensor_node]['T'],
                y=st.session_state.parameters['sensor_dfs'][sensor_node]['Z_Mag'],
                mode='lines',
                marker=dict(
                    color='red',
                    size=10,
                    line=dict(
                        color='red',
                        width=1
                    )
                ),
                name='Z_Mag'
            )

            layout = go.Layout(
                width=300,
                height=150,
            )

            # 将两个散点图放在同一个坐标系中
            fig1 = go.Figure(data=[trace1_1, trace1_2, trace1_3], layout=layout)
            fig2 = go.Figure(data=[trace2], layout=layout)

            fig3 = make_subplots(specs=[[{"secondary_y": True}]])
            fig3.add_trace(trace3_1, secondary_y=False)
            fig3.add_trace(trace3_2, secondary_y=False)
            fig3.add_trace(trace3_3, secondary_y=True)

            fig1.update_layout(
                margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
                # title="",
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                # xaxis_title='时间 - [秒]',
                yaxis_title='振动信号',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    # yanchor="bottom",
                    y=1.5,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),
                yaxis=dict(

                    showline=True,
                    showgrid=True,
                    mirror=True,
                    nticks=11,
                    showticklabels=True,
                ),
            )
            fig2.update_layout(
                margin=dict(l=0,r=10,t=0,b=0),  # margin=dict(l=5, r=5, t=5, b=5)
                # title="",
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                # xaxis_title='时间 - [秒]',
                yaxis_title='声频信号',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    # yanchor="bottom",
                    y=1.5,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),
                yaxis=dict(
                    showline=True,
                    showgrid=True,
                    mirror=True,
                    nticks=8,
                    showticklabels=True,
                ),
            )

            fig3.update_yaxes(title_text="X,Y轴磁场信号", nticks=11, secondary_y=False)
            fig3.update_yaxes(title_text="Z轴磁场信号",
                              showline=True,
                              showgrid=True,
                              mirror=True,
                              nticks=11,
                              showticklabels=True,
                              secondary_y=True)
            fig3.update_layout(
                # title="",
                width=300,
                height=200,
                margin=dict(l=0, r=10, t=0, b=0),
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                xaxis_title='时间 - [秒]',
                # yaxis_title='质量累计含量R(x) - [%]',
                showlegend=True,
                legend=dict(
                    font=dict(size=12),
                    orientation="h",
                    # yanchor="bottom",
                    y=1.4,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),

            )

            col_sub_1.plotly_chart(fig1, use_container_width=True)
            col_sub_1.plotly_chart(fig2, use_container_width=True)
            col_sub_1.plotly_chart(fig3, use_container_width=True)

        else:
            warning_container.empty()
            warning_container.image("pic2-2.png", width=150)
            layout = go.Layout(
                width=300,
                height=150,
            )
            layout1 = go.Layout(
                width=300,
                height=180,
            )
            # 将两个散点图放在同一个坐标系中
            fig1 = go.Figure(data=[], layout=layout)
            fig2 = go.Figure(data=[], layout=layout)
            fig3 = go.Figure(data=[], layout=layout1)

            fig1.update_layout(
                margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
                # title="",
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                # xaxis_title='时间 - [秒]',
                yaxis_title='振动信号',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    # yanchor="bottom",
                    y=1.5,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),
                yaxis=dict(

                    showline=True,
                    showgrid=True,
                    mirror=True,
                    nticks=11,
                    showticklabels=True,
                ),
            )
            fig2.update_layout(
                margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
                # title="",
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                # xaxis_title='时间 - [秒]',
                yaxis_title='声频信号',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    # yanchor="bottom",
                    y=1.5,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),
                yaxis=dict(

                    showline=True,
                    showgrid=True,
                    mirror=True,
                    nticks=11,
                    showticklabels=True,
                ),
            )
            fig3.update_layout(
                margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
                # title="",
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                xaxis_title='时间 - [秒]',
                yaxis_title='磁场信号',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    # yanchor="bottom",
                    y=1.5,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),
                yaxis=dict(

                    showline=True,
                    showgrid=True,
                    mirror=True,
                    nticks=11,
                    showticklabels=True,
                ),
            )

            col_sub_1.plotly_chart(fig1, use_container_width=True)
            col_sub_1.plotly_chart(fig2, use_container_width=True)
            col_sub_1.plotly_chart(fig3, use_container_width=True)



    st.markdown("------")
    # Button Style
    st.markdown("""<style> div.stButton > button:first-child {
    background-color: white;
    color: black;
    height:3em; 
    width:8em; 
    border-radius:10px 10px 10px 10px;
    border: 3px solid #008CBA;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown("""<style> div.stButton > button:hover {
    background-color: #008CBA;
    color: white;
    }
    </style>""", unsafe_allow_html=True)

def app2():
    st.sidebar.success("已选择：📊  目标特征数据库")
    directory_person = "./" \
                       "recognition_data/"
    directory_vehicle = "./" \
                        "recognition_data/"
    db_data_person = pd.read_csv(directory_person + "人员声频.csv")
    db_data_vehicle = pd.read_csv(directory_person + "车辆声频.csv")
    acc_data_person = pd.read_csv(directory_person + "人员振动.csv")
    acc_data_vehicle = pd.read_csv(directory_person + "车辆振动.csv")
    mag_data_person = pd.read_csv(directory_person + "人员磁场.csv")
    mag_data_vehicle = pd.read_csv(directory_person + "车辆磁场.csv")

    st.markdown(
        f'''
            <style>
                .reportview-container .sidebar-content {{
                    padding-top: {0}rem;
                }}
                .appview-container .main .block-container {{
                    {f'max-width: 100%;'}
                    padding-top: {0}rem;
                    padding-right: {1}rem;
                    padding-left: {1}rem;
                    padding-bottom: {0}rem;
                    overflow: auto;
                }}
            </style>
            ''',
        unsafe_allow_html=True,
    )

    st.subheader("  ")

    st.markdown(
        """
        <style>
        .column-color {
            background-color: red;
            padding: 1rem;
            border-radius: 0.25rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


    colmns0 = st.columns(3, gap="large")

    with colmns0[1]:
        # st.session_state.parameters = {}
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold">目标特征数据库</p></nobr>', unsafe_allow_html=True)
        # st.markdown('###')
        st.markdown('###')
        st.markdown('<nobr><p style="font-size: 18px;font-weight: bold">声频信号数据库</p></nobr>', unsafe_allow_html=True)
        selected_dB_type = colmns0[1].radio(
            '选择识别类别：',
            ("人员信号", "车辆信号"), key='dB', horizontal=True)
        # selected_dB_type = colmns0[1].multiselect('选择识别类别：', signal_label, signal_label, key='dB')  # ["人员信号", "车辆信号"]

        selected_dB_disturb = colmns0[1].radio(
            '选择背景扰动类型：',
            ("低背景扰动", "高背景扰动"), key='dB_disturb', horizontal=True)

        if '人员信号' in selected_dB_type:
            distance_list = ['50m', '100m']
        else:
            distance_list = ['200m', '500m']

        selected_dB_distance = colmns0[1].radio(
            '选择距离：',
            distance_list, key='dB_distance', horizontal=True)

        colmns0_1 = colmns0[1].columns([1, 1], gap="small")
        dB_uploaded_file = colmns0_1[0].button("增加数据", key="dB_add_file")
        dB_delete_button = colmns0_1[1].button("删除数据", key="dB_delete_file")

        db_data_person = pd.read_csv(directory_person + "人员声频.csv")
        db_data_vehicle = pd.read_csv(directory_person + "车辆声频.csv")


        if '人员信号' == selected_dB_type:
            final_file_df = db_data_person
            plot_x_axis = final_file_df['Time']
            if '50m' == selected_dB_distance:
                if "低背景扰动" == selected_dB_disturb:
                    plot_y_axis = final_file_df['LowNoiseDis50DB']
                else:
                    plot_y_axis = final_file_df['HighNoiseDis50DB']
            elif '100m' == selected_dB_distance:
                if "低背景扰动" == selected_dB_disturb:
                    plot_y_axis = final_file_df['LowNoiseDis100DB']
                else:
                    plot_y_axis = final_file_df['HighNoiseDis100DB']
        else:  # 车辆信号
            final_file_df = db_data_vehicle
            plot_x_axis = final_file_df['Time']
            if '200m' == selected_dB_distance:
                if "低背景扰动" == selected_dB_disturb:
                    plot_y_axis = final_file_df['LowNoiseDis200DB']
                else:
                    plot_y_axis = final_file_df['HighNoiseDis200DB']
            elif '500m' == selected_dB_distance:
                if "低背景扰动" == selected_dB_disturb:
                    plot_y_axis = final_file_df['LowNoiseDis500DB']
                else:
                    plot_y_axis = final_file_df['HighNoiseDis500DB']

        # 创建声频散点图
        trace2 = go.Scatter(
            x=plot_x_axis,
            y=plot_y_axis,
            mode='lines',
            marker=dict(
                color='black',
                size=10,
                line=dict(
                    color='black',
                    width=1
                )
            ),
            name='dB'
        )

        layout = go.Layout(
            width=300,
            height=280,
        )

        fig2 = go.Figure(data=[trace2], layout=layout)
        fig2.update_layout(
            margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            yaxis_title='声频信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.25,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(
                showline=True,
                showgrid=True,
                mirror=True,
                nticks=8,
                showticklabels=True,
            ),
        )
        colmns0[1].plotly_chart(fig2, use_container_width=True)


    with colmns0[0]:
        # timestr = time.strftime('%Y-%m-%d %H:%M:%S')
        # st.metric(label='时间', value=timestr, label_visibility='collapsed') # visible hidden collapsed
        # st.markdown('###')
        st.markdown(
            '<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>',
            unsafe_allow_html=True)
        st.markdown(
            '<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>',
            unsafe_allow_html=True)
        st.markdown(
            '<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>',
            unsafe_allow_html=True)
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        st.markdown('###')
        # st.markdown('###')
        st.markdown('###')
        st.markdown('<nobr><p style="font-size: 18px;font-weight: bold">振动信号数据库</p></nobr>', unsafe_allow_html=True)
        selected_acc_type = colmns0[0].radio(
            '选择识别类别：',
            ("人员信号", "车辆信号"), key='acc', horizontal=True)

        selected_acc_disturb = colmns0[0].radio(
            '选择背景扰动类型：',
            ("低背景扰动", "高背景扰动"), key='acc_disturb', horizontal=True)

        if '人员信号' in selected_acc_type:
            distance_list = ['10m', '20m']
        else:
            distance_list = ['50m', '100m']

        selected_acc_distance = colmns0[0].radio(
            '选择距离：',
            distance_list, key='acc_distance', horizontal=True)

        colmns0_0 = colmns0[0].columns([1, 1], gap="small")
        acc_uploaded_file = colmns0_0[0].button("增加数据", key="acc_add_file")
        acc_delete_button = colmns0_0[1].button("删除数据", key="acc_delete_file")

        acc_data_person = pd.read_csv(directory_person + "人员振动.csv")
        acc_data_vehicle = pd.read_csv(directory_person + "车辆振动.csv")
        mag_data_person = pd.read_csv(directory_person + "人员磁场.csv")
        mag_data_vehicle = pd.read_csv(directory_person + "车辆磁场.csv")

        if '人员信号' == selected_acc_type:
            final_file_df = acc_data_person
            plot_x_axis = final_file_df['Time']
            if '10m' == selected_acc_distance:
                if "低背景扰动" == selected_acc_disturb:
                    plot_y_axis = final_file_df['LowNoiseDis10']
                else:  # 高背景扰动
                    plot_y_axis = final_file_df['HighNoiseDis10']
            elif '20m' == selected_acc_distance:
                if "低背景扰动" == selected_acc_disturb:
                    plot_y_axis = final_file_df['LowNoiseDis20']
                else:
                    plot_y_axis = final_file_df['HighNoiseDis20']
        else:  # 车辆信号
            final_file_df = acc_data_vehicle
            plot_x_axis = final_file_df['Time']
            if '50m' == selected_acc_distance:
                if "低背景扰动" == selected_acc_disturb:
                    plot_y_axis = final_file_df['LowNoiseDis50']
                else:
                    plot_y_axis = final_file_df['HighNoiseDis50']
            elif '100m' == selected_acc_distance:
                if "低背景扰动" == selected_acc_disturb:
                    plot_y_axis = final_file_df['LowNoiseDis100']
                else:
                    plot_y_axis = final_file_df['HighNoiseDis100']

        max_value = plot_y_axis.max()
        min_value = plot_y_axis.min()

        # 创建X,Y,Z轴加速度散点图
        trace1_1 = go.Scatter(
            x=plot_x_axis,
            y=plot_y_axis,
            mode='lines',
            marker=dict(
                color='black',
                size=10,
                line=dict(
                    color='black',
                    width=1
                )
            ),
            name='X_Accel'
        )

        trace1_2 = go.Scatter(
            x=plot_x_axis,
            y=plot_y_axis.apply(lambda x: round(((x - min_value) * (100 - (-100)) / (max_value - min_value)) + (-100))),
            mode='lines',
            marker=dict(
                color='blue',
                size=10,
                line=dict(
                    color='blue',
                    width=1
                )
            ),
            name='Y_Accel'
        )

        trace1_3 = go.Scatter(
            x=plot_x_axis,
            y=plot_y_axis.apply(lambda x: x*5),
            mode='lines',
            marker=dict(
                color='red',
                size=10,
                line=dict(
                    color='red',
                    width=1
                )
            ),
            name='Z_Accel'
        )

        layout = go.Layout(
            width=300,
            height=280,
        )

        # 将两个散点图放在同一个坐标系中
        fig1 = go.Figure(data=[trace1_1, trace1_2, trace1_3], layout=layout)
        fig1.update_layout(
            margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            yaxis_title='振动信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.25,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )

        colmns0[0].plotly_chart(fig1, use_container_width=True)


    with colmns0[2]:
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; '
                    'font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; '
                    'font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        # st.markdown('###')
        st.markdown('###')
        # st.markdown('###')
        st.markdown('###')
        st.markdown('###')
        st.markdown('<nobr><p style="font-size: 18px;font-weight: bold">磁场信号数据库</p></nobr>', unsafe_allow_html=True)
        selected_mag_type = colmns0[2].radio(
            '选择识别类别：',
            ("人员信号", "车辆信号"), key='mag', horizontal=True)

        selected_mag_disturb = colmns0[2].radio(
            '选择背景扰动类型：',
            ("低背景扰动", "高背景扰动"), key='mag_disturb', horizontal=True)

        if '人员信号' in selected_mag_type:
            distance_list = ['25m', '50m']
        else:
            distance_list = ['100m', '200m']

        selected_mag_distance = colmns0[2].radio(
            '选择距离：',
            distance_list, key='mag_distance', horizontal=True)

        colmns0_2 = colmns0[2].columns([1, 1], gap="small")
        mag_uploaded_file = colmns0_2[0].button("增加数据", key="mag_add_file")
        mag_delete_button = colmns0_2[1].button("删除数据", key="mag_delete_file")

        mag_data_person = pd.read_csv(directory_person + "人员磁场.csv")
        mag_data_vehicle = pd.read_csv(directory_person + "车辆磁场.csv")

        if '人员信号' == selected_mag_type:
            final_file_df = mag_data_person
            plot_x_axis = final_file_df['Time']
            if '25m' == selected_mag_distance:
                if "低背景扰动" == selected_mag_disturb:
                    plot_y_axis = final_file_df['LowNoiseDis25']
                else:  # 高背景扰动
                    plot_y_axis = final_file_df['HighNoiseDis25']
            elif '50m' == selected_mag_distance:
                if "低背景扰动" == selected_mag_disturb:
                    plot_y_axis = final_file_df['LowNoiseDis50']
                else:
                    plot_y_axis = final_file_df['HighNoiseDis50']
        else:  # 车辆信号
            final_file_df = mag_data_vehicle
            plot_x_axis = final_file_df['Time']
            if '100m' == selected_mag_distance:
                if "低背景扰动" == selected_mag_disturb:
                    plot_y_axis = final_file_df['LowNoiseDis100']
                else:
                    plot_y_axis = final_file_df['HighNoiseDis100']
            elif '200m' == selected_mag_distance:
                if "低背景扰动" == selected_mag_disturb:
                    plot_y_axis = final_file_df['LowNoiseDis200']
                else:
                    plot_y_axis = final_file_df['HighNoiseDis200']

        max_value = plot_y_axis.max()
        min_value = plot_y_axis.min()

        # 创建X,Y,Z轴磁场散点图
        trace3_1 = go.Scatter(
            x=plot_x_axis,
            y=plot_y_axis,
            mode='lines',
            marker=dict(
                color='black',
                size=10,
                line=dict(
                    color='black',
                    width=1
                )
            ),
            name='X_Mag'
        )
        trace3_2 = go.Scatter(
            x=plot_x_axis,
            y=plot_y_axis.apply(lambda x: x*0.5),
            mode='lines',
            marker=dict(
                color='blue',
                size=10,
                line=dict(
                    color='blue',
                    width=1
                )
            ),
            name='Y_Mag'
        )
        trace3_3 = go.Scatter(
            x=plot_x_axis,
            y=plot_y_axis.apply(lambda x: x*0.25),
            mode='lines',
            marker=dict(
                color='red',
                size=10,
                line=dict(
                    color='red',
                    width=1
                )
            ),
            name='Z_Mag'
        )

        layout = go.Layout(
            width=300,
            height=280,
        )

        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(trace3_1, secondary_y=False)
        fig3.add_trace(trace3_2, secondary_y=False)
        fig3.add_trace(trace3_3, secondary_y=True)
        fig3.update_yaxes(title_text="X,Y轴磁场信号", nticks=11, secondary_y=False)
        fig3.update_yaxes(title_text="Z轴磁场信号",
                          showline=True,
                          showgrid=True,
                          mirror=True,
                          nticks=11,
                          showticklabels=True,
                          secondary_y=True)
        fig3.update_layout(
            # title="",
            width=300,
            height=280,
            margin=dict(l=0, r=10, t=20, b=0),
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            # yaxis_title='质量累计含量R(x) - [%]',
            showlegend=True,
            legend=dict(
                font=dict(size=12),
                orientation="h",
                # yanchor="bottom",
                y=1.25,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),

        )
        colmns0[2].plotly_chart(fig3, use_container_width=True)



    st.markdown("------")

    st.markdown("""<style>.css-16idsys p
    {
    word-break: break-word;
    margin-bottom: 10px;
    font-size: 15px;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown('###')

def app3():
    st.sidebar.success("已选择：📈  感知历史数据库")
    directory = "./sensor_files/"

    # 获取目录下的所有文件名，并按照数字序号排序
    files_name = sorted(os.listdir(directory), key=sort_by_number)
    files_nums = []
    files_time = []

    # 定义匹配数字序号的正则表达式
    pattern = r'\d+'

    # 循环处理每个文件
    for filename in files_name:
        # 仅处理.txt文件
        if filename.endswith('.txt'):
            # 提取数字序号
            files_nums.append(re.findall(pattern, filename)[0])
            # 打开文件并读取第一行内容
            with open(directory + filename, 'r') as f:
                first_line = f.readline()
                start_index = first_line.find("T:") + 2
                end_index = first_line.find("N:")
                time_str = first_line[start_index:end_index]
                files_time.append(datetime.datetime.utcfromtimestamp(float(time_str)
                                                                     + 1682395190).strftime('%Y-%m-%d %H:%M:%S'))
            # 提取T和N之间的数字
            # t_value = re.findall(r'T:(\d+\.\d+)', first_line)[0]
            # n_value = re.findall(r'N:(\d+\.\d+)', first_line)[0]
            # 输出结果
            # print(f'File {filename} has number {number}, Time value {time_str}')
    # 将传感器编号左填补为001，002
    files_str_nums = [str(num).zfill(3) for num in files_nums]
    # 获取传感器序列号2023001，2023002
    sensors_label = ['2023' + str(num1) for num1 in files_str_nums]
    curr_status = []
    curr_power = []
    for labels in range(len(sensors_label)):
        curr_status.append('通信正常')
        curr_power.append('正常')
    sensors_label_df = pd.DataFrame({'节点序列号': sensors_label, '当前状态': curr_status, '电量': curr_power})

    sensors_df = pd.DataFrame({'labels': files_str_nums, 'time': files_time})
    # 将日期时间列解析为 Pandas 中的日期时间格式
    sensors_df['time'] = pd.to_datetime(sensors_df['time'], format='%Y-%m-%d %H:%M:%S')

    # 对 DataFrame 进行日期时间排序
    sorted_df = sensors_df.sort_values(by='time', ascending=False).reset_index(drop=True)

    txt_name_time = []
    for name_index in range(len(sorted_df['time'])):
        txt_name_time.append("●  节点2023" + sorted_df['labels'][name_index] + "于" + str(sorted_df['time'][name_index]) + "识别到振动信号")
    txt_name_time_df = pd.DataFrame({'txt': txt_name_time})



    # MAGE_EMOJI_URL = "streamlitBKN.png"
    # st.set_page_config(page_title='环境传感器目标识别平台', page_icon=MAGE_EMOJI_URL, initial_sidebar_state='collapsed',
    #                    layout="wide")

    st.markdown(
        f'''
            <style>
                .reportview-container .sidebar-content {{
                    padding-top: {0}rem;
                }}
                .appview-container .main .block-container {{
                    {f'max-width: 100%;'}
                    padding-top: {0}rem;
                    padding-right: {1}rem;
                    padding-left: {1}rem;
                    padding-bottom: {0}rem;
                    overflow: auto;
                }}
            </style>
            ''',
        unsafe_allow_html=True,
    )

    st.subheader("  ")

    st.markdown(
        """
        <style>
        .column-color {
            background-color: red;
            padding: 1rem;
            border-radius: 0.25rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


    colmns0 = st.columns(3, gap="large")

    # st.container()
    # page_button = st.sidebar.selectbox('请选择', ['选项1', '选项2', '选项3'])
    # if page_button:
    #     option = st.sidebar.selectbox('请选择', ['选项1', '选项2', '选项3'])
    #     st.write('你选择了：', option)

    with colmns0[1]:
        # st.session_state.parameters = {}
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold">感知历史数据库</p></nobr>', unsafe_allow_html=True)
        # st.markdown('###')
        # st.markdown('###')

        multi_line_str = "\n".join(sensors_label)
        st.markdown('<nobr><p style="font-size: 18px;font-weight: bold">环境感知节点</p></nobr>', unsafe_allow_html=True)
        txt_node = st.text_area(label="环境感知节点", value=multi_line_str, height=200, label_visibility='collapsed')
        selected_node = st.selectbox('选择节点：', sensors_label)

    with colmns0[0]:
        # timestr = time.strftime('%Y-%m-%d %H:%M:%S')
        # st.metric(label='时间', value=timestr, label_visibility='collapsed') # visible hidden collapsed
        # st.markdown('###')
        st.markdown(
            '<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>',
            unsafe_allow_html=True)
        st.markdown(
            '<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>',
            unsafe_allow_html=True)
        st.markdown(
            '<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>',
            unsafe_allow_html=True)
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        # st.markdown('###')
        # st.markdown('###')
        st.markdown('###')
        tempt_date = sorted_df['time'].dt.strftime('%Y-%m-%d').tolist()
        multi_line_str2 = "\n".join(tempt_date)
        st.markdown('<nobr><p style="font-size: 18px;font-weight: bold">环境感知日期</p></nobr>', unsafe_allow_html=True)
        txt_date = st.text_area(label="环境感知日期", value=multi_line_str2, height=200, label_visibility='collapsed')
        # st.markdown('###')
        # st.markdown('###')
        selected_date = st.date_input('选择日期：', value=datetime.date(2023, 5, 1), min_value=datetime.date(2023, 1, 1),
                                      max_value=datetime.datetime.now()) # , key='date_filter'
    with colmns0[2]:

        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        # st.markdown('###')
        # st.markdown('###')

        st.markdown('###')
        st.markdown('###')
        # st.markdown('###')
        signal_label = ["振动信号", "声频信号", "磁场信号"]
        multi_line_str3 = "\n".join(signal_label)
        st.markdown('<nobr><p style="font-size: 18px;font-weight: bold">环境感知数据</p></nobr>', unsafe_allow_html=True)
        txt_signal = st.text_area(label="环境感知数据", value=multi_line_str3, height=200, label_visibility='collapsed')
        selected_signal = st.multiselect('选择信号：', signal_label, signal_label)

    read_files_name = 'sensor_' + str(int(selected_node[4:])) + '_gps.txt'
    # st.markdown(read_files_name)
    # 读取文本文件
    read_file_df = pd.read_csv('./sensor_files/'
                               + read_files_name, sep=',', header=None)
    final_file_df = read_files_split1(read_file_df)
    # final_file_df['Audio'] = final_file_df['Audio'].apply(lambda x: x / 100)

    # 创建X,Y,Z轴加速度散点图
    trace1_1 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['X_Accel'],
        mode='lines',
        marker=dict(
            color='black',
            size=10,
            line=dict(
                color='black',
                width=1
            )
        ),
        name='X_Accel'
    )

    trace1_2 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['Y_Accel'],
        mode='lines',
        marker=dict(
            color='blue',
            size=10,
            line=dict(
                color='blue',
                width=1
            )
        ),
        name='Y_Accel'
    )

    trace1_3 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['Z_Accel'].apply(lambda x: x * -1),
        mode='lines',
        marker=dict(
            color='red',
            size=10,
            line=dict(
                color='red',
                width=1
            )
        ),
        name='Z_Accel'
    )

    # 创建声频散点图
    trace2 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['Audio'],
        mode='lines',
        marker=dict(
            color='black',
            size=10,
            line=dict(
                color='black',
                width=1
            )
        ),
        name='dB'
    )

    # 创建X,Y,Z轴磁场散点图
    trace3_1 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['X_Mag'].apply(lambda x: x * -1),
        mode='lines',
        marker=dict(
            color='black',
            size=10,
            line=dict(
                color='black',
                width=1
            )
        ),
        name='X_Mag'
    )
    trace3_2 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['Y_Mag'].apply(lambda x: x * -1),
        mode='lines',
        marker=dict(
            color='blue',
            size=10,
            line=dict(
                color='blue',
                width=1
            )
        ),
        name='Y_Mag'
    )
    trace3_3 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['Z_Mag'],
        mode='lines',
        marker=dict(
            color='red',
            size=10,
            line=dict(
                color='red',
                width=1
            )
        ),
        name='Z_Mag'
    )

    layout = go.Layout(
        width=300,
        height=280,
    )

    # 将两个散点图放在同一个坐标系中
    fig1 = go.Figure(data=[trace1_1, trace1_2, trace1_3], layout=layout)
    fig2 = go.Figure(data=[trace2], layout=layout)

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(trace3_1, secondary_y=False)
    fig3.add_trace(trace3_2, secondary_y=False)
    fig3.add_trace(trace3_3, secondary_y=True)

    fig1.update_layout(
        margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
        # title="",
        xaxis_gridcolor="lightgray",
        yaxis_gridcolor="lightgray",
        xaxis_title='时间 - [秒]',
        yaxis_title='振动信号',
        showlegend=True,
        legend=dict(
            orientation="h",
            # yanchor="bottom",
            y=1.25,
            # xanchor="right",
            x=0
        ),
        xaxis=dict(
            showline=True,
            showgrid=True,
            showticklabels=True,
            mirror=True,
            # nticks=21,
        ),
        yaxis=dict(

            showline=True,
            showgrid=True,
            mirror=True,
            nticks=11,
            showticklabels=True,
        ),
    )
    fig2.update_layout(
        margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
        # title="",
        xaxis_gridcolor="lightgray",
        yaxis_gridcolor="lightgray",
        xaxis_title='时间 - [秒]',
        yaxis_title='声频信号',
        showlegend=True,
        legend=dict(
            orientation="h",
            # yanchor="bottom",
            y=1.25,
            # xanchor="right",
            x=0
        ),
        xaxis=dict(
            showline=True,
            showgrid=True,
            showticklabels=True,
            mirror=True,
            # nticks=21,
        ),
        yaxis=dict(
            showline=True,
            showgrid=True,
            mirror=True,
            nticks=8,
            showticklabels=True,
        ),
    )

    fig3.update_yaxes(title_text="X,Y轴磁场信号", nticks=11, secondary_y=False)
    fig3.update_yaxes(title_text="Z轴磁场信号",
                      showline=True,
                      showgrid=True,
                      mirror=True,
                      nticks=11,
                      showticklabels=True,
                      secondary_y=True)
    fig3.update_layout(
        # title="",
        width=300,
        height=280,
        margin=dict(l=0, r=10, t=20, b=0),
        xaxis_gridcolor="lightgray",
        yaxis_gridcolor="lightgray",
        xaxis_title='时间 - [秒]',
        # yaxis_title='质量累计含量R(x) - [%]',
        showlegend=True,
        legend=dict(
            font=dict(size=12),
            orientation="h",
            # yanchor="bottom",
            y=1.25,
            # xanchor="right",
            x=0
        ),
        xaxis=dict(
            showline=True,
            showgrid=True,
            showticklabels=True,
            mirror=True,
            # nticks=21,
        ),

    )

    if len(selected_signal) != 0:
        if len(selected_signal) == 3:
            colmns1 = st.columns(3, gap="large")
            colmns1[0].plotly_chart(fig1, use_container_width=True)
            colmns1[1].plotly_chart(fig2, use_container_width=True)
            colmns1[2].plotly_chart(fig3, use_container_width=True)
        elif len(selected_signal) == 2:
            colmns1 = st.columns(2, gap="large")
            if "振动信号" in selected_signal:
                colmns1[0].plotly_chart(fig1, use_container_width=True)
                if "声频信号" in selected_signal:
                    colmns1[1].plotly_chart(fig2, use_container_width=True)
                else:
                    colmns1[1].plotly_chart(fig3, use_container_width=True)
            else:
                colmns1[0].plotly_chart(fig2, use_container_width=True)
                colmns1[1].plotly_chart(fig3, use_container_width=True)
        elif len(selected_signal) == 1:
            if "振动信号" in selected_signal:
                st.plotly_chart(fig1, use_container_width=True)
            elif "声频信号" in selected_signal:
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.plotly_chart(fig3, use_container_width=True)
    else:
        colmns1 = st.columns(3, gap="large")
        layout = go.Layout(
            width=300,
            height=280,
        )
        layout1 = go.Layout(
            width=300,
            height=280,
        )
        # 将两个散点图放在同一个坐标系中
        fig1 = go.Figure(data=[], layout=layout)
        fig2 = go.Figure(data=[], layout=layout)
        fig3 = go.Figure(data=[], layout=layout1)

        fig1.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            yaxis_title='振动信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )
        fig2.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            yaxis_title='声频信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )
        fig3.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            yaxis_title='磁场信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )


        colmns1[0].plotly_chart(fig1, use_container_width=True)
        colmns1[1].plotly_chart(fig2, use_container_width=True)
        colmns1[2].plotly_chart(fig3, use_container_width=True)
        colmns0[2].error("请选择需要绘制的信号类型！")

    st.markdown("------")
    st.markdown("""<style>.css-16idsys p
    {
    word-break: break-word;
    margin-bottom: 10px;
    font-size: 18px;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown('###')




st.set_page_config(page_title='传感器目标识别服务', page_icon="streamlitBKN.png", initial_sidebar_state='collapsed',
                   layout="wide")
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# .css-1wbqy5l

page_names_to_funcs = {
    "🌍  主监测页面": app1,
    "📊  目标特征数据库": app2,
    "📈  感知历史数据库": app3
}
st.sidebar.markdown(
    '<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 20px; font-weight: bold">传感器目标识别服务</p></nobr>',
    unsafe_allow_html=True)
# st.sidebar.markdown("###")
st.sidebar.markdown(
    '<nobr><p style="font-family:sans serif; color:Black; font-size: 15px; font-weight: bold">选择页面：</p></nobr>',
    unsafe_allow_html=True)
demo_name = st.sidebar.selectbox("选择页面", page_names_to_funcs.keys(), label_visibility='collapsed')
page_names_to_funcs[demo_name]()
