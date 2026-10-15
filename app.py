from datetime import date, timedelta
from geopy.geocoders import Nominatim
import folium
import pandas as pd
import streamlit as st

# 設定網頁標題與寬版面配置
st.set_page_config(page_title="我的個人旅行與航班助手", layout="wide")

st.title("✈️ 個人旅行與行程地圖儀表板")

# 初始化 Session State 裡的資料（含全新的飯店日期欄位）
if "itinerary" not in st.session_state:
  try:
    st.session_state.itinerary = pd.read_csv("itinerary.csv")
  except FileNotFoundError:
    st.session_state.itinerary = pd.DataFrame(
        columns=["day", "location_name", "lat", "lon", "note"]
    )
    st.session_state.itinerary.to_csv("itinerary.csv", index=False)

if "hotels" not in st.session_state:
  try:
    st.session_state.hotels = pd.read_csv("hotels.csv")
  except FileNotFoundError:
    st.session_state.hotels = pd.DataFrame(
        columns=[
            "hotel_name",
            "address",
            "check_in",
            "check_out",
            "nights",
            "lat",
            "lon",
            "note",
        ]
    )
    st.session_state.hotels.to_csv("hotels.csv", index=False)

if "transport" not in st.session_state:
  try:
    st.session_state.transport = pd.read_csv("transport.csv")
  except FileNotFoundError:
    st.session_state.transport = pd.DataFrame(
        columns=[
            "transport_name",
            "date",
            "origin",
            "destination",
            "status",
            "note",
        ]
    )
    st.session_state.transport.to_csv("transport.csv", index=False)

if "flight_info" not in st.session_state:
  try:
    with open("flight.txt", "r", encoding="utf-8") as f:
      st.session_state.flight_info = f.read()
  except FileNotFoundError:
    st.session_state.flight_info = (
        "例如: AC888 YYZ to CDG, 2026-12-18\n(輸入後會自動儲存)"
    )

