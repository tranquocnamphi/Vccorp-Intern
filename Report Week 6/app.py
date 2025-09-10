from flask import Flask, request, render_template, jsonify
import requests
import os
from dotenv import load_dotenv
import re
import json
import random
import time
import string

app = Flask(__name__)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
CRYPTOCOMPARE_API_KEY = os.getenv('CRYPTOCOMPARE_API_KEY')
N8N_API_KEY = os.getenv('N8N_API_KEY')
N8N_HOST = 'n8n'
N8N_PORT = '5678'
N8N_BASE_URL = f'http://{N8N_HOST}:{N8N_PORT}'
N8N_WORKFLOWS_URL = f'{N8N_BASE_URL}/api/v1/workflows'
N8N_RUN_URL = f'{N8N_BASE_URL}/rest/workflows'
N8N_EXECUTIONS_URL = f'{N8N_BASE_URL}/api/v1/executions'

def parse_query(query):
    pattern = r'(avg|average|trung bình|max|tối đa|lớn nhất)\s+(close price|giá đóng cửa|giá close|price|giá|volume|khối lượng)\s+(lớn nhất)?\s*(của)?\s*(\w+)\s*(in\s+\w+|từ\s+\d+\s+đến\s+nay)?'
    match = re.search(pattern, query, re.IGNORECASE)
    
    if match:
        metric = match.group(1).lower() if match.group(1) else 'max'
        field = match.group(2).lower()
        symbol = match.group(5).upper() if match.group(5) else 'BTC'
        currency_or_timeframe = match.group(6).lower() if match.group(6) else 'usd'
        
        if 'từ' in currency_or_timeframe and 'đến nay' in currency_or_timeframe:
            timeframe = currency_or_timeframe
            currency = 'usd'
        else:
            currency = currency_or_timeframe.replace('in ', '') if currency_or_timeframe.startswith('in ') else 'usd'
            timeframe = '2y'
        
        if metric in ['trung bình', 'average']:
            metric = 'avg'
        elif metric in ['tối đa', 'max', 'lớn nhất']:
            metric = 'max'
        if field in ['giá đóng cửa', 'giá close', 'price', 'giá']:
            field = 'close price'
        elif field == 'khối lượng':
            field = 'volume'
        
        return {
            'metric': metric,
            'field': field,
            'symbol': symbol,
            'currency': currency,
            'timeframe': timeframe
        }
    
    return {
        'metric': 'max',
        'field': 'close price',
        'symbol': 'BTC',
        'currency': 'USD',
        'timeframe': '2y'
    }

def generate_workflow_json(query):
    parsed = parse_query(query)
    random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    field = parsed['field'].replace('close price', 'close').replace('volume', 'volumeto')
    
    timeframe_mapping = {
        'từ 2022 đến nay': 365 * 3,
        'từ 2023 đến nay': 365 * 2,
        'từ 2024 đến nay': 365,
        '1y': 365,
        '2y': 365 * 2,
        '3y': 365 * 3
    }
    limit = timeframe_mapping.get(parsed['timeframe'], 365)
    
    workflow = {
        "name": f"crypto_workflow_{random_id}",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "GET",
                    "path": f"crypto/{random_id}",
                    "options": {},
                    "responseMode": "onReceived",
                    "authentication": "none"
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 300]
            },
            {
                "parameters": {
                    "url": f"https://min-api.cryptocompare.com/data/histoday?fsym={parsed['symbol']}&tsym={parsed['currency']}&limit={limit}&api_key={CRYPTOCOMPARE_API_KEY}",
                    "options": {}
                },
                "name": "CryptoCompare",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 1,
                "position": [300, 300]
            },
            {
                "parameters": {
                    "functionCode": f"""
const jsonData = items[0].json;
if (!jsonData || !jsonData.Data) {{
    throw new Error("No Data field in CryptoCompare response");
}}
const data = Array.isArray(jsonData.Data) ? jsonData.Data : jsonData.Data.Data;
if (!Array.isArray(data) || data.length === 0) {{
    throw new Error("No valid data array in CryptoCompare response");
}}
const values = data.map(item => item['{field}']);
if (!values.every(val => typeof val === 'number')) {{
    throw new Error("Invalid {field} prices in data");
}}
const result = '{parsed['metric']}' === "avg" ? values.reduce((a, b) => a + b, 0) / values.length : Math.max(...values);
return [{{ json: {{ result }} }}]];
"""
                },
                "name": "Calculate",
                "type": "n8n-nodes-base.function",
                "typeVersion": 1,
                "position": [500, 300]
            }
        ],
        "connections": {
            "Webhook": {
                "main": [[{ "node": "CryptoCompare", "type": "main", "index": 0 }]]
            },
            "CryptoCompare": {
                "main": [[{ "node": "Calculate", "type": "main", "index": 0 }]]
            }
        },
        "settings": {
            "timezone": "UTC",
            "saveDataErrorExecution": "all",
            "saveDataSuccessExecution": "all",
            "saveManualExecutions": True
        }
    }
    return workflow, random_id

