from pyscript import window, document
from pyodide.ffi import create_proxy
import json
from datetime import datetime
import random

products = []
orders = []
deleted_products = []

current_modal_index = -1
current_modal_action = ""
current_return_order_id = "" 

def load_data():
    global products, orders, deleted_products
    
    # Đọc dữ liệu đơn hàng
    try:
        orders_data = window.localStorage.getItem('pyscript_orders_db')
        orders = json.loads(orders_data) if orders_data else []
    except Exception as e:
        print("Lỗi load đơn hàng:", e)
        orders = []
    
    # Đọc dữ liệu hàng hủy
    try:
        deleted_data = window.localStorage.getItem('pyscript_deleted_db')
        deleted_products = json.loads(deleted_data) if deleted_data else []
    except Exception as e:
        print("Lỗi load hàng hủy:", e)
        deleted_products = []
    
    # Đọc và chuyển đổi dữ liệu sản phẩm an toàn
    try:
        data = window.localStorage.getItem('pyscript_products_db')
        if data:
            raw_products = json.loads(data)
            products = []
            for p in raw_products:
                # Đảm bảo an toàn dữ liệu cũ, tự tạo 'cost' nếu thiếu
                if 'cost' not in p:
                    try:
                        p['cost'] = int(float(p.get('price', 0)) * 0.7)
                    except:
                        p['cost'] = 0
                products.append(p)
        else:
            # Khởi tạo nếu hoàn toàn trống
            products = [
                {"name": "Điện thoại iPhone 15 Pro Max 256GB", "cost": 21000000, "price": 29500000, "quantity": 14},
                {"name": "Máy tính bảng iPad Air 5 M1 Wifi", "cost": 10500000, "price": 14200000, "quantity": 8},
                {"name": "Laptop ASUS ROG Strix G16 Gaming", "cost": 26000000, "price": 34800000, "quantity": 5}
            ]
            save_products()
    except Exception as e:
        print("Lỗi load sản phẩm:", e)
        products = []

def save_products():
    window.localStorage.setItem('pyscript_products_db', json.dumps(products))

def save_orders():
    window.localStorage.setItem('pyscript_orders_db', json.dumps(orders))

def save_deleted():
    window.localStorage.setItem('pyscript_deleted_db', json.dumps(deleted_products))

def format_currency(v):
    try:
        return f"{int(float(v)):,}".replace(",", ".") + " đ"
    except:
        return "0 đ"



def render_tables():
    global products, orders
    
    # Tính toán số liệu tổng quan
    total_qty = sum(int(p.get('quantity', 0)) for p in products)
    total_types = len(products)
    revenue_bar = sum(float(o.get('value', 0)) for o in orders if o.get('status') in ['paid', 'kiemtuan'])
    
    # Cập nhật an toàn lên thanh Top Mini Bar (Không sợ thiếu ID)
    el_qty = document.getElementById("total-products-qty")
    if el_qty: el_qty.innerText = f"{total_qty} cái"
    
    el_count = document.getElementById("total-products-count")
    if el_count: el_count.innerText = f"{total_types} dòng"
    
    el_val = document.getElementById("total-products-value")
    if el_val: el_val.innerText = format_currency(revenue_bar)

    # Đổ dữ liệu bảng Mặt Hàng Web
    tbody = document.getElementById("product-tbody")
    if tbody:
        tbody.innerHTML = ""
        search_el = document.getElementById("search-input")
        search_q = search_el.value.lower() if search_el else ""
        
        for idx, p in enumerate(products):
            if search_q and search_q not in p.get('name', '').lower():
                continue
                
            tr = document.createElement("tr")
            tr.innerHTML = f"""
                <td style="font-weight: 500;">{p.get('name', 'Không tên')}</td>
                <td style="color: #f59e0b; font-weight:600;">{format_currency(p.get('cost', 0))}</td>
                <td style="color: #10b981; font-weight: 600;">{format_currency(p.get('price', 0))}</td>
                <td style="font-weight: 700;">{p.get('quantity', 0)} cái</td>
                <td>
                    <button class="action-btn" style="background-color: #10b981;" onclick="openQuantityModal({idx}, 'import')"><i class="fa-solid fa-square-plus"></i> Nhập</button>
                    <button class="action-btn" style="background-color: #3b82f6;" onclick="openQuantityModal({idx}, 'export')"><i class="fa-solid fa-cart-arrow-down"></i> Bán</button>
                    <button class="action-btn" style="background-color: #ef4444;" onclick="deleteProduct({idx})"><i class="fa-solid fa-trash-can"></i> Xóa</button>
                </td>
            """
            tbody.appendChild(tr)
            
    render_reports()



