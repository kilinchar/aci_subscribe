#!/usr/bin/python

import websocket
import json
import requests
import time
import ssl
import sys
import config
import threading
import sqlalchemy
import pandas as pd


apic = config.controller
username = config.username
password = config.password
token = ""
close_message = ""
#APP_Profile_url = "https://" + apic + "/api/class/fvAp.json?subscription=yes&refresh-timeout=500?query-target=subtree"
int_url = "https://" + apic + "/api/node/class/infraHPortS.json?rsp-subtree=full&subscription=yes&refresh-timeout=500?query-target=subtree"
df_url = "https://" + apic + "/api/node/class/infraHPortS.json?rsp-subtree=full&order-by=infraHPortS.modTs|desc"
epg_subs_url = "https://"+ apic + "/api/node/class/fvAEPg.json?subscription=yes&refresh-timeout=500?query-target=subtree"
epg_url = "https://" + apic + """/api/node/class/fvAEPg.json?rsp-subtree=children&rsp-subtree-class=fvRsPathAtt,fvRsDomAtt&rsp-subtree-filter=or(ne(fvRsDomAtt.tCl,"physDomP"),eq(fvRsPathAtt.annotation,""))&order-by=fvAEPg.name"""
table_interface = "interfaces"
table_epg = "epg"
dbname = "dcnm"

def on_open(ws):
    "Open func that is used by WebSocketApp wrapper which start the socket and then subscribe the related MO by using subscription() function."
    "Also it assigns the subscription ID from local var to global var in order to use this ID in refresh function."
    global int_sub_ID
    global epg_sub_ID
    print("Ws is started")
    int_sub_ID = subscription(url=int_url, token=token)
    epg_sub_ID = subscription(url=epg_subs_url, token=token)


def on_message(ws, message):
    "on_message function is being used to receive messages from websocket for subscribed MOs. It is again being used by WebSocketApp wrapper"
    print("Message is Received")
    if msg_parser(message) == int_sub_ID:
        populate_int_table(session, table_interface, engine)
        print("Interface related message is received")
        print(message)
    elif msg_parser(message) == epg_sub_ID:
        populate_epg_table(session, table_epg, engine)
        print ("EPG Subs message is received")
        print(message)
    else:
        print("Nothing is matched")
        print(message)

def on_error(ws, error):
    "on_error function is being used to receive errors from websocket. It is again being used by WebSocketApp wrapper"
    print(error)

def on_close(ws):
    "on_close function is being used to close the websocket and print goodbye message. It is again being used by WebSocketApp wrapper"
    "Also it assigns close message as global var in order to break infinite refresh loop in case Websocket is closed"
    global close_message
    close_message = "Websocket is closed"
    print("Websocket is closed")




def login():
    "Regular APIC login function in order to login and return cookie token"
    base_url = "https://" + apic + "/api/"
    auth_bit = "aaaLogin.json"
    auth_url = base_url + auth_bit
    auth_data = {
        "aaaUser": {
            "attributes": {
                "name": username,
                "pwd": password
            }
        }
    }
    requests.packages.urllib3.disable_warnings()
    s = requests.session()
    login = s.post(auth_url, json=auth_data, verify=False)
    response_body = login.content
    response_body_dictionary = json.loads(response_body)
    token = response_body_dictionary["imdata"][0]["aaaLogin"]["attributes"]["token"]
    if login.ok:
        token = response_body_dictionary["imdata"][0]["aaaLogin"]["attributes"]["token"]
    else:
        print("Unable to login")
        pass   
    return token, s


def subscription(url, token):
    "subscription function in order to subscribe related MO on APIC and return subscription_id for future use(refresh)"
    cookie = {"APIC-cookie": token}
    subscription_req = requests.get(url, verify=False, cookies=cookie)
    #print(subscription_req.text)
    json_dict = json.loads(subscription_req.text)
    subscription_id = json_dict["subscriptionId"]
    print ("Subscription ID: ", subscription_id)
    return subscription_id

def refresh():
    "Refresh function in order to refresh session before it aged out"
    while True:
        if close_message == "Websocket is closed":
            print("Since Websocket is closed, breaking refresh loop for MO subscriptions")
            break
        else:
            time.sleep(480)
            global session
            login_l = login()
            token = login_l[0]
            session = login_l[1]
            cookie = {"APIC-cookie": token}
            int_refresh_url = "https://" + apic + "/api/subscriptionRefresh.json?id={}".format(int_sub_ID)
            epg_refresh_url = "https://" + apic + "/api/subscriptionRefresh.json?id={}".format(epg_sub_ID)
            int_refresh_response = requests.get(int_refresh_url, verify=False, cookies=cookie)
            epg_refresh_response = requests.get(epg_refresh_url, verify=False, cookies=cookie)
            print(int_refresh_response.content)
            print(epg_refresh_response.content)


def msg_parser(message):
    message_dict = json.loads(message)
    subscription_value = message_dict["subscriptionId"][0]
    return subscription_value