def delete_old_workflows():
    headers = {
        'X-N8N-API-KEY': N8N_API_KEY,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(N8N_WORKFLOWS_URL, headers=headers, timeout=30)
        print(f"Phản hồi lấy danh sách workflows: {response.status_code} - {response.text[:1000]}")
        if response.status_code == 200:
            workflows = response.json().get('data', [])
            for workflow in workflows:
                if workflow.get('name').startswith('crypto_workflow_'):
                    response = requests.delete(f"{N8N_WORKFLOWS_URL}/{workflow['id']}", headers=headers, timeout=30)
                    print(f"Đã xóa workflow: {workflow['id']} - Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi xóa workflows cũ: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_query():
    query = request.form.get('query')
    print(f"Nhận được câu truy vấn: {query}")
    
    try:
        delete_old_workflows()  # Xóa workflows cũ
        workflow_json, random_id = generate_workflow_json(query)
        headers = {
            'X-N8N-API-KEY': N8N_API_KEY,
            'Content-Type': 'application/json'
        }
        
        # Create workflow
        print("Đang tạo workflow...")
        response = requests.post(N8N_WORKFLOWS_URL, headers=headers, json=workflow_json, timeout=30)
        print(f"Phản hồi tạo workflow: {response.status_code} - {response.text[:1000]}")
        if response.status_code != 200:
            return jsonify({'error': f'Không thể tạo workflow: {response.text[:1000]}'}), 500
        
        workflow_id = response.json().get('id')
        if not workflow_id:
            print("Lỗi: Không tìm thấy workflow_id")
            return jsonify({'error': 'Không tìm thấy workflow_id'}), 500
        print(f"Đã tạo workflow với ID: {workflow_id}")
        
        # Activate workflow
        print("Đang kích hoạt workflow...")
        try:
            response = requests.post(f"{N8N_WORKFLOWS_URL}/{workflow_id}/activate", headers=headers, timeout=30)
            print(f"Phản hồi kích hoạt workflow: {response.status_code} - {response.text[:1000]}")
            if response.status_code != 200:
                return jsonify({'error': f'Không thể kích hoạt workflow: {response.text[:1000]}'}), 500
        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi kích hoạt workflow: {str(e)}")
            return jsonify({'error': f'Lỗi khi kích hoạt workflow: {str(e)}'}), 500
        
        # Check activation status
        print("Đang kiểm tra trạng thái kích hoạt workflow...")
        activated = False
        for attempt in range(10):
            try:
                response = requests.get(f"{N8N_WORKFLOWS_URL}/{workflow_id}", headers=headers, timeout=30)
                print(f"Thử kiểm tra trạng thái lần {attempt + 1}: {response.status_code} - {response.text[:1000]}")
                if response.status_code == 200:
                    try:
                        response_json = response.json()
                        if response_json.get('active'):
                            print("Workflow đã được kích hoạt!")
                            activated = True
                            break
                    except ValueError as e:
                        print(f"Lỗi phân tích JSON trạng thái workflow lần {attempt + 1}: {str(e)}, Response: {response.text[:1000]}")
                        return jsonify({'error': f'Lỗi phân tích JSON trạng thái workflow: {response.text[:1000]}'}), 500
                else:
                    print(f"Trạng thái không phải 200: {response.status_code} - {response.text[:1000]}")
            except requests.exceptions.RequestException as e:
                print(f"Lỗi kiểm tra trạng thái lần {attempt + 1}: {str(e)}")
            time.sleep(5)
        
        if not activated:
            print("Lỗi: Workflow không thể kích hoạt sau 10 lần thử")
            return jsonify({'error': 'Workflow không thể kích hoạt sau 10 lần thử'}), 500
        
        # Wait for webhook registration
        print("Chờ 30 giây để webhook đăng ký...")
        time.sleep(30)
        
        # Try production webhook
        webhook_url = f"{N8N_BASE_URL}/webhook/crypto/{random_id}"
        print(f"Webhook URL: {webhook_url}")
        
        print(f"Đang gọi production webhook: {webhook_url}")
        response = None
        for attempt in range(5):
            try:
                response = requests.get(webhook_url, timeout=30)
                print(f"Thử gọi production webhook lần {attempt + 1}: {response.status_code} - {response.text[:1000]}")
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException as e:
                print(f"Lỗi gọi production webhook lần {attempt + 1}: {str(e)}")
            time.sleep(5)
        
        if response and response.status_code == 200:
            print("Đang xử lý phản hồi webhook...")
            try:
                result = response.json()[0]['json']['result']
                print(f"Kết quả: {result}")
                return jsonify({'result': result})
            except Exception as e:
                print(f"Lỗi xử lý response webhook: {str(e)}")
                return jsonify({'error': f'Lỗi xử lý response webhook: {str(e)}'}), 500
        
        # Try test webhook
        print("Production webhook fail, thử test webhook...")
        test_webhook_url = f"{N8N_BASE_URL}/webhook-test/crypto/{random_id}"
        response = None
        for attempt in range(5):
            try:
                response = requests.get(test_webhook_url, timeout=30)
                print(f"Thử gọi test webhook lần {attempt + 1}: {response.status_code} - {response.text[:1000]}")
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException as e:
                print(f"Lỗi gọi test webhook lần {attempt + 1}: {str(e)}")
            time.sleep(5)
        
        if response and response.status_code == 200:
            print("Đang xử lý phản hồi test webhook...")
            try:
                result = response.json()[0]['json']['result']
                print(f"Kết quả: {result}")
                return jsonify({'result': result})
            except Exception as e:
                print(f"Lỗi xử lý response test webhook: {str(e)}")
                return jsonify({'error': f'Lỗi xử lý response test webhook: {str(e)}'}), 500
        
        # Fallback to API run
        print("Webhook fail, thử chạy workflow qua API run...")
        run_url = f"{N8N_RUN_URL}/{workflow_id}/run"
        try:
            exec_response = requests.post(run_url, headers=headers, json={}, timeout=30)
            print(f"Phản hồi API run: {exec_response.status_code} - {exec_response.text[:1000]}")
            if exec_response.status_code != 200:
                return jsonify({'error': f'Không thể chạy workflow qua API: {exec_response.text[:1000]}'}), 500
        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi chạy API run: {str(e)}")
            return jsonify({'error': f'Lỗi khi chạy API run: {str(e)}'}), 500
        
        execution_id = exec_response.json().get('data', {}).get('executionId')
        if not execution_id:
            print("Lỗi: Không tìm thấy execution_id")
            return jsonify({'error': 'Không tìm thấy execution_id'}), 500
        
        # Poll execution result
        print(f"Đang poll execution ID: {execution_id}")
        for attempt in range(10):
            try:
                result_response = requests.get(f"{N8N_EXECUTIONS_URL}/{execution_id}", headers=headers, timeout=30)
                print(f"Thử kiểm tra execution lần {attempt + 1}: {result_response.status_code} - {result_response.text[:1000]}")
                if result_response.status_code == 200:
                    try:
                        exec_data = result_response.json().get('data', {})
                        if exec_data.get('finished'):
                            run_data = exec_data.get('resultData', {}).get('runData', {})
                            calculate_node = run_data.get('Calculate', [{}])[0].get('data', {}).get('main', [[]])[0]
                            if calculate_node:
                                result = calculate_node[0].get('json', {}).get('result')
                                print(f"Kết quả từ execution: {result}")
                                return jsonify({'result': result})
                            else:
                                print("Lỗi: Không tìm thấy kết quả từ node Calculate")
                                return jsonify({'error': 'Không tìm thấy kết quả từ node Calculate'}), 500
                    except ValueError as e:
                        print(f"Lỗi phân tích JSON execution lần {attempt + 1}: {str(e)}, Response: {result_response.text[:1000]}")
                        return jsonify({'error': f'Lỗi phân tích JSON execution: {result_response.text[:1000]}'}), 500
                time.sleep(5)
            except requests.exceptions.RequestException as e:
                print(f"Lỗi kiểm tra execution lần {attempt + 1}: {str(e)}")
        print("Lỗi: Không thể lấy kết quả execution sau 10 lần thử")
        return jsonify({'error': 'Không thể lấy kết quả execution sau 10 lần thử'}), 500
    
    except Exception as e:
        print(f"Lỗi trong submit_query: {str(e)}")
        return jsonify({'error': f'Lỗi server nội bộ: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)