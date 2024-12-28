import os
import time
import yfinance as yf
from random import gauss
from statistics import mean
import json, http.client, requests
from flask import Flask, jsonify, request
from datetime import datetime, timedelta, timezone, date

os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred'
import boto3

app = Flask(__name__)
static_path = app.static_folder

instances = []
s = ""
r = 3
h = None
d = None
t = None
p = None

VaR = None
VaR_mean = None
PnL = None
PnL_mean = None
Chart_res = None
time_cost = None
stock_data = None
arg = {
    
  "multiValueQueryStringParameters": {
    "key1": [
      "10.0",
      "10.1",
      "10.2",
      "10.3",
      "10.4",
      "10.0",
      "10.1",
      "10.2",
      "10.3",
      "10.4",
      "10.0",
      "10.1",
      "10.2",
      "10.3",
      "10.4",
      "10.0",
      "10.1",
      "10.2",
      "10.3",
      "10.4",
      "10.0",
      "10.1",
      "10.2",
      "10.3",
      "10.4",
      "10.0",
      "10.1",
      "10.2",
      "10.3",
      "10.4"
    ],
    "key2": [
      "0",
      "1",
      "0",
      "1",
      "0",
      "0",
      "1",
      "0",
      "1",
      "0",
      "0",
      "1",
      "0",
      "1",
      "0",
      "0",
      "1",
      "0",
      "1",
      "0",
      "0",
      "1",
      "0",
      "1",
      "0",
      "0",
      "1",
      "0",
      "1",
      "0"
    ],
    "key3": [
      "0",
      "0",
      "1",
      "0",
      "1",
      "0",
      "0",
      "1",
      "0",
      "1",
      "0",
      "0",
      "1",
      "0",
      "1",
      "0",
      "0",
      "1",
      "0",
      "1",
      "0",
      "0",
      "1",
      "0",
      "1",
      "0",
      "0",
      "1",
      "0",
      "1"
    ]
  },
  "queryStringParameters": {
    "key4": "10",
    "key5": "1000",
    "key6": "Buy",
    "key7": "10"
  }
}
@app.route('/warmup', methods=['POST'])
def warmup():
    global service,scale,instances
    user_input = request.get_json()
    scale = int(user_input.get('r'))

    service = user_input.get('s')
    if service == 'lambda':
        lambda_client = boto3.client("lambda","us-east-1")
        responses = lambda_client.invoke(
            FunctionName="Function1",
            Payload = json.dumps(arg)
        )
        print(responses["Payload"].read().decode("utf-8"))
        print("lambda ready")
    
    elif service == 'ec2':
        user_data = """#!/bin/bash
            wget https://XXXXX.appspot.com/cacheavoid/setup.bash
            bash setup.bash"""

        ec2 = boto3.resource('ec2', region_name='us-east-1')

        global instances
        instances = ec2.create_instances(
            ImageId = 'ami-0005e0cfe09cc9050', 
            MinCount = scale, 
            MaxCount = scale, 
            InstanceType = 't2.micro', 
            KeyName = 'us-east-1kp',
            SecurityGroups=['SSH'], 
            BlockDeviceMappings = 
            [  {'DeviceName' : '/dev/sdf', 'Ebs' : { 'VolumeSize' : 10 } }   ],
            UserData=user_data 
            )
    response = {'result': 'ok'}
    return jsonify(response)

@app.route('/scaled_ready')
def scaled_ready():
    global service
    if service == "lambda":
        return jsonify({'warm': True})
    
    else:
        time.sleep(10)
        ec2_client = boto3.client('ec2',"us-east-1")
        ec2_running = check_instances_running(ec2_client)

        if ec2_running:
            return jsonify({'warm': True})
        else:
            return jsonify({'warm': False})