# --- 側邊欄：新增與設定 ---
with st.sidebar:
  st.header("📝 旅程與航班設定")

  # 航班資訊文字框（具備自動儲存功能）
  flight_input_val = st.text_area(
      "航班資訊 (Flight Info)", value=st.session_state.flight_info, height=150
  )
  if flight_input_val != st.session_state.flight_info:
    st.session_state.flight_info = flight_input_val
    with open("flight.txt", "w", encoding="utf-8") as f:
      f.write(flight_input_val)

  st.markdown("---")
  st.subheader("🚆 新增交通方式")
  trans_name_input = st.text_input(
      "交通工具/班次名稱", "例如：Eurostar 歐洲之星"
  )
  trans_date_input = st.date_input("交通日期 (Date)", value=date.today())
  trans_origin_input = st.text_input("起點 (Origin)", "例如：Paris Gare du Nord")
  trans_dest_input = st.text_input(
      "終點 (Destination)", "例如：London St Pancras"
  )
  trans_status = st.selectbox(
      "預訂狀態", ["已預訂 ✅", "未預訂 ⏳", "考慮中 🤔"]
  )
  trans_note = st.text_area("交通備註", "車票代碼、座位號碼等")

  if st.button("➕ 新增交通工具"):
    if trans_name_input and trans_origin_input and trans_dest_input:
      new_trans = pd.DataFrame({
          "transport_name": [trans_name_input],
          "date": [str(trans_date_input)],
          "origin": [trans_origin_input],
          "destination": [trans_dest_input],
          "status": [trans_status],
          "note": [trans_note],
      })
      st.session_state.transport = pd.concat(
          [st.session_state.transport, new_trans], ignore_index=True
      )
      st.session_state.transport.to_csv("transport.csv", index=False)
      st.success(f"成功新增交通項目「{trans_name_input}」！")
      st.rerun()
    else:
      st.warning("請填寫交通名稱、起點與總起終點！")

  st.markdown("---")
  st.subheader("🏨 新增住宿飯店")
  hotel_name_input = st.text_input("飯店名稱", "例如：Novotel Paris Centre")
  hotel_address_input = st.text_input(
      "飯店地址或城市", "例如：Paris, France 或 街道地址"
  )

  col_d1, col_d2 = st.columns(2)
  with col_d1:
    check_in_input = st.date_input("入住日期", value=date.today(), key="h_in")
  with col_d2:
    check_out_input = st.date_input(
        "退房日期", value=date.today() + timedelta(days=2), key="h_out"
    )

  hotel_nights = (check_out_input - check_in_input).days
  if hotel_nights < 1:
    hotel_nights = 1
    st.warning("退房日期需晚於入住日期，已自動設為 1 晚。")
  else:
    st.info(f"自動計算入住天數：{hotel_nights} 晚")

  hotel_note = st.text_area("飯店備註", "含早餐、已付訂金")

  if st.button("➕ 新增飯店"):
    if hotel_name_input and hotel_address_input:
      with st.spinner("正在自動搜尋飯店位置中..."):
        try:
          geolocator = Nominatim(user_agent="my_travel_app_streamlit")
          search_query = f"{hotel_name_input}, {hotel_address_input}"
          location = geolocator.geocode(search_query)

          if not location:
            location = geolocator.geocode(hotel_address_input)

          if location:
            lat = location.latitude
            lon = location.longitude

            new_hotel = pd.DataFrame({
                "hotel_name": [hotel_name_input],
                "address": [hotel_address_input],
                "check_in": [str(check_in_input)],
                "check_out": [str(check_out_input)],
                "nights": [int(hotel_nights)],
                "lat": [lat],
                "lon": [lon],
                "note": [hotel_note],
            })

            st.session_state.hotels = pd.concat(
                [st.session_state.hotels, new_hotel], ignore_index=True
            )
            st.session_state.hotels.to_csv("hotels.csv", index=False)

            st.success(f"成功新增飯店「{hotel_name_input}」！")
            st.rerun()
          else:
            st.error("找不到這個地址，請嘗試輸入更具體的城市名稱。")
        except Exception as e:
          st.error(f"查詢時發生錯誤: {e}")
    else:
      st.warning("請填寫飯店名稱與地址！")

  st.markdown("---")
  st.subheader("📍 新增景點")
  day_num = st.number_input(
      "天數 (Day)", min_value=1, value=1, step=1, format="%d"
  )
  place_name = st.text_input("景點名稱", "例如：Eiffel Tower")
  place_address = st.text_input("景點地址或城市", "例如：Paris, France")
  note_input = st.text_area("備註說明", "拍照與參觀")

  if st.button("➕ 自動搜尋並加入行程"):
    if place_name and place_address:
      with st.spinner("正在自動查詢地點中..."):
        try:
          geolocator = Nominatim(user_agent="my_travel_app_streamlit")
          search_query = f"{place_name}, {place_address}"
          location = geolocator.geocode(search_query)

          if not location:
            location = geolocator.geocode(place_address)

          if location:
            lat = location.latitude
            lon = location.longitude

            new_row = pd.DataFrame({
                "day": [int(day_num)],
                "location_name": [place_name],
                "lat": [lat],
                "lon": [lon],
                "note": [note_input],
            })

            st.session_state.itinerary = pd.concat(
                [st.session_state.itinerary, new_row], ignore_index=True
            )
            st.session_state.itinerary = st.session_state.itinerary.sort_values(
                by=["day"]
            ).reset_index(drop=True)
            st.session_state.itinerary.to_csv("itinerary.csv", index=False)

            st.success(f"成功找到「{place_name}」並加入 Day {int(day_num)}！")
            st.rerun()
          else:
            st.error("找不到這個地點，請試著輸入更詳細的城市或國家。")
        except Exception as e:
          st.error(f"查詢時發生錯誤: {e}")
    else:
      st.warning("請填寫景點名稱與地址！")

# --- 主畫面：三大主分頁 ---
main_tab1, main_tab2, main_tab3 = st.tabs(
    ["📍 每日行程與地圖", "🏨 住宿與 🚆 交通管理", "✈️ 航班與摘要"]
)

