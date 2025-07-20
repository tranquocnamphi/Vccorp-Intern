# Hệ thống Hỏi Đáp Giá Tiền Điện Tử

Dự án này là một hệ thống hỏi đáp dựa trên web, được xây dựng bằng Flask và Pandas, để truy vấn dữ liệu giá lịch sử của tiền điện tử (BTC và XMR) từ tập dữ liệu `coin_historical_2020_2025.csv`. Người dùng có thể đặt câu hỏi về các chỉ số giá (open, high, low, close, volume) với các bộ lọc tùy chọn theo đồng coin hoặc ngày, và hệ thống trả về kết quả qua giao diện web.

## Tính năng
- **Câu hỏi bằng ngôn ngữ tự nhiên**: Hỗ trợ câu hỏi bằng tiếng Việt cho các phép tính thống kê (tổng, trung bình, lớn nhất, nhỏ nhất, số lượng) trên các chỉ số giá.
- **Lọc linh hoạt**: Lọc theo đồng coin (BTC, XMR) hoặc ngày (ví dụ: "2020-07-21" hoặc ngôn ngữ tự nhiên như "ngày 21 tháng 7 năm 2020").
- **Giao diện web**: Giao diện thân thiện, hiển thị các cột dữ liệu, đồng coin được hỗ trợ, ví dụ câu hỏi và kết quả (bao gồm câu hỏi người dùng đã nhập).
- **Xử lý lỗi**: Xử lý các câu hỏi không hợp lệ hoặc dữ liệu không tồn tại với thông báo lỗi rõ ràng.

## Cấu trúc dự án
```
crypto_qa_system/
├── app.py
├── coin_historical_2020_2025.csv
├── templates/
│   └── index.html
└── README.md
```

- `app.py`: File chính chứa logic ứng dụng Flask và xử lý câu hỏi.
- `coin_historical_2020_2025.csv`: Tập dữ liệu chứa giá lịch sử của BTC và XMR.
- `templates/index.html`: Mẫu HTML cho giao diện web.
- `README.md`: File này.

## Yêu cầu
- Python 3.6 trở lên
- Thư viện: `flask`, `pandas`, `chrono-python`

## Cài đặt
1. **Sao chép hoặc tạo dự án**:
   - Tạo cấu trúc thư mục như trên hoặc sao chép từ kho lưu trữ (nếu có).
2. **Cài đặt các thư viện**:
   ```bash
   pip install flask pandas chrono-python
   ```
3. **Đảm bảo tập dữ liệu**:
   - Đặt file `coin_historical_2020_2025.csv` trong cùng thư mục với `app.py`.
   - File CSV cần có các cột: `date`, `coin`, `open`, `high`, `low`, `close`, `volume`.

## Hướng dẫn sử dụng
1. **Chạy ứng dụng**:
   ```bash
   python app.py
   ```
   Lệnh này khởi động máy chủ Flask tại `http://127.0.0.1:5000`.

2. **Truy cập giao diện web**:
   - Mở trình duyệt và truy cập `http://127.0.0.1:5000`.
   - Nhập câu hỏi vào ô nhập liệu và nhấn "Gửi".

3. **Ví dụ câu hỏi**:
   - "Tổng volume của coin BTC" (Tổng khối lượng giao dịch của BTC)
   - "Giá close lớn nhất nơi coin là XMR" (Giá đóng cửa cao nhất của XMR)
   - "Giá open nơi ngày là 2020-07-21" (Giá mở cửa vào ngày 21/07/2020)
   - "Trung bình close của coin BTC nơi ngày là 2021-01-01" (Giá đóng cửa trung bình của BTC vào ngày 01/01/2021)

4. **Xem kết quả**:
   - Kết quả hiển thị bên dưới ô nhập liệu, bao gồm câu hỏi đã nhập và câu trả lời.

## Ví dụ kết quả
Cho câu hỏi "Tổng volume của coin BTC":
```
Câu hỏi: Tổng volume của coin BTC
Kết quả sum của volume: 123456789.00
```

## Lưu ý
- **Xử lý ngày tháng**: Hệ thống sử dụng `chrono-python` để phân tích ngày tháng theo ngôn ngữ tự nhiên (ví dụ: "ngày 21 tháng 7 năm 2020"). Ngoài ra, bạn có thể dùng định dạng `YYYY-MM-DD` để chỉ định ngày chính xác.
- **Tập dữ liệu**: Đảm bảo file `coin_historical_2020_2025.csv` được định dạng đúng và nằm trong thư mục dự án.
- **Cải tiến**: Để thêm biểu đồ trực quan (ví dụ: biểu đồ giá), có thể tích hợp Chart.js hoặc Recharts. Liên hệ nhà phát triển để được hỗ trợ.

## Khắc phục sự cố
- **Lỗi ModuleNotFoundError**: Đảm bảo tất cả thư viện được cài đặt trong môi trường Python đúng. Kiểm tra bằng `pip list`.
- **Lỗi File Not Found**: Kiểm tra file `coin_historical_2020_2025.csv` có trong thư mục chứa `app.py`.
- **Xung đột cổng**: Nếu `http://127.0.0.1:5000` không hoạt động, dừng các ứng dụng Flask khác hoặc đổi cổng trong `app.py` (ví dụ: `app.run(debug=True, port=5001)`).

## Cải tiến trong tương lai
- Thêm biểu đồ trực quan (ví dụ: biểu đồ đường cho xu hướng giá).
- Hỗ trợ câu hỏi phức tạp hơn (ví dụ: khoảng thời gian, nhiều điều kiện).
- Xuất kết quả ra file CSV hoặc PDF.

## Giấy phép
Dự án này phục vụ mục đích học tập và sử dụng tập dữ liệu mẫu. Đảm bảo bạn có quyền sử dụng dữ liệu trong `coin_historical_2020_2025.csv`.