def render_orders_table():
    tbody = document.getElementById("orders-tbody")
    if not tbody: return
    tbody.innerHTML = ""
    
    # 1. Đọc giá trị từ cả 3 bộ lọc
    filter_el = document.getElementById("filter-status")
    status_filter = filter_el.value if filter_el else "all"
    
    category_el = document.getElementById("filter-category")
    category_filter = category_el.value.lower() if category_el else "all"
    
    search_el = document.getElementById("search-order")
    search_q = search_el.value.lower() if search_el else ""
    
    status_map = {
        "paid": {"text": "Đã thanh toán", "class": "badge-paid"},
        "kiemtuan": {"text": "Kiểm kho", "class": "badge-kiemtuan"},
        "return_pending": {"text": "Chờ duyệt hoàn tiền", "class": "badge-return"},
        "exchange_pending": {"text": "Chờ duyệt đổi hàng", "class": "badge-exchange"},
        "refunded": {"text": "Đã hoàn trả kho", "class": "badge-refunded"}
    }
    
    for o in reversed(orders):
        status_current = o.get('status', 'paid')
        order_detail = o.get('detail', '')
        
        # Kiểm tra Bộ lọc 1: Trạng thái đơn hàng
        if status_filter != "all" and status_current != status_filter:
            continue
            
        # Kiểm tra Bộ lọc 2: Danh mục nghiệp vụ (Chuẩn chữ thường để tìm chính xác)
        if category_filter != "all" and category_filter not in order_detail.lower():
            continue
            
        # Kiểm tra Bộ lọc 3: Ô tìm kiếm từ khóa
        if search_q and (search_q not in o.get('id', '').lower() and search_q not in order_detail.lower()):
            continue
            
        st = status_map.get(status_current, {"text": status_current, "class": ""})
        
        # TÌM ĐOẠN NÀY TRONG HÀM render_orders_table() VÀ THAY THẾ:
        action_html = ""
        if status_current in ['paid', 'kiemtuan']:
            # Xóa sạch thuộc tính style="..." cũ để nhường chỗ cho CSS custom hoạt động
            action_html = f"""
                <button class="action-btn cancel-btn" onclick="openCancelModal('{o['id']}')">
                    <i class="fa-solid fa-circle-xmark"></i> Hủy đơn
                </button>
                <button class="action-btn exchange-btn" onclick="openExchangeModal('{o['id']}')">
                    <i class="fa-solid fa-arrows-rotate"></i> Đổi trả
                </button>
            """
        elif status_current == 'return_pending':
            # Thay style="background-color:#10b981" bằng class "approve-btn" của bạn
            action_html = f"""
                <button class="action-btn approve-btn" onclick="approveRefund('{o['id']}')">
                    <i class="fa-solid fa-check"></i> Duyệt hoàn tiền
                </button>
            """
        elif status_current == 'exchange_pending':
            # Tương tự cho nút duyệt đổi trả
            action_html = f"""
                <button class="action-btn approve-btn" onclick="approveExchange('{o['id']}')">
                    <i class="fa-solid fa-check"></i> Duyệt đổi trả
                </button>
            """
        else:
            action_html = """<span style="color:#64748b; font-size:12px;">Đã đóng giao dịch</span>"""

        tr = document.createElement("tr")
        tr.innerHTML = f"""
            <td style="color: #64748b; font-size: 0.85rem;">{o.get('time', '')}</td>
            <td style="font-weight: 700; color: #1e293b;">{o.get('id', '')}</td>
            <td>{order_detail}</td>
            <td style="font-weight: 700; color: #1e293b;">{format_currency(o.get('value', 0))}</td>
            <td><span class="gcp-badge {st['class']}">{st['text']}</span></td>
            <td>{action_html}</td>
        """
        tbody.appendChild(tr)
    render_reports()

def render_deleted_table():
    tbody = document.getElementById("deleted-tbody")
    if not tbody: return
    tbody.innerHTML = ""
    for p in reversed(deleted_products):
        cost_val = float(p.get('cost', 0))
        qty_val = int(p.get('quantity', 0))
        loss_val = cost_val * qty_val
        
        tr = document.createElement("tr")
        tr.innerHTML = f"""
            <td style="font-weight:500;">{p.get('name', 'Không tên')}</td>
            <td>{format_currency(cost_val)}</td>
            <td style="color:#ef4444; font-weight:700;">{qty_val} cái</td>
            <td style="color:#ef4444; font-weight:700;">{format_currency(loss_val)}</td>
        """
        tbody.appendChild(tr)
    render_reports()

