import pandas as pd
import re
from flask import Flask, request, render_template
from datetime import datetime
from chrono_python import parse_date

app = Flask(__name__)

class CryptoQASystem:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file)
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.columns = self.df.columns.str.lower()
        
    def clean_query(self, query):
        return query.lower().strip()
    
    def parse_query(self, query):
        query = self.clean_query(query)
        
        # Từ khóa thống kê
        stats_keywords = {
            'tổng': 'sum',
            'trung bình': 'mean',
            'lớn nhất': 'max',
            'nhỏ nhất': 'min',
            'số lượng': 'count'
        }
        
        # Tìm cột được hỏi
        selected_column = None
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in query:
                selected_column = col
                break
                
        # Tìm phép tính
        operation = None
        for key, value in stats_keywords.items():
            if key in query:
                operation = value
                break
                
        # Tìm điều kiện lọc (coin hoặc date)
        condition = {}
        # Lọc theo coin
        coin_match = re.search(r'coin.*?(btc|xmr)', query, re.IGNORECASE)
        if coin_match:
            condition['coin'] = coin_match.group(1).upper()
            
        # Lọc theo ngày
        date_match = re.search(r'n(?:ơ|o)i\s+ng(?:à|a)y\s+(.+?)(?:\s+là|=|\s|$)', query, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(1).strip()
            parsed_date = parse_date(date_str)
            if parsed_date:
                condition['date'] = parsed_date.date()
                
        return selected_column, operation, condition
    
    def execute_query(self, query):
        column, operation, condition = self.parse_query(query)
        
        if not column:
            return "Không tìm thấy cột phù hợp (open, high, low, close, volume)."
            
        try:
            df_temp = self.df.copy()
            
            # Áp dụng điều kiện lọc
            if 'coin' in condition:
                df_temp = df_temp[df_temp['coin'].str.lower() == condition['coin'].lower()]
            if 'date' in condition:
                df_temp = df_temp[df_temp['date'].dt.date == condition['date']]
                
            if df_temp.empty:
                return "Không tìm thấy dữ liệu phù hợp với điều kiện."
                
            # Thực hiện phép tính
            if operation:
                if operation == 'sum':
                    result = df_temp[column].sum()
                elif operation == 'mean':
                    result = df_temp[column].mean()
                elif operation == 'max':
                    result = df_temp[column].max()
                elif operation == 'min':
                    result = df_temp[column].min()
                elif operation == 'count':
                    result = df_temp[column].count()
                return f"Kết quả {operation} của {column}: {result:.2f}"
            else:
                # Hiển thị tất cả giá trị
                result = df_temp[['date', 'coin', column]].to_dict('records')
                return "\n".join([f"{r['date'].strftime('%Y-%m-%d')} ({r['coin']}): {r[column]:.2f}" for r in result])
                
        except Exception as e:
            return f"Lỗi khi xử lý câu hỏi: {str(e)}"

# Khởi tạo hệ thống
qa_system = CryptoQASystem("coin_historical_2020_2025.csv")

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    query = None
    columns = ['open', 'high', 'low', 'close', 'volume']
    if request.method == "POST":
        query = request.form.get("query")
        if query:
            result = qa_system.execute_query(query)
    return render_template("index.html", columns=columns, result=result, query=query)

if __name__ == "__main__":
    app.run(debug=True)