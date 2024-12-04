from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import sqlite3, re 
from datetime import datetime

app = Flask(__name__)
CORS(app)#確保允許所有域名進行跨域請求
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

#SQL的位置
db_path = r"D:\day88byReact\backend\cafes.db"

#現在時間
currtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# db_path = r"D:\day88 Professional Portfolio Project\day88byReact\backend\cafes.db"

# 計算每個咖啡館綜合排名
def calculate_rank(row):
       # 確保需要計算的欄位為數字類型
    sockets = int(row[5]) if row[5] is not None else 0
    toilet = int(row[6]) if row[6] is not None else 0
    wifi = int(row[7]) if row[7] is not None else 0
    call = int(row[8]) if row[8] is not None else 0
    
    
     # 找出 row[9] 中的數字，如果找不到則使用 0
    seat_numbers = re.findall(r'\d+', row[9])
    seat_number = float(max(seat_numbers)) * 0.6 if seat_numbers else 0  # 如果沒找到數字，設置為 0
    
    if row[10] and row[10].strip() !='':
        cafe_price = float(row[10].replace('£',''))*-3.6 #有效價格
    else:
        cafe_price = 10 #沒有價格以高價扣分
        
    rank =( 
            sockets * 1.0 +  # has_socket
            toilet * 1.0 +   # has_toilet
            wifi * 1.0 +     # has_wifi
            call * -1.0 +    # can_take_call
            # row[5]*1.0 + #has_socket 
            # row[6]*1.0 + #has_toilet
            # row[7]*1.0 + #has_wifi
            # row[8]*-1.0 + #can_take_call
            seat_number + 
            cafe_price
            # 9/24 加入判斷如果找不到則使用0
            # float(max(re.findall(r'\d +',row[9])))*0.6 + #seat_number 
            # float(row[10].replace('£', ''))*-3.6  #coffe_prices
            )
    return rank

#函式:確保資料表中指定的欄位
def ensur_column_exists(db_path, table_name, column_name, column_type):
    with sqlite3.connect(db_path) as db_connection:
        cursor = db_connection.cursor()
        cursor.execute(f'PRAGMA table_info({table_name})')
        columns = [column[1] for column in cursor.fetchall()]
        print(f"ensur_column check_columns: {columns}")
        if column_name  not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            db_connection.commit()
            print(f"Added {column_name} column to {table_name}")



# 函式: 更新排名
def update_rank(db_path):
    with sqlite3.connect(db_path, timeout= 10) as db_connection: #連接資料庫
        
        #使用不設置row_factory，默認返回元組
        db_connection.row_factory = sqlite3.Row #使游標返回字典形式的行
        
        ensur_column_exists(db_path, 'cafe', 'rank', 'REAL') #檢查rank行是否存在
        
        cursor = db_connection.cursor() #想像為滑鼠點選資料庫的行為
        cursor.execute('SELECT * FROM cafe') #點選分頁表的概念
        cafes = cursor.fetchall()  #全選分頁表所有項目
        
        for cafe  in cafes:
            rank =  calculate_rank(cafe)
            cursor.execute('UPDATE cafe SET rank =? WHERE id = ?', (rank, cafe['id']))
            # cursor.execute('UPDATE cafe SET rank =? WHERE id = ?', (rank, cafe[0]))
        # db_connection.commit #確認執行
        db_connection.commit()
        
def make_bold(function):
    def wrapper_function(*args, **kwargs):
        return f"<b>{function(*args, **kwargs)}</b>"
    return wrapper_function

#獲得全部數據的function----------------------------------------------------------------
def get_all_cafes(db_path):
    with sqlite3.connect(db_path) as conn:
        cusor = conn.cursor()
        cusor.execute('SELECT * FROM cafe ORDER BY rank DESC')
        all_cafes = cusor.fetchall()
    return all_cafes