def calculate_warmup_cost(r):
    ec2_client = boto3.client('ec2',"us-east-1")

    response = ec2_client.describe_instances()
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if instance['State']['Name'] == "running":
                target = instance
                launch_time = target["LaunchTime"]
                warmup_start_time = launch_time
                warmup_end_time = datetime.now(timezone.utc)
                billable_time = (warmup_end_time - warmup_start_time).total_seconds() / 60 *r
                cost_per_minute = 0.00001667
                cost = round(billable_time * cost_per_minute, 2)
                return billable_time, cost 
    return 0,0

@app.route('/get_warmup_cost')
def get_warmup_cost():
    if service == "lambda":
        response = {
            'billable_time': 0,
            'cost': 0
        }
        return jsonify(response)
    else:
        ec2_client = boto3.client('ec2',"us-east-1")
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        instances = response['Reservations']
        r = len(instances)
        billable_time, cost = calculate_warmup_cost(r)
        response = {
            'billable_time': billable_time,
            'cost': cost
        }
        return jsonify(response)


@app.route('/get_endpoints')
def get_endpoints():
    return jsonify({
    "warmup": "curl -H 'Content-Type: application/json' -d <arg> localhost:8888/warmup",
    "scaled_ready": "curl http://127.0.0.1:8888/scaled_ready",
    "get_warmup_cost": "curl http://127.0.0.1:8888/get_warmup_cost",
    "get_endpoints": "curl http://127.0.0.1:8888/get_endpoints",
    "analyse": "curl -X POST -H 'Content-Type: application/json' -d <arg> http://127.0.0.1:8888/analyse",
    "get_sig_vars9599": "curl http://127.0.0.1:8888/get_sig_vars9599",
    "get_avg_vars9599": "curl http://127.0.0.1:8888/get_avg_vars9599",
    "get_sig_profit_loss": "curl http://127.0.0.1:8888/get_sig_profit_loss",
    "get_tot_profit_loss": "curl http://127.0.0.1:8888/get_tot_profit_loss",
    "get_chart_url": "curl http://127.0.0.1:8888/get_chart_url",
    "get_time_cost": "curl http://127.0.0.1:8888/get_time_cost",
    "get_audit": "curl http://127.0.0.1:8888/get_audit",
    "reset": "curl http://127.0.0.1:8888/reset",
    "terminate": "curl http://127.0.0.1:8888/terminate",
    "scaled_terminated": "curl http://127.0.0.1:8888/scaled_terminated"
    })

@app.route("/analyse", methods=["POST"])
def analyse_endpoint():
    global h,d,t,p,minhistory,shots,stock_data
    starting = time.time()
    h = int(request.json.get("h")) 
    d = int(request.json.get("d"))
    t = request.json.get("t") 
    p = int(request.json.get("p"))
    minhistory = h
    shots = d

    ticker = "MSFT"
    stock_data = yf.download(ticker, start=date.today() - timedelta(days=1095), end=date.today())
    stock_data['Buy'] = 0
    stock_data['Sell'] = 0
    for i in range(2, len(stock_data)): 
        body = 0.01
        if (stock_data.Close[i] - stock_data.Open[i]) >= body  \
            and stock_data.Close[i] > stock_data.Close[i-1]  \
            and (stock_data.Close[i-1] - stock_data.Open[i-1]) >= body  \
            and stock_data.Close[i-1] > stock_data.Close[i-2]  \
            and (stock_data.Close[i-2] - stock_data.Open[i-2]) >= body:
            stock_data.at[stock_data.index[i], 'Buy'] = 1

        if (stock_data.Open[i] - stock_data.Close[i]) >= body  \
            and stock_data.Close[i] < stock_data.Close[i-1] \
            and (stock_data.Open[i-1] - stock_data.Close[i-1]) >= body  \
            and stock_data.Close[i-1] < stock_data.Close[i-2]  \
            and (stock_data.Open[i-2] - stock_data.Close[i-2]) >= body:
            stock_data.at[stock_data.index[i], 'Sell'] = 1


    global VaR, VaR_mean, PnL, PnL_mean
    api = 'http://127.0.0.1:8888/get_sig_vars9599'
    VaR = requests.get(api).json()
    api = 'http://127.0.0.1:8888/get_avg_vars9599'
    VaR_mean = requests.get(api).json()
    api = 'http://127.0.0.1:8888/get_sig_profit_loss'
    PnL = requests.get(api).json()
    api = 'http://127.0.0.1:8888/get_tot_profit_loss'
    PnL_mean = requests.get(api).json()
    url = 'http://127.0.0.1:8888/get_chart_url'
    Chart_res = requests.get(url).json()
    ending = time.time()
    global tot_time, time_cost
    tot_time = ending - starting
    api = 'http://127.0.0.1:8888/get_time_cost'
    time_cost = requests.get(api).json()

    return jsonify({"result": "ok"})

