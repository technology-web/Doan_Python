from pyscript import window, document
from pyodide.ffi import create_proxy
import json

# Mảng lưu trữ danh sách sản phẩm và đơn hàng
products = []
orders = []
deleted_products = []

# Biến toàn cục tạm thời lưu lại sản phẩm nào đang được chọn thao tác trong Modal
current_modal_index = -1
current_modal_action = "" # "sell" hoặc "delete"

def load_data():
    """Tải dữ liệu từ bộ nhớ cục bộ của trình duyệt"""
    global products, orders, deleted_products
    
    orders_data = window.localStorage.getItem('pyscript_orders_db')
    if orders_data:
        orders = json.loads(orders_data)
    else:
        orders = []

    deleted_data = window.localStorage.getItem('pyscript_deleted_db')
    if deleted_data:
        deleted_products = json.loads(deleted_data)
    else:
        deleted_products = []
    
    data = window.localStorage.getItem('pyscript_products_db')
    if data:
        products = json.loads(data)
    else:
        products = [
            {"name": "Laptop Gaming ASUS ROG", "price": 35000000, "quantity": 5},
            {"name": "Bàn phím cơ Keychron Q1", "price": 4500000, "quantity": 12},
            {"name": "Chuột Logitech G Pro X", "price": 2800000, "quantity": 8}
        ]
        save_data()

def save_data():
    """Lưu trữ dữ liệu vào localStorage"""
    window.localStorage.setItem('pyscript_products_db', json.dumps(products))
    window.localStorage.setItem('pyscript_orders_db', json.dumps(orders))
    window.localStorage.setItem('pyscript_deleted_db', json.dumps(deleted_products))

def format_currency(value):
    """Định dạng số thành tiền tệ VNĐ"""
    return "{:,.0f} đ".format(value).replace(",", ".")

def handle_search_product(event):
    """Hàm trung gian xử lý tìm kiếm sản phẩm kho hàng"""
    render_table()

def handle_search_order(event):
    """Hàm trung gian xử lý tìm kiếm đơn hàng"""
    render_orders_table()

def render_table():
    """Hiển thị dữ liệu ra bảng HTML"""
    tbody = document.getElementById("product-tbody")
    if not tbody:
        return
    tbody.innerHTML = ""
    
    search_input = document.getElementById("search-input")
    query = search_input.value.strip().lower() if search_input else ""
    
    total_count = 0
    total_value = 0
    
    for i, p in enumerate(products):
        if query and query not in p['name'].lower():
            continue
            
        tr = document.createElement("tr")
        subtotal = float(p['price']) * int(p['quantity'])
        total_count += int(p['quantity'])
        total_value += subtotal
        
        cols_data = [
            str(i + 1),
            p['name'],
            format_currency(float(p['price'])),
            str(p['quantity']),
            format_currency(subtotal)
        ]
        
        for idx, text in enumerate(cols_data):
            td = document.createElement("td")
            td.textContent = text
            if idx == 4:
                td.className = "highlight-text"
            tr.appendChild(td)
            
        td_action = document.createElement("td")
        action_div = document.createElement("div")
        action_div.className = "action-buttons"
        
        # Nút Bán
        sell_btn = document.createElement("button")
        sell_btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path><line x1="3" y1="6" x2="21" y2="6"></line><path d="M16 10a4 4 0 0 1-8 0"></path></svg> Bán'
        sell_btn.className = "sell-btn"
        if p['quantity'] <= 0:
            sell_btn.disabled = True
            
        def make_sell_handler(index):
            def handler(event):
                sell_product(index)
            return create_proxy(handler)
            
        sell_btn.addEventListener("click", make_sell_handler(i))
        
        # Nút Kiểm kê
        edit_btn = document.createElement("button")
        edit_btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg> Kiểm kê'
        edit_btn.className = "edit-btn"
        
        def make_edit_handler(index):
            def handler(event):
                edit_product(index)
            return create_proxy(handler)
            
        edit_btn.addEventListener("click", make_edit_handler(i))
        
        # Nút Xóa
        del_btn = document.createElement("button")
        del_btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg> Xóa'
        del_btn.className = "delete-btn"
        
        def make_delete_handler(index):
            def handler(event):
                delete_product(index)
            return create_proxy(handler)
            
        del_btn.addEventListener("click", make_delete_handler(i))
        
        action_div.appendChild(sell_btn)
        action_div.appendChild(edit_btn)
        action_div.appendChild(del_btn)
        td_action.appendChild(action_div)
        tr.appendChild(td_action)
        tbody.appendChild(tr)
        
    document.getElementById("total-count").textContent = str(total_count)
    document.getElementById("total-value").textContent = format_currency(total_value)
    
    total_revenue = sum(o['total'] for o in orders if o['id'].startswith('DH'))
    rev_element = document.getElementById("total-revenue")
    if rev_element:
        rev_element.textContent = format_currency(total_revenue)