# 【分頁 1：每日行程與地圖】
with main_tab1:
  col_map1, col_map2 = st.columns([1, 1])

  with col_map1:
    st.subheader("📅 按天數檢視行程")
    df = st.session_state.itinerary

    if not df.empty:
      unique_days = sorted(df["day"].unique())
      day_tabs = st.tabs([f"Day {int(d)}" for d in unique_days])

      for tab, d in zip(day_tabs, unique_days):
        with tab:
          day_df = df[df["day"] == d]
          edited_day_df = st.data_editor(
              day_df[["location_name", "note", "lat", "lon"]],
              key=f"day_editor_{d}",
              use_container_width=True,
              hide_index=True,
          )
          if not edited_day_df.equals(day_df[["location_name", "note", "lat", "lon"]]):
            df.loc[df["day"] == d, ["location_name", "note", "lat", "lon"]] = (
                edited_day_df.values
            )
            st.session_state.itinerary = df
            st.session_state.itinerary.to_csv("itinerary.csv", index=False)

      st.markdown("")
      itin_options = {}
      for idx, row in st.session_state.itinerary.iterrows():
        label = f"Day {int(row['day'])}: {row['location_name']}"
        itin_options[label] = idx

      col_i1, col_i2 = st.columns([3, 1])
      with col_i1:
        selected_itin_label = st.selectbox(
            "選擇要移除的景點",
            list(itin_options.keys()),
            key="del_itin_sb",
            label_visibility="collapsed",
        )
      with col_i2:
        if st.button("🗑️ 刪除景點", key="del_itin_btn"):
          idx_to_remove = itin_options[selected_itin_label]
          st.session_state.itinerary = (
              st.session_state.itinerary.drop(idx_to_remove).reset_index(
                  drop=True
              )
          )
          st.session_state.itinerary.to_csv("itinerary.csv", index=False)
          st.success("已成功刪除該景點！")
          st.rerun()
    else:
      st.info("目前還沒有任何行程。")

  with col_map2:
    st.subheader("🗺️ 互動地圖預覽")
    df = st.session_state.itinerary
    hotels_df = st.session_state.hotels

    if not df.empty:
      start_lat = df["lat"].iloc[0]
      start_lon = df["lon"].iloc[0]
    elif not hotels_df.empty:
      start_lat = hotels_df["lat"].iloc[0]
      start_lon = hotels_df["lon"].iloc[0]
    else:
      start_lat, start_lon = 49.2827, -123.1207

    m = folium.Map(
        location=[start_lat, start_lon], zoom_start=6, tiles="Esri.WorldStreetMap"
    )

    # 1. 標註飯店
    if not hotels_df.empty:
      for _, h_row in hotels_df.iterrows():
        h_lat, h_lon = h_row["lat"], h_row["lon"]
        popup_text = f"<b>🏨 住宿: {h_row['hotel_name']}</b><br>地址: {h_row['address']}<br>入住: {h_row['check_in']} ~ 退房: {h_row['check_out']} ({h_row['nights']} 晚)<br>{h_row['note']}"
        folium.Marker(
            [h_lat, h_lon],
            popup=popup_text,
            tooltip=f"飯店: {h_row['hotel_name']}",
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
        ).add_to(m)

    # 2. 標註景點與畫連線
    if not df.empty:
      colors = ["blue", "green", "purple", "orange", "cadetblue"]
      unique_days = sorted(df["day"].unique())

      for i, d in enumerate(unique_days):
        day_df = df[df["day"] == d]
        day_color = colors[i % len(colors)]
        day_coords = []

        for _, row in day_df.iterrows():
          lat, lon = row["lat"], row["lon"]
          day_coords.append([lat, lon])

          popup_text = f"<b>Day {int(row['day'])}: {row['location_name']}</b><br>{row['note']}"
          folium.Marker(
              [lat, lon],
              popup=popup_text,
              tooltip=f"Day {int(row['day'])}: {row['location_name']}",
              icon=folium.Icon(color=day_color, icon="info-sign"),
          ).add_to(m)

        if len(day_coords) > 1:
          folium.PolyLine(
              day_coords,
              color=day_color,
              weight=4,
              opacity=0.8,
              tooltip=f"Day {d} 路線",
          ).add_to(m)

    st.components.v1.html(m._repr_html_(), height=500)