# 獲得前3名的function----------------------------------------------------------------
def get_top_cafes(db_path):
    #連接到SQLite
    #直接使用匯入db
    #獲取排名前3的咖啡館
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        # 獲取排名前3的咖啡館
        cursor.execute('SELECT * FROM cafe ORDER BY rank DESC LIMIT 3')
        top3_cafes = cursor.fetchall()
    return top3_cafes

@app.route('/api/top_cafes', methods=['GET', 'POST'])
def get_cafes():
    ensur_column_exists(db_path=db_path, table_name="cafe",column_name='rank', column_type='REAL')
    try:
        ensur_column_exists(db_path=db_path, table_name="cafe",column_name='additional_info', column_type='TEXT')
    except sqlite3.error as e:
        print(f"An error occurred: {e}")
    update_rank(db_path)
    cafes = get_top_cafes(db_path)
    return jsonify(cafes)

@app.route('/')
def home_page():
    top_cafes= get_top_cafes(r"D:\day88 Professional Portfolio Project\instance\cafes.db")
    # return render_template("index.html") #使用templete
    # return render_template("index.html", cafes=top_cafes)；
    # return "Hello World" 
# command line啟動 輸入 flask --app .\app.py run  參考: https://flask.palletsprojects.com/en/3.0.x/quickstart/


@app.route('/api/all_cafes', methods=['GET']) # 刪掉, 'POST'
def cafes():
    all_cafes = get_all_cafes(db_path)
    return jsonify(all_cafes)