def populate_int_table(s, table, engine):
    s_response = s.get(df_url, verify=False)
    s_int_list = s_response.json()["imdata"]
    int_dic = {}
    i = 0
    for int in s_int_list:
        attributes = int["infraHPortS"]["attributes"]
        cc = int["infraHPortS"]["children"]
        for k in cc:
            if "infraRsAccBaseGrp" in k:
                infraRsAccBaseGrp = k["infraRsAccBaseGrp"]["attributes"]["tDn"]
                splittes_Acc = infraRsAccBaseGrp.split("/")[3]
                vpc = splittes_Acc.split("-")[1]
                dn = attributes["dn"]
                intprof = dn.split("/")[2][12:]
                splitted_intprof = intprof.split("_")
                hport = dn.split("/")[3]
                name = hport.split("-")[1]
                if splitted_intprof[0] == "LEAF":
                    node_id = splitted_intprof[1]
                    d = {i: {"Name": name, "VPC": vpc, "Intpro": intprof, "Node": node_id}}
                    int_dic.update(d)
                    i += 1
                else:
                    pass
            else:
                pass
    pd.set_option('display.max_rows', 300)
    df = pd.DataFrame.from_dict(int_dic, orient='index')
    df.to_sql(table, con = engine, if_exists='replace', index = False)
    print(df)

def populate_epg_table(s, table, engine):
    s_response = s.get(epg_url, verify=False)
    s_epg_list = s_response.json()["imdata"]
    j = 0
    epg_dic = {}
    for i in s_epg_list:
        if i["fvAEPg"]["attributes"]["dn"].split("/")[1] != "tn-ACI_UMK":
            pass
        else:
            dn = i["fvAEPg"]["attributes"]["dn"]
            ap = dn.split("/")[2][3:]
            if ap.endswith("_AP"):
                vlan2 = ap.split("_")[-2:-1][0]
                vlan = vlan2[1:]
                epg = dn.split("/")[3][4:]
                #custom_epg_name = i["fvAEPg"]["children"][0]["fvRsDomAtt"]["attributes"]["customEpgName"]
                if vlan2.startswith('v'):
                    if any("children" in d for d in i["fvAEPg"]) == True:
                        if any("fvRsDomAtt" in d for d in i["fvAEPg"]["children"]) == True:
                            custom_epg_name = i["fvAEPg"]["children"][0]["fvRsDomAtt"]["attributes"]["customEpgName"]
                            if any("fvRsPathAtt" in d for d in i["fvAEPg"]["children"]) == True:
                                binded_vlan = i["fvAEPg"]["children"][1]["fvRsPathAtt"]["attributes"]["encap"][5:]
                            else:
                                binded_vlan = "No static Binding"
                        else:
                            custom_epg_name = "No VMM Integration"
                            if any("fvRsPathAtt" in d for d in i["fvAEPg"]["children"]) == True:
                                binded_vlan = i["fvAEPg"]["children"][0]["fvRsPathAtt"]["attributes"]["encap"][5:]
                            else:
                                binded_vlan = "No static Binding"
                    else:
                        custom_epg_name = "No VMM Integration"
                        binded_vlan = "No static Binding"
                    dd = {j: {"AP": ap, "EPG": epg, "Custom_EPG_Name": custom_epg_name, "Vlan": vlan, "Already_Exists_Vlan": binded_vlan}}
                    epg_dic.update(dd)
                    j += 1
                else:
                    pass
            else:
                pass

    pd.set_option('display.max_rows', 300)
    df = pd.DataFrame.from_dict(epg_dic, orient='index')
    df.to_sql(table, con = engine, if_exists='replace', index = False)
    print(df)

def db(table1, table2, dbname):
    connect = "postgresql+psycopg2://%s:%s@%s:5432/%s" % (
    config.dbuser,
    config.dbpass,
    config.dbip,
    dbname
)
    create_table_interface = f"""CREATE TABLE IF NOT EXISTS {table1} ( Name text, VPC text, Intpro text, Node text)"""
    create_table_epg = f"""CREATE TABLE IF NOT EXISTS {table2} ( AP text, EPG text, Custom_EPG_Name text, Vlan text, Already_Exists_Vlan text)"""
    engine = sqlalchemy.create_engine(connect)
    conn = engine.raw_connection()
    c = conn.cursor()
    c.execute(create_table_interface)
    c.execute(create_table_epg)
    conn.commit()
    return c, conn, engine

# def insert_db(c, conn, table, name, VPC, intpro ,node):
#     # sql_insert = f"""INSERT INTO {table} (Name, Intpro, Node) VALUES ({name}, {node}, {intpro});"""
#     sql_insert = f"""INSERT INTO {table} (Name, VPC, INTPRO, Node) VALUES (?, ?, ?, ?);"""
#     tup =(name, VPC, intpro, node)
#     c.execute(sql_insert, tup)
#     conn.commit()

# def delete_db(c, conn, table, name):
#     sql_delete =f"""DELETE from {table} WHERE Name = ?"""
#     c.execute(sql_delete, (name,))
#     conn.commit()


if __name__ == "__main__":
    login_list = login()
    session = login_list[1]
    token = login_list[0]
    db_return_list = db(table_interface, table_epg, dbname)
    c = db_return_list[0]
    conn = db_return_list[1]
    engine = db_return_list[2]
    populate_int_table(session, table_interface, engine)
    populate_epg_table(session, table_epg, engine)
    # # delete_db(c, conn, table, "INTPOL_N7K_VPC")
    # # insert_db(c, conn, table, "INTPOL_N7K_VPC", "INTPOL_N7K_VPC", "N7K_VPC_INTPRO", "801-802")
    refreshThread = threading.Thread(target=refresh)
    refreshThread.start()
    websocket.enableTrace(True)
    socket = "wss://" + apic + "/socket" + token
    "WebSocketApp is a wrapper which uses above given functions for ease of operation."
    ws = websocket.WebSocketApp(socket, on_open=on_open, on_message=on_message, on_error = on_error, on_close=on_close)
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}) 
    #### Run in an infinite loop until manually stop it with Ctlr + Z