# 【分頁 2：住宿與交通管理】
with main_tab2:
  col_t1, col_t2 = st.columns([1, 1])

  with col_t1:
    st.subheader("🏨 住宿飯店清單")
    if not st.session_state.hotels.empty:
      hotel_cols_to_show = [
          "hotel_name",
          "address",
          "check_in",
          "check_out",
          "nights",
          "note",
      ]
      for col in hotel_cols_to_show:
        if col not in st.session_state.hotels.columns:
          st.session_state.hotels[col] = ""

      edited_hotels = st.data_editor(
          st.session_state.hotels[hotel_cols_to_show],
          key="hotels_editor",
          use_container_width=True,
          hide_index=True,
      )
      if not edited_hotels.equals(
          st.session_state.hotels[hotel_cols_to_show]
      ):
        st.session_state.hotels.update(edited_hotels)
        st.session_state.hotels.to_csv("hotels.csv", index=False)

      hotel_options = {}
      for idx, row in st.session_state.hotels.iterrows():
        label = f"{row['hotel_name']} ({row['check_in']} 起, {row['nights']} 晚)"
        hotel_options[label] = idx

      col_h1, col_h2 = st.columns([3, 1])
      with col_h1:
        selected_hotel_label = st.selectbox(
            "選擇要移除的飯店",
            list(hotel_options.keys()),
            key="del_hotel_sb",
            label_visibility="collapsed",
        )
      with col_h2:
        if st.button("🗑️ 刪除飯店", key="del_hotel_btn"):
          h_idx_to_remove = hotel_options[selected_hotel_label]
          st.session_state.hotels = (
              st.session_state.hotels.drop(h_idx_to_remove).reset_index(
                  drop=True
              )
          )
          st.session_state.hotels.to_csv("hotels.csv", index=False)
          st.success("已成功刪除該飯店！")
          st.rerun()
    else:
      st.info("目前尚無住宿資訊。")

  with col_t2:
    st.subheader("🚆 交通運輸清單")
    if not st.session_state.transport.empty:
      cols_to_show = [
          "transport_name",
          "date",
          "origin",
          "destination",
          "status",
          "note",
      ]
      for col in cols_to_show:
        if col not in st.session_state.transport.columns:
          st.session_state.transport[col] = ""

      edited_transport = st.data_editor(
          st.session_state.transport[cols_to_show],
          key="transport_editor",
          use_container_width=True,
          hide_index=True,
      )
      if not edited_transport.equals(
          st.session_state.transport[cols_to_show]
      ):
        st.session_state.transport.update(edited_transport)
        st.session_state.transport.to_csv("transport.csv", index=False)

      trans_options = {}
      for idx, row in st.session_state.transport.iterrows():
        label = f"{row['transport_name']} ({row['date']}: {row['origin']} -> {row['destination']})"
        trans_options[label] = idx

      col_tr1, col_tr2 = st.columns([3, 1])
      with col_tr1:
        selected_trans_label = st.selectbox(
            "選擇要移除的交通項目",
            list(trans_options.keys()),
            key="del_trans_sb",
            label_visibility="collapsed",
        )
      with col_tr2:
        if st.button("🗑️ 刪除交通", key="del_trans_btn"):
          t_idx_to_remove = trans_options[selected_trans_label]
          st.session_state.transport = (
              st.session_state.transport.drop(t_idx_to_remove).reset_index(
                  drop=True
              )
          )
          st.session_state.transport.to_csv("transport.csv", index=False)
          st.success("已成功刪除該交通項目！")
          st.rerun()
    else:
      st.info("目前尚無交通資訊。")

# 【分頁 3：航班與摘要】
with main_tab3:
  st.subheader("📋 旅程與航班總覽")
  st.markdown("✈️ **航班資訊：**")
  st.markdown(
      st.session_state.flight_info.replace("\n", "  \n")
      if st.session_state.flight_info
      else "尚未填寫航班資訊。"
  )