def render_reports():
    net_revenue = 0
    total_cost = 0
    
    for o in orders:
        if o.get('status') in ['paid', 'kiemtuan']:
            net_revenue += float(o.get('value', 0))
            total_cost += float(o.get('cost_total', float(o.get('value', 0)) * 0.7))
            
    total_loss = 0
    for dp in deleted_products:
        total_loss += float(dp.get('cost', 0)) * int(dp.get('quantity', 0))
        
    profit = net_revenue - total_cost
    
    # Đổ ra các thẻ tổng quan báo cáo an toàn
    el_rev = document.getElementById("rep-revenue")
    if el_rev: el_rev.innerText = format_currency(net_revenue)
    
    el_cst = document.getElementById("rep-cost")
    if el_cst: el_cst.innerText = format_currency(total_cost)
        
    profit_el = document.getElementById("rep-profit")
    if profit_el:
        profit_el.innerText = format_currency(profit)
        card_border = document.getElementById("profit-card-border")
        if profit >= 0:
            profit_el.style.color = "#3b82f6"
            if card_border: card_border.style.borderLeftColor = "#3b82f6"
        else:
            profit_el.style.color = "#ef4444"
            if card_border: card_border.style.borderLeftColor = "#ef4444"
            
    el_los = document.getElementById("rep-loss")
    if el_los: el_los.innerText = format_currency(total_loss)

    rep_tbody = document.getElementById("report-orders-tbody")
    if rep_tbody:
        count_paid = len([o for o in orders if o.get('status') == 'paid'])
        count_audit = len([o for o in orders if o.get('status') == 'kiemtuan'])
        count_pending = len([o for o in orders if o.get('status') in ['return_pending', 'exchange_pending']])
        count_refund = len([o for o in orders if o.get('status') == 'refunded'])
        
        val_paid = sum(float(o.get('value', 0)) for o in orders if o.get('status') == 'paid')
        val_audit = sum(float(o.get('value', 0)) for o in orders if o.get('status') == 'kiemtuan')
        val_pending = sum(float(o.get('value', 0)) for o in orders if o.get('status') in ['return_pending', 'exchange_pending'])
        val_refund = sum(float(o.get('value', 0)) for o in orders if o.get('status') == 'refunded')

        rep_tbody.innerHTML = f"""
            <tr>
              <td style="font-weight:600; color:#10b981;">Đơn Hoàn Tất (Đã thu tiền)</td>
              <td>{count_paid} đơn</td>
              <td style="font-weight:700; color:#10b981;">{format_currency(val_paid)}</td>
              <td>Hàng bán ra trực tiếp bình thường, dòng tiền an toàn.</td>
            </tr>
            <tr>
              <td style="font-weight:600; color:#6366f1;">Đơn Kiểm Kho (Tạm xuất)</td>
              <td>{count_audit} đơn</td>
              <td style="font-weight:700; color:#6366f1;">{format_currency(val_audit)}</td>
              <td>Hàng xuất đi kiểm kê nội bộ / đối tác, chưa chốt doanh số.</td>
            </tr>
            <tr>
              <td style="font-weight:600; color:#f59e0b;">Đơn Chờ Duyệt (Hủy/Đổi)</td>
              <td>{count_pending} đơn</td>
              <td style="font-weight:700; color:#f59e0b;">{format_currency(val_pending)}</td>
              <td>Đang trong trạng thái tranh chấp / chờ quản lý xử lý.</td>
            </tr>
            <tr>
              <td style="font-weight:600; color:#ef4444;">Đơn Hoàn Trả Kho (Thất thu)</td>
              <td>{count_refund} đơn</td>
              <td style="font-weight:700; color:#ef4444;">-{format_currency(val_refund)}</td>
              <td>Giao dịch thất bại, hàng thu hồi nhưng mất chi phí cơ hội.</td>
            </tr>
        """

def add_product(e):
    name = document.getElementById("product-name").value.strip()
    cost_str = document.getElementById("product-cost").value.strip()
    price_str = document.getElementById("product-price").value.strip()
    qty_str = document.getElementById("product-quantity").value.strip()
    
    if not name or not cost_str or not price_str or not qty_str:
        window.showModal("Vui lòng điền đầy đủ thông tin Tên, Giá Vốn, Giá Bán và Số Lượng!")
        return
        
    products.append({
        "name": name,
        "cost": int(cost_str),
        "price": int(price_str),
        "quantity": int(qty_str)
    })
    save_products()
    render_tables()
    
    document.getElementById("product-name").value = ""
    document.getElementById("product-cost").value = ""
    document.getElementById("product-price").value = ""
    document.getElementById("product-quantity").value = ""