@app.route("/get_time_cost", methods=["GET"])
def get_time_cost():
    billable_time = tot_time * r
    cost = billable_time * 0.00001667
    return jsonify({"billable_time":billable_time, "cost":cost})

@app.route("/get_sig_vars9599", methods=["GET"])
def get_sig_vars9599():
    global list_var95, list_var99,service,scale
    if service == "lambda":
        list_var95, list_var99 = [],[]
        candidates = ["Function1","Function2","Function3"]
        for i in candidates[:scale]:
            arg = {
                    
                "multiValueQueryStringParameters": {
                    "key1": list(stock_data["Close"]),
                    "key2": list(stock_data["Buy"]),
                    "key3": list(stock_data["Sell"])
                },
                "queryStringParameters": {
                    "key4": h,
                    "key5": d,
                    "key6": t,
                    "key7": p
                }
            }
            lambda_client = boto3.client("lambda","us-east-1")
            responses = lambda_client.invoke(
                FunctionName=f"{i}",
                Payload = json.dumps(arg),
            )

            response_payload = responses["Payload"]
            res = response_payload.read().decode('utf-8')
            res = json.loads(res)
            res = res["body"]
            res = json.loads(res)
            
            if list_var95 == []:
                
                list_var95.append(res["var95"])
                list_var99.append(res["var99"])
            else:
                list_var95[0] = [(a + b) / 2 for a, b in zip(list_var95[0], res["var95"])]
                list_var99[0] = [(a + b) / 2 for a, b in zip(list_var99[0], res["var99"])]

        VaR = {"var95": list_var95[0], "var99": list_var99[0]}
        return jsonify(VaR)
    else:
        list_var95, list_var99 = [], []
        if t == "Buy":
            for i in range(minhistory, len(stock_data)): 
                if stock_data.Buy[i]==1:
                        mean=stock_data.Close[i-minhistory:i].pct_change(1).mean()
                        std=stock_data.Close[i-minhistory:i].pct_change(1).std()
                        simulated = [gauss(mean,std) for x in range(shots)]
                        simulated.sort(reverse=True)
                        var95 = simulated[int(len(simulated)*0.95)]
                        var99 = simulated[int(len(simulated)*0.99)]
                        list_var95.append(var95)
                        list_var99.append(var99)
        elif t == "Sell":
            for i in range(minhistory, len(stock_data)): 
                if stock_data.Sell[i]==1:
                        mean=stock_data.Close[i-minhistory:i].pct_change(1).mean()
                        std=stock_data.Close[i-minhistory:i].pct_change(1).std()
                        simulated = [gauss(mean,std) for x in range(shots)]
                        simulated.sort(reverse=True)
                        var95 = simulated[int(len(simulated)*0.95)]
                        var99 = simulated[int(len(simulated)*0.99)]
                        list_var95.append(var95)
                        list_var99.append(var99)

        VaR = {"var95": list_var95, "var99": list_var99}
        return jsonify(VaR)

@app.route("/get_avg_vars9599", methods=["GET"])
def get_avg_vars9599():
    avg_var95 = mean(VaR["var95"])
    avg_var99 = mean(VaR["var99"])

    VaR_mean = {
        "avg_var95": avg_var95,
        "avg_var99": avg_var99
    }

    return jsonify(VaR_mean)


