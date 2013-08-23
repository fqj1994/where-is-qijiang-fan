where-is-qijiang-fan
====================

The implementation of "Where is Qijiang Fan" ( https://where.fqj.me/ )

# 這是什麼

這是一個 Web + Android 的應用。當用戶訪問此 Web 時，會發送 GCM 推送信息到 Android 應用， Android 應用收到後定位並反饋給 Web 應用。Web 應用對反饋的位置進行一些偏移變換後以地圖形式展現給網站訪問者。

# 使用許可

對該倉庫中代碼的使用需遵循 Apache License 2.0

# 演示

https://where.fqj.me/

# 如何使用

首先你需要去申請 Google 的 Key，名義上 GCM 和 Maps 是可以用同一個 Key 的，但是見於 Maps 的 Key 會漏出去，所以可以申請兩個不同的 Key。

## 服務端的配置

首先將config.sample.py複製到config.py

然後，進行設置，GCM_API_KEY 和 MAPS_BROWSER_KEY 是那兩個 key

UPDATE_PASSWORD 是更新位置和Registration ID 時需要的 Password

WEB_TITLE 就是你的頁面標題

LOCATION_FLOAT_PASSWORD 是設置位置偏移密碼，位置會根據你的偏移密碼和系統當前時間來進行偏移，同時將精度的圈畫大，來避免泄漏準確位置。

ACCURATE_LOCATION_PASSWORD 爲獲取準確位置的密碼，接口在 /get_best_location?password=密碼

FLASK_SECRET_KEY 是 Flask 的secret key，同時也是 Redis 的前綴。不要和使用同一 Redis 服務器的其他實例重名。

然後對 app.py 使用 WSGI 服務器 或 Web 服務器即可。

## 客戶端的配置

客戶端有3項

Sender ID 爲你的 GCM 服務的 Sender ID (Project ID)

Location Callback 爲 http://服務地址/update_location?UPDATE_PASSWORD= 其中 UPDATE_PASSWORD 需要替換爲服務端上配置的 UPDATE_PASSWORD 的值

RegID Callback 爲 http://服務地址/update_regid?UPDATE_PASSWORD= 其中 UPDATE_PASSWORD 需要替換爲服務端上配置的 UPDATE_PASSWORD 的值

然後點擊 Start 就可以了

你需要保證你的手機允許允許開機自啓動（即不屏蔽未曾啓動的應用的廣播消息）
