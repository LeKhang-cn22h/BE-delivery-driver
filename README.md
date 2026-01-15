# BE-delivery-driver
The application will be used by managers and administrators to monitor and manage information, as well as the status of routes for users and employees. Additionally, it will connect to the supporting databases responsible for the backend, facilitating the frontend operations.
Muốn tạo ra service mới thì 
- mở terminal chạy pip install cookiecutter    
- trỏ cd tới thư mục BE-delivery-driver/backend/services rồi chạy lệnh sau
cookiecutter ..\..\templates\microservice-template
- sau đó điền theo yêu cầu
  [1/3] service_name (receive_orders): (tên service muốn tạo)
  [2/3] port (8001): (port cho service chạy)
  [3/3] description (Receive orders): (mô tả service này có chức năng gì)
lưu ý: Chạy service nào thì tạo venv tại service đó.