@app.route("/get_sig_profit_loss", methods=["GET"])
def get_sig_profit_loss():

    profit_loss_res = []

    if t == "Buy":
        for i in range(minhistory, len(stock_data)): 
            if stock_data.Buy[i] == 1:
                buy_price = stock_data['Close'][i]
                sell_price = stock_data['Close'][min(i + p, len(stock_data) - 1)]
                PnL = sell_price - buy_price
                profit_loss_res.append(PnL)

    elif t == "Sell":
        for i in range(minhistory, len(stock_data)): 
            if stock_data.Sell[i] == 1:
                sell_price = stock_data['Close'][i]
                buy_price = stock_data['Close'][max(0, i - p)]
                PnL = sell_price - buy_price
                profit_loss_res.append(PnL)

    return jsonify({"PnL":profit_loss_res})
        
@app.route("/get_tot_profit_loss", methods=["GET"])
def get_tot_profit_loss():
    PnL_mean = sum(PnL["PnL"])
    return jsonify({'PnL':PnL_mean})

@app.route("/get_audit", methods=["GET"])
def get_audit():
    audit_data = {
        "VaR": VaR,
        "avg_VaR": VaR_mean,
        "profit_loss": PnL,
        "avg_profit_loss": PnL_mean,
        "chart_url": Chart_res,
        "time_cost": time_cost
    }

    return jsonify(audit_data)

@app.route("/reset", methods=["GET"])
def reset():
    global VaR, VaR_mean, PnL, PnL_mean, Chart_res, time_cost
    VaR = None
    VaR_mean = None
    PnL = None
    PnL_mean = None
    Chart_res = None
    time_cost = None
    return jsonify({
        "result": "ok",
    })

@app.route("/get_chart_url", methods=["GET"])
def get_chart_url():

    xticks = [str(i) for i in list(range(len(VaR["var95"])))]
    xticks = '|'.join(xticks)
    VaR95 = ','.join([str(i) for i in VaR["var95"]])
    Mean_VaR95 = ','.join([str(VaR_mean["avg_var95"]) for i in range(len(VaR["var95"]))])
    VaR99 = ','.join([str(i) for i in VaR["var99"]])
    Mean_VaR99 = ','.join([str(VaR_mean["avg_var99"]) for i in range(len(VaR["var95"]))])
    ledend = "VaR95|VaR99|Avg_VaR95|Avg_VaR99"
    
    chart = f"https://image-charts.com/chart?cht=lc&chs=999x720&chd=a:{VaR95}|{VaR99}|{Mean_VaR95}|{Mean_VaR99}&chxt=x,y&chdl={ledend}&chxl=0:|{xticks}&chxs=0,min90&chco=1984C5,C23728,A7D5ED,E1A692&chls=3|3|3,5,3|3,5,3"
    return jsonify({
        "chart1_url": chart,
    })    




def terminate_ec2_instances(ec2_client):
    response = ec2_client.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    instances = response['Reservations']
    instance_ids = []
    for reservation in instances:
        for instance in reservation['Instances']:
            instance_ids.append(instance['InstanceId'])
    
    if instance_ids:
        ec2_client.terminate_instances(InstanceIds=instance_ids)
        return True

    return False

@app.route('/terminate', methods=['GET'])
def terminate_instances():
    ec2_client = boto3.client('ec2',"us-east-1")
    if s == "ec2":
        ec2_terminated = terminate_ec2_instances(ec2_client)
    else:
        pass
    return {"result":"ok"}

@app.route('/scaled_terminated')
def scaled_terminated():
    if service == "ec2":
        ec2_client = boto3.client('ec2',"us-east-1")
        ec2_running = check_instances_running(ec2_client)
        if ec2_running:
            return jsonify({'terminated': False})
        else:
            return jsonify({'terminated': True})
        
    else:
        return jsonify({'terminated': True}) 






if __name__ == '__main__':
    app.run(port = 8888, debug=True)
