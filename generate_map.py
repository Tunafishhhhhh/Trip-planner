import folium
import pandas as pd

# 讀取行程 CSV 檔案
df = pd.read_csv('itinerary.csv')

# 以行程的第一個地點作為地圖的中心點
start_lat = df['lat'].iloc[0]
start_lon = df['lon'].iloc[0]

# 改用 Esri 世界街道地圖底圖，徹底避開 OpenStreetMap 的 403 封鎖
my_map = folium.Map(
    location=[start_lat, start_lon], zoom_start=9, tiles='Esri.WorldStreetMap'
)

# 用迴圈把每一個行程點加到地圖上
for index, row in df.iterrows():
  # 設定點擊標記時跳出的彈窗內容
  popup_content = (
      f"<b>Day {row['day']}: {row['location_name']}</b><br>備註: {row['note']}"
  )

  folium.Marker(
      location=[row['lat'], row['lon']],
      popup=folium.Popup(popup_content, max_width=300),
      tooltip=row['location_name'],  # 滑鼠移上去時顯示的名字
      icon=folium.Icon(color='blue', icon='info-sign'),
  ).add_to(my_map)

# 將地圖儲存成一個網頁檔案
my_map.save('travel_map.html')
print('太棒了！地圖已成功生成，檔名為 travel_map.html')