#新增咖啡資料
@app.route('/api/add_cafe', methods=['POST']) #增加新咖啡資料
def add_cafe():
    # data = request.json 這個gpt提供的方法無法運作
    data = request.get_json()
    print(f"get new cafe: {data}")
    name = data.get('name', '')  # 使用 .get() 以防字段为空
    map_url = data.get('map_url', '')
    img_url = data.get('img_url', '')
    location = data.get('location', '')
     # 強制將 `sockets`、`toilet`、`wifi`、`call` 等欄位轉為整數
    sockets = int(data.get('sockets', 0))  # 默認為 0
    toilet = int(data.get('toilet', 0))
    wifi = int(data.get('wifi', 0))
    call = int(data.get('call', 0))
    seats = data.get('seats', '')
    coffee_price = data.get('coffee_price', '')
    additional_info = data.get('additional_information', '')  # 可以为空
    print(f"ADD第二次列印:{sockets, toilet, additional_info}")  # 檢查 additional_info 是否正常
    
    # 構建 row 結構來計算 rank
    row = [None, name, map_url, img_url, location, sockets, toilet, wifi, call, seats, coffee_price, None,  additional_info]

    #計算rank
    rank = calculate_rank(row)
    print("New coffee rank is {}".format(rank))
    
    # 插入新咖啡馆数据
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            sql ='''INSERT INTO cafe (name, map_url, img_url, location, has_sockets, has_toilet, has_wifi, can_take_calls, seats, coffee_price, rank, additional_info) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            val =(name, map_url, img_url, location, sockets, toilet, wifi, call, seats, coffee_price, rank, additional_info)
            print(f"插入的值: {val}")
            cursor.execute(sql, val)
            conn.commit()
            print(f"add newe cafe commit succeeded at {currtime}")
        
        return jsonify({"message": "New cafe added successfully!"})
    
    except sqlite3.Error as e:
        return jsonify({"error": f"Failed to add cafe: {str(e)}"}), 500

    

#更新資料
@app.route('/api/update_cafe/<string:name>', methods=['PUT'])
def update_cafe(name):
    # data = request.json 這個gpt提供的方法無法運作
    data = request.get_json()
    print(f"update cafe: {data}")
    updat_name = data.get('name', '')  # 使用 .get() 以防字段为空
    map_url = data.get('map_url', '')
    img_url = data.get('img_url', '')
    location = data.get('location', '')
   # 強制將 `sockets`、`toilet`、`wifi`、`call` 等欄位轉為整數
    sockets = int(data.get('sockets', 0))  # 默認為 0
    toilet = int(data.get('toilet', 0))
    wifi = int(data.get('wifi', 0))
    call = int(data.get('call', 0))
    seats = data.get('seats', '')
    coffee_price = data.get('coffee_price', '')
    rank = data.get('rank',0)
    additional_info = data.get('additional_information', '')  # 可以为空
    print(f"第二次列印:{sockets, toilet}")
    
    # 取 row 結構來計算 rank
    row = [None, updat_name, map_url, img_url, location, sockets, toilet, wifi, call, seats, coffee_price, rank, additional_info]
    
    #重算rank
    rank =calculate_rank(row)
    print("Updated coffee rank is {}".format(rank))
    
    # 更新現有咖啡館數據
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # maxid = cursor.execute('''SELECT MAX(id) FROM cafe'''
            
            cursor.execute(
                '''UPDATE cafe
                SET name = ?,  map_url = ?, img_url = ?, location = ?, has_sockets = ?, has_toilet = ?, has_wifi = ?, can_take_calls = ?, seats = ?, coffee_price = ?, rank = ?, additional_info = ?
                WHERE name = ?
                '''
                ,(updat_name, map_url, img_url, location, sockets, toilet, wifi, call, seats, coffee_price, rank, additional_info, name))
            conn.commit() #確認
        
        return jsonify({"message":f"Cafe '{name}' updated successfully"})
    
    except sqlite3.Error as e:
         return jsonify({"error": f"Failed to update cafe: {str(e)}"}), 500


@app.route('/api/delete_cafe_by_name/<string:name>', methods=['DELETE'])
def delete_cafe(name):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
        
        cursor.execute(
            '''
            DELETE FROM cafe WHERE name =?
            '''
            ,(name, ))
        conn.commit() #確認
        if cursor.rowcount == 0:
                return jsonify({"error": f"No cafe found with name {name}"}),404
        return jsonify({"message": "Cafe deleted successfully"}), 200

    except sqlite3.Error as e:
        return jsonify({"error": f"Failed to delete cafe: {str(e)}"}), 500
    


@app.route("/bye/", defaults={'name': ''})
@app.route("/bye/<path:name>")
@make_bold
def bye(name):
    if name:
        return f"Bye! {name}"
    else:
        return "Bye!!"

# import requests

# requests.get("http://www.google.com")

#1. 伺服器端建立FLASK 參考day100_420


#/11/06增加
@app.route('/api/cafe/<int:id>', methods=['GET'])
def get_cafe_detail(id):
    # all_cafes = get_all_cafes(db_path)
    # return jsonify(all_cafes[id])
    
    # try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cafe WHERE id = ?", (id,))
            print(f"ID:{id}")
            cafe = cursor.fetchone()
        return jsonify(cafe)


# 11/15 加入cafe_table的功能
@app.route('/api/cafe_table', methods=['GET'])
def cafe_table():
    with sqlite3.connect(db_path) as conn:
        cafes = conn.execute("SELECT id, name, location, has_sockets, has_toilet, can_take_calls, has_wifi, seats,  coffee_price, rank, additional_info  FROM cafe").fetchall()
        
    # HTML 表格模板
    table_html = """

        <table border="1" cellpadding="10">
            <thead>
                <tr>
                    {% for col in ["ID", "Name", "Location","Socket", "Toilet", "Take calls", "Wifi", "Seats", "Price", "Rank", "Additional information"] %}
                        <th>{{ col }}</th>
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for cafe in cafes %}
                <tr>
                    <td>{{ cafe[0] }}</td> <!-- ID -->
                    <td>{{ cafe[1] }}</td> <!-- Name -->
                    <td>{{ cafe[2] }}</td> <!-- Location -->
                    <td>{{ "Yes" if cafe[3] == 1 else "No" }}</td> <!-- Socket -->
                    <td>{{ "Yes" if cafe[4] == 1 else "No" }}</td> <!-- Toilet -->
                    <td>{{ "Yes" if cafe[5] == 1 else "No" }}</td> <!-- Take calls -->
                    <td>{{ "Yes" if cafe[6] == 1 else "No" }}</td> <!-- Wifi -->
                    <td>{{ cafe[7] }}</td> <!-- Seats -->
                    <td>{{ cafe[8] }}</td> <!-- Price -->
                    <td>{{ cafe[9] }}</td> <!-- Rank -->
                    <td>{{ cafe[10] }}</td> <!-- Addtitional info -->
                </tr>
                {% endfor %}
            </tbody>
        </table>


    """
    return render_template_string(table_html, cafes=cafes)

# #11/17 用React渲染 table資料
# 要實現類似 Excel 的篩選表格，建議結合前端框架如 React 和 UI 庫（如 Material-UI 或 Ant Design）來實現。以下是完整的後端與前端實現過程：
# 後端：支持篩選功能的 API
# 後端提供一個通用的篩選 API，支持通過查詢參數傳遞篩選條件。
@app.route('/api/cafe_tablefilter', methods = ['GET'])
def cafe_tablefilter():
    #獲取查詢參數
    filter ={
        'name': request.args.get('name', '').lower(),  # 名稱關鍵字
        'location': request.args.get('location', ''),  # 位置
        'socket': request.args.get('socket', ''), 
        'toilet': request.args.get('toilet', ''),
        'call': request.args.get('call', ''),           
        'wifi': request.args.get('wifi', ''),# Wifi 篩選條件
        'seat': request.args.get('seat', ''),
        'price': request.args.get('price', ''),
        'rank': request.args.get('rank', ''),
    }
    
    query = """
        SELECT
            id, name, location, has_sockets, has_toilet, can_take_calls, has_wifi, seats,  coffee_price, rank
        FROM 
            cafe
        WHERE 
            1 = 1
    """
    params  = []
    
    #依序篩選
    # 名稱篩選
    if filter['name'] != '':
        query += " AND LOWER(name) LIKE?"
        params.append('%'+filter['name']+'%')
    
    # 位置篩選
    if filter['location'] != '':
        query += " AND location LIKE?"
        params.append('%'+filter['location']+'%')
    
    # Socket 篩選
    if filter['socket']!= '':
        socket_value = 1 if filter['socket'].lower() =="yes" else 0
        query += " AND has_sockets =?"
        params.append(filter['socket_value'])
    
    # Toilet 篩選
    if filter['toilet']!= '':
        toilet_value = 1 if filter['toilet'].lower() =="yes" else 0
        query += " AND has_toilet =?"
        params.append(filter['toilet_value'])
    
    # Call 篩選
    if filter['call']!= '':
        can_take_calls_value = 1 if filter['call'].lower() =="yes" else 0
        query += " AND can_take_calls =?"
        params.append(filter['can_take_calls_value'])

    
    # Wifi 篩選
    if filter['wifi']!= '':
        wifi_value = 1 if filter['wifi'].lower() == "yes" else 0
        query += " AND has_wifi = ?"
        params.append(wifi_value)
        
    # seat 篩選
    if filter['seat']!= '':
        query += " AND seat LIKE?"
        params.append('%'+filter['seat']+'%')
        
    # price 篩選
    if filter['price']!= '':
        query += " AND price LIKE?"
        params.append('%'+filter['price']+'%')
        
    # rank 篩選
    if filter['rank']!= '':
        query += " AND rank LIKE?"
        params.append('%'+filter['rank']+'%')
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        cafes = cursor.fetchall()
    #     cafes = conn.execute("SELECT id, name, location, has_sockets, has_toilet, can_take_calls, has_wifi, seats,  coffee_price, rank, additional_info  FROM cafe").fetchall()
        
    return jsonify(cafes)


if __name__ == "__main__":    
    app.run(debug=True)
    