def edit_product(index):
    """Sửa số lượng thực tế (Kiểm kê)"""
    p = products[index]
    old_qty = p['quantity']
    
    new_qty_str = window.prompt(f"Kiểm kê: Nhập số lượng thực tế của '{p['name']}' trong kho:", str(old_qty))
    if new_qty_str is not None:
        try:
            new_qty = int(new_qty_str.strip())
            if new_qty < 0:
                window.alert("⚠ Số lượng không thể nhỏ hơn 0!")
                return
                
            diff = new_qty - old_qty
            if diff != 0:
                p['quantity'] = new_qty
                note = "[Dư]" if diff > 0 else "[Thiếu]"
                orders.append({
                    "id": f"KK{len(orders)+1:03d}",
                    "name": f"{note} {p['name']}",
                    "quantity": abs(diff),
                    "price": 0,
                    "total": 0
                })
                save_data()
                render_table()
                render_orders_table()
                render_reports()
        except ValueError:
            window.alert("⚠ Vui lòng nhập một số hợp lệ!")

def show_quantity_modal(index, action):
    """Mở hộp thoại tùy chỉnh và cấu hình nội dung tương ứng với hành động Bán/Xóa"""
    global current_modal_index, current_modal_action
    current_modal_index = index
    current_modal_action = action
    
    p = products[index]
    
    modal_title = document.getElementById("modal-title")
    confirm_btn = document.getElementById("modal-confirm-btn")
    
    if action == "sell":
        modal_title.textContent = "📦 Xác Nhận Bán Hàng"
        confirm_btn.textContent = "Bán Ngay"
        confirm_btn.className = "primary-btn"
        confirm_btn.style.background = "var(--accent)"
    else:
        modal_title.textContent = "🗑 Xóa Sản Phẩm Khỏi Kho"
        confirm_btn.textContent = "Xóa Ngay"
        confirm_btn.className = "primary-btn"
        confirm_btn.style.background = "var(--danger)"

    document.getElementById("modal-p-name").textContent = p['name']
    document.getElementById("modal-p-stock").textContent = str(p['quantity'])
    
    input_field = document.getElementById("modal-quantity-input")
    input_field.value = str(p['quantity']) if action == "delete" else "1"
    
    confirm_btn.onclick = create_proxy(handle_modal_confirm)
    document.getElementById("quantity-modal").classList.add("open")

def handle_modal_confirm(event):
    """Xử lý sự kiện khi người dùng bấm nút Xác Nhận trên giao diện Modal mới"""
    global current_modal_index, current_modal_action
    if current_modal_index == -1:
        return
        
    p = products[current_modal_index]
    input_field = document.getElementById("modal-quantity-input")
    user_input = input_field.value.strip()
    
    try:
        qty = int(user_input)
        if qty <= 0:
            window.alert("⚠ Số lượng phải lớn hơn 0!")
            return
    except ValueError:
        window.alert("⚠ Vui lòng nhập số lượng hợp lệ!")
        return

    if current_modal_action == "sell":
        if qty > p['quantity']:
            window.alert(f"⚠ Không đủ hàng! Kho chỉ còn {p['quantity']} sản phẩm.")
            return
            
        order_total = qty * float(p['price'])
        orders.append({
            "id": f"DH{len(orders)+1:03d}",
            "name": p['name'],
            "quantity": qty,
            "price": float(p['price']),
            "total": order_total
        })
        p['quantity'] -= qty

    elif current_modal_action == "delete":
        if qty >= p['quantity']:
            deleted_products.append({
                "name": p["name"],
                "price": p["price"],
                "quantity": p["quantity"]
            })
            products.pop(current_modal_index)
        else:
            deleted_products.append({
                "name": p["name"],
                "price": p["price"],
                "quantity": qty
            })
            p["quantity"] -= qty

    save_data()
    document.getElementById("quantity-modal").classList.remove("open")
    render_table()
    render_orders_table()
    render_deleted_table()
    render_reports()