def open_quantity_modal(index, action):
    global current_modal_index, current_modal_action
    current_modal_index = int(index)
    current_modal_action = action
    
    p = products[current_modal_index]
    title = f"Nhập Thêm Kho: {p.get('name', '')}" if action == "import" else f"Tạo Đơn Bán Xuất Kho: {p.get('name', '')}"
    confirm_btn_color = "#10b981" if action == "import" else "#3b82f6"
    
    document.getElementById("modal-title").innerText = title
    document.getElementById("modal-qty-input").value = ""
    document.getElementById("modal-confirm-btn").style.backgroundColor = confirm_btn_color
    document.getElementById("quantity-modal").classList.add("open")

def confirm_quantity_modal(e):
    global current_modal_index, current_modal_action
    qty_str = document.getElementById("modal-qty-input").value.strip()
    if not qty_str or int(qty_str) <= 0:
        window.showModal("Số lượng thao tác phải lớn hơn 0!")
        return
        
    qty = int(qty_str)
    p = products[current_modal_index]
    
    if current_modal_action == "import":
        p['quantity'] = int(p.get('quantity', 0)) + qty
        window.showModal(f"Đã nhập thêm {qty} cái vào kho thành công!")
    elif current_modal_action == "export":
        current_qty = int(p.get('quantity', 0))
        if qty > current_qty:
            window.showModal(f"Thất bại! Kho thực tế chỉ còn {current_qty} cái, không đủ để bán {qty} cái!")
            return
        p['quantity'] = current_qty - qty
        
        oid = f"DH{random.randint(100, 999)}"
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        val_total = float(p.get('price', 0)) * qty
        cost_total = float(p.get('cost', 0)) * qty
        
        orders.append({
            "id": oid,
            "time": now_str,
            "detail": f"Xuất bán hàng: {p.get('name', '')} (SL: {qty})",
            "value": val_total,
            "cost_total": cost_total,
            "status": "paid"
        })
        save_orders()
        render_orders_table()
        window.showModal(f"Đã xuất hóa đơn {oid} thành công!")
        
    save_products()
    render_tables()
    document.getElementById("quantity-modal").classList.remove("open")

# 1. Hàm này chứa logic xóa thực tế
def perform_delete_product(index):
    idx = int(index)
    p = products[idx]
    deleted_products.append(products.pop(idx))
    save_products()
    save_deleted()
    render_tables()
    render_deleted_table()

# 2. Hàm này gọi Modal lên
def delete_product(index):
    idx = int(index)
    p = products[idx]
    
    # Tạo một proxy cho logic xóa
    def callback():
        perform_delete_product(idx)
        
    # Gọi Modal thay cho confirm()
    window.showModal(
        f"Bạn chắc chắn muốn xóa mặt hàng '{p.get('name','')}'? Toàn bộ hàng tồn hiện tại sẽ đưa vào danh mục thất thoát!", 
        create_proxy(callback)
    )

# 🟩 HÃY SAO CHÉP VÀ DÁN ĐOẠN NÀY VÀO:

def open_cancel_modal(oid):
    global current_return_order_id
    current_return_order_id = oid
    document.getElementById("cancel-modal-oid").innerText = oid
    document.getElementById("cancel-reason-text").value = ""
    # Thêm dòng này để xóa thông báo lỗi đỏ của lần bấm trước đó đi khi vừa mở lên
    if document.getElementById("cancel-error-msg"):
        document.getElementById("cancel-error-msg").innerText = ""
    document.getElementById("modal-cancel-refund").classList.add("open")

def submit_cancel_request(e):
    global current_return_order_id
    reason = document.getElementById("cancel-reason-text").value.strip()
    
    # Không dùng window.alert nữa, mà chèn chữ đỏ trực tiếp vào modal công nghệ
    if not reason:
        if document.getElementById("cancel-error-msg"):
            document.getElementById("cancel-error-msg").innerText = "⚠ Vui lòng nhập lý do hủy đơn hàng!"
        return
        
    for o in orders:
        if o.get('id') == current_return_order_id:
            o['status'] = "return_pending"
            o['detail'] = f"{o.get('detail', '')} | Lý do hủy: {reason}"
            break
    save_orders()
    render_orders_table()
    document.getElementById("modal-cancel-refund").classList.remove("open")