def sell_product(index):
    show_quantity_modal(index, "sell")

def delete_product(index):
    show_quantity_modal(index, "delete")

def render_orders_table():
    """Hiển thị lịch sử đơn hàng"""
    tbody = document.getElementById("order-tbody")
    if not tbody:
        return
    tbody.innerHTML = ""
    
    search_order = document.getElementById("search-order")
    query = search_order.value.strip().lower() if search_order else ""
    
    for o in reversed(orders):
        if query and (query not in o['id'].lower() and query not in o['name'].lower()):
            continue
            
        tr = document.createElement("tr")
        cols_data = [
            o['id'],
            o['name'],
            str(o['quantity']),
            format_currency(o['price']),
            format_currency(o['total'])
        ]
        
        for idx, text in enumerate(cols_data):
            td = document.createElement("td")
            td.textContent = text
            if idx == 4:
                td.className = "highlight-text"
            tr.appendChild(td)
        tbody.appendChild(tr)

def add_product(event):
    """Xử lý thêm sản phẩm"""
    name_input = document.getElementById("product-name")
    price_input = document.getElementById("product-price")
    qty_input = document.getElementById("product-quantity")
    error_msg = document.getElementById("error-message")
    
    name = name_input.value.strip()
    price_str = price_input.value.strip()
    qty_str = qty_input.value.strip()
    
    if not name or not price_str or not qty_str:
        error_msg.textContent = "⚠ Vui lòng điền đầy đủ thông tin!"
        return
        
    try:
        price_val = float(price_str)
        qty_val = int(qty_str)
        if price_val < 0 or qty_val < 0:
            error_msg.textContent = "⚠ Giá và số lượng phải lớn hơn hoặc bằng 0!"
            return
    except ValueError:
        error_msg.textContent = "⚠ Giá và số lượng phải là một số hợp lệ!"
        return
        
    error_msg.textContent = ""
    products.append({
        "name": name,
        "price": price_val,
        "quantity": qty_val
    })
    
    name_input.value = ""
    price_input.value = ""
    qty_input.value = ""
    
    save_data()
    render_table()

def render_reports():
    """Bảng báo cáo doanh số"""
    tbody = document.getElementById("report-tbody")
    if not tbody:
        return
    tbody.innerHTML = ""
    
    stats = {}
    for o in orders:
        if o['id'].startswith('DH'):
            name = o['name']
            if name not in stats:
                stats[name] = {"sold": 0, "revenue": 0, "adjustments": 0}
            stats[name]["sold"] += o['quantity']
            stats[name]["revenue"] += o['total']
        elif o['id'].startswith('KK'):
            parts = o['name'].split("] ")
            name = parts[1] if len(parts) > 1 else o['name']
            if name not in stats:
                stats[name] = {"sold": 0, "revenue": 0, "adjustments": 0}
            stats[name]["adjustments"] += 1
            
    for name, data in stats.items():
        tr = document.createElement("tr")
        cols_data = [
            name,
            str(data["sold"]),
            format_currency(data["revenue"]),
            str(data["adjustments"])
        ]
        for idx, text in enumerate(cols_data):
            td = document.createElement("td")
            td.textContent = text
            if idx == 2:
                td.className = "highlight-text"
            tr.appendChild(td)
        tbody.appendChild(tr)

def render_deleted_table():
    """Bảng sản phẩm đã xóa"""
    tbody = document.getElementById("deleted-tbody")
    if not tbody:
        return
    tbody.innerHTML = ""

    for p in reversed(deleted_products):
        tr = document.createElement("tr")
        data = [
            p["name"],
            format_currency(p["price"]),
            str(p["quantity"])
        ]
        for text in data:
            td = document.createElement("td")
            td.textContent = text
            tr.appendChild(td)
        tbody.appendChild(tr)

def main():
    load_data()
    render_table()
    render_orders_table()
    render_reports()
    render_deleted_table()
    
    # Gắn sự kiện thêm sản phẩm một lần duy nhất
    add_btn = document.getElementById("add-btn")
    if add_btn:
        add_btn.addEventListener("click", create_proxy(add_product))
    
    # Lắng nghe sự kiện tìm kiếm tối ưu
    search_input = document.getElementById("search-input")
    if search_input:
        search_input.addEventListener("input", create_proxy(handle_search_product))
        
    search_order = document.getElementById("search-order")
    if search_order:
        search_order.addEventListener("input", create_proxy(handle_search_order))

main()