def open_exchange_modal(oid):
    global current_return_order_id
    current_return_order_id = oid
    document.getElementById("exchange-modal-oid").innerText = oid
    document.getElementById("exchange-reason-text").value = ""
    # Thêm dòng này để dọn sạch lỗi cũ khi vừa mở lên
    if document.getElementById("exchange-error-msg"):
        document.getElementById("exchange-error-msg").innerText = ""
    document.getElementById("modal-exchange-product").classList.add("open")

def submit_exchange_request(e):
    global current_return_order_id
    reason = document.getElementById("exchange-reason-text").value.strip()
    
    # Không dùng window.alert nữa, mà chèn chữ đỏ trực tiếp vào modal công nghệ
    if not reason:
        if document.getElementById("exchange-error-msg"):
            document.getElementById("exchange-error-msg").innerText = "⚠ Vui lòng nhập lý do đổi hàng lỗi!"
        return
        
    for o in orders:
        if o.get('id') == current_return_order_id:
            o['status'] = "exchange_pending"
            o['detail'] = f"{o.get('detail', '')} | Lý do đổi: {reason}"
            break
    save_orders()
    render_orders_table()
    document.getElementById("modal-exchange-product").classList.remove("open")
# 1. Logic thực hiện hoàn tiền thực tế
def perform_approve_refund(order_id):
    # Tìm đơn hàng và cập nhật trạng thái của bạn ở đây
    # Ví dụ:
    for order in orders:
        if order.get('id') == order_id:
            order['status'] = 'Đã hoàn tiền'
            break
    save_orders() # Lưu dữ liệu
    render_orders_table() # Cập nhật bảng
    window.showNotification("Đã duyệt hoàn tiền thành công!") # Thông báo đẹp

# 2. Hàm gọi Modal xác nhận
def approve_refund(order_id):
    # Hàm trung gian để gọi logic khi bấm OK
    def callback():
        perform_approve_refund(order_id)
    
    # Gọi Modal thay cho confirm()
    window.showModal("Bạn chắc chắn muốn duyệt hoàn tiền cho đơn hàng này?", create_proxy(callback))

def approve_exchange(oid):
    if window.confirm(f"Phê duyệt ĐỔI TRẢ HÀNG cho đơn {oid}? Hệ thống sẽ ghi nhận chuyển đổi thành công."):
        for o in orders:
            if o.get('id') == oid:
                o['status'] = "paid"
                o['detail'] = f"{o.get('detail', '')} (Đã đổi xong)"
                break
        save_orders()
        render_orders_table()

def handle_search_product(e):
    render_tables()

def handle_search_order(e):
    render_orders_table()

def main():
    load_data()
    render_tables()
    render_orders_table()
    render_deleted_table()
    
    if document.getElementById("add-btn"): 
        document.getElementById("add-btn").addEventListener("click", create_proxy(add_product))
    if document.getElementById("search-input"): 
        document.getElementById("search-input").addEventListener("input", create_proxy(handle_search_product))
    if document.getElementById("search-order"): 
        document.getElementById("search-order").addEventListener("input", create_proxy(handle_search_order))
    if document.getElementById("modal-confirm-btn"): 
        document.getElementById("modal-confirm-btn").addEventListener("click", create_proxy(confirm_quantity_modal))
        
    # Gộp tất cả sự kiện lắng nghe bộ lọc vào đúng khu vực khởi tạo của main()
    if document.getElementById("filter-status"): 
        document.getElementById("filter-status").addEventListener("change", create_proxy(lambda e: render_orders_table()))
    if document.getElementById("filter-category"): 
        document.getElementById("filter-category").addEventListener("change", create_proxy(lambda e: render_orders_table()))
    
    if document.getElementById("cancel-submit-btn"): 
        document.getElementById("cancel-submit-btn").addEventListener("click", create_proxy(submit_cancel_request))
    if document.getElementById("exchange-submit-btn"): 
        document.getElementById("exchange-submit-btn").addEventListener("click", create_proxy(submit_exchange_request))

    window.openQuantityModal = create_proxy(open_quantity_modal)
    window.deleteProduct = create_proxy(delete_product)
    window.openCancelModal = create_proxy(open_cancel_modal)
    window.openExchangeModal = create_proxy(open_exchange_modal)
    window.approveRefund = create_proxy(approve_refund)
    window.approveExchange = create_proxy(approve_exchange)

main()


