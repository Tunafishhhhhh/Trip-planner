from datetime import date, timedelta
import io
import zipfile
from geopy.geocoders import Nominatim
import folium
import pandas as pd
import streamlit as st

# 設定網頁標題與寬版面配置
st.set_page_config(page_title="個人旅行與行程地圖儀表板", layout="wide")

# --- 🎨 完美適應深色/淺色模式的現代化 CSS ---
st.markdown(
    """
    <style>
    /* 按鈕現代化圓角與互動過場 */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease-in-out;
    }
    
    /* 輸入框與文字區域圓角優化 */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px;
    }

    /* 讓 expander (收納卡片) 在深色/淺色模式下都保持極佳質感 */
    div.stExpander {
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }

    /* 空資料狀態視覺卡片樣式 */
    .empty-state-card {
        padding: 2rem;
        border-radius: 12px;
        border: 2px dashed rgba(128, 128, 128, 0.3);
        text-align: center;
        margin: 1rem 0;
    }
    .empty-state-card h4 {
        margin-bottom: 0.5rem;
        opacity: 0.9;
    }
    .empty-state-card p {
        opacity: 0.6;
        font-size: 0.9rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 初始化自訂標題（優先讀取 title.txt，沒有的話用預設值）
if "app_title" not in st.session_state:
  try:
    with open("title.txt", "r", encoding="utf-8") as f:
      st.session_state.app_title = f.read().strip()
  except FileNotFoundError:
    st.session_state.app_title = "✈️ 個人旅行與行程地圖儀表板"

# --- 頂部標題與即時修改區 ---
col_title_1, col_title_2 = st.columns([3, 1])

with col_title_1:
  st.title(st.session_state.app_title)

with col_title_2:
  with st.expander("✏️ 修改網頁標題"):
    new_title_input = st.text_input(
        "輸入新標題", value=st.session_state.app_title
    )
    if new_title_input != st.session_state.app_title:
      st.session_state.app_title = new_title_input
      with open("title.txt", "w", encoding="utf-8") as f:
        f.write(new_title_input)
      st.success("標題已更新！")
      st.rerun()

# 初始化 Session State 裡的資料
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
    required_hotel_cols = [
        "hotel_name",
        "address",
        "check_in",
        "check_out",
        "nights",
        "lat",
        "lon",
        "note",
    ]
    for col in required_hotel_cols:
      if col not in st.session_state.hotels.columns:
        st.session_state.hotels[col] = ""
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

if "links" not in st.session_state:
  try:
    st.session_state.links = pd.read_csv("links.csv")
  except FileNotFoundError:
    st.session_state.links = pd.DataFrame(
        columns=["title", "category", "url", "note"]
    )
    st.session_state.links.to_csv("links.csv", index=False)

if "flight_info" not in st.session_state:
  try:
    with open("flight.txt", "r", encoding="utf-8") as f:
      st.session_state.flight_info = f.read()
  except FileNotFoundError:
    st.session_state.flight_info = (
        "例如: AC888 YYZ to CDG, 2026-12-18\n(輸入後會自動儲存)"
    )

st.markdown("---")

# --- 側邊欄：現代感收納排版與總天數設定 ---
with st.sidebar:
  st.header("⚙️ 控制中心")

  # 1. 總行程天數設定
  with st.expander("📅 旅程總天數設定", expanded=True):
    max_existing_day = (
        int(st.session_state.itinerary["day"].max())
        if not st.session_state.itinerary.empty
        else 1
    )
    default_total_days = max(5, max_existing_day)
    total_days = st.number_input(
        "預計旅行天數",
        min_value=1,
        max_value=30,
        value=default_total_days,
        step=1,
        help="設定後會在每日行程分頁中自動為你準備好對應天數的頁籤",
    )

  # 2. 航班資訊
  with st.expander("✈️ 航班資訊", expanded=False):
    flight_input_val = st.text_area(
        "航班細節",
        value=st.session_state.flight_info,
        height=130,
        label_visibility="collapsed",
    )
    if flight_input_val != st.session_state.flight_info:
      st.session_state.flight_info = flight_input_val
      with open("flight.txt", "w", encoding="utf-8") as f:
        f.write(flight_input_val)

  # 3. 資料備份
  with st.expander("💾 資料備份", expanded=False):
    st.caption("將所有行程資料打包下載：")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
      zip_file.writestr("title.txt", st.session_state.app_title)
      if not st.session_state.itinerary.empty:
        zip_file.writestr(
            "itinerary.csv", st.session_state.itinerary.to_csv(index=False)
        )
      if not st.session_state.hotels.empty:
        zip_file.writestr(
            "hotels.csv", st.session_state.hotels.to_csv(index=False)
        )
      if not st.session_state.links.empty:
        zip_file.writestr("links.csv", st.session_state.links.to_csv(index=False))
      if st.session_state.flight_info:
        zip_file.writestr("flight.txt", st.session_state.flight_info)

    zip_buffer.seek(0)
    st.download_button(
        label="📦 一鍵下載 ZIP 備份",
        data=zip_buffer,
        file_name="travel_backup.zip",
        mime="application/zip",
        use_container_width=True,
    )

  st.divider()
  st.caption("✨ Version 1.0 • Built with Python & Streamlit")

# --- 主畫面：三大主分頁 ---
main_tab1, main_tab2, main_tab3 = st.tabs(
    ["📍 每日行程與地圖", "🏨 住宿管理", "✈️ 航班、票券與摘要"]
)

# 【分頁 1：每日行程與地圖】
with main_tab1:
  st.subheader("📅 每日行程規劃與編輯")
  df = st.session_state.itinerary

  day_list = list(range(1, int(total_days) + 1))
  day_tabs = st.tabs([f"Day {d}" for d in day_list])

  for tab, d in zip(day_tabs, day_list):
    with tab:
      day_df = df[df["day"] == d] if not df.empty else pd.DataFrame()

      if not day_df.empty:
        # 💡 隱藏 lat 和 lon，只留下 day, location_name, note 讓使用者編輯
        display_df = day_df[["day", "location_name", "note"]]
        edited_display_df = st.data_editor(
            display_df,
            key=f"day_editor_{d}",
            use_container_width=True,
            hide_index=True,
        )
        if not edited_display_df.equals(display_df):
          # 將修改後的 day, location_name, note 更新回去，同時保留原本的 lat 和 lon
          df.loc[df["day"] == d, ["day", "location_name", "note"]] = (
              edited_display_df.values
          )
          df["day"] = pd.to_numeric(df["day"])
          st.session_state.itinerary = (
              df.sort_values(by=["day"]).reset_index(drop=True)
          )
          st.session_state.itinerary.to_csv("itinerary.csv", index=False)
          st.rerun()
      else:
        st.markdown(
            f"""
            <div class="empty-state-card">
                <h4>🗺️ Day {d} 尚未安排任何行程</h4>
                <p>透過下方的新增景點工具，即可將地點加入這一天！</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

  if not df.empty:
    st.markdown("")
    itin_options = {}
    for idx, row in st.session_state.itinerary.iterrows():
      label = f"Day {int(row['day'])}: {row['location_name']}"
      itin_options[label] = idx

    col_i1, col_i2 = st.columns([4, 1])
    with col_i1:
      selected_itin_label = st.selectbox(
          "選擇要移除的景點",
          list(itin_options.keys()),
          key="del_itin_sb",
          label_visibility="collapsed",
      )
    with col_i2:
      if st.button("🗑️ 刪除景點", key="del_itin_btn", use_container_width=True):
        idx_to_remove = itin_options[selected_itin_label]
        st.session_state.itinerary = (
            st.session_state.itinerary.drop(idx_to_remove).reset_index(drop=True)
        )
        st.session_state.itinerary.to_csv("itinerary.csv", index=False)
        st.success("已成功刪除該景點！")
        st.rerun()

  st.markdown("---")

  col_bottom_add, col_bottom_map = st.columns([1, 1])

  with col_bottom_add:
    with st.expander("➕ 點擊展開：新增景點工具", expanded=False):
      day_num = st.number_input(
          "選擇天數 (Day)",
          min_value=1,
          max_value=int(total_days),
          value=1,
          step=1,
          format="%d",
          key="tab1_day",
      )
      place_name = st.text_input(
          "景點名稱", "例如：Eiffel Tower", key="tab1_pname"
      )
      place_address = st.text_input(
          "景點地址或城市", "例如：Paris, France", key="tab1_paddr"
      )
      note_input = st.text_area(
          "備註說明", "拍照與參觀", key="tab1_pnote", height=80
      )

      if st.button("➕ 自動搜尋並加入行程", key="tab1_add_btn", use_container_width=True):
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
                st.session_state.itinerary = (
                    st.session_state.itinerary.sort_values(by=["day"]).reset_index(
                        drop=True
                    )
                )
                st.session_state.itinerary.to_csv("itinerary.csv", index=False)

                st.success(f"成功找到「{place_name}」並加入 Day {int(day_num)}！")
                st.rerun()
              else:
                st.error("找不到這個地點，請試著輸入更詳細的城市或國家。")
            except Exception as e:
              st.error(f"查詢時發生錯誤: {e}")
        else:
          st.warning("請填寫景點名稱與地址！")

  with col_bottom_map:
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

# 【分頁 2：住宿管理】
with main_tab2:
  st.subheader("🏨 新增與管理住宿飯店")

  with st.expander("➕ 點擊展開：新增住宿飯店", expanded=True):
    hotel_name_input = st.text_input(
        "飯店名稱", "例如：Novotel Paris Centre", key="t2_hname"
    )
    hotel_address_input = st.text_input(
        "飯店地址或城市",
        "例如：Paris, France 或 街道地址",
        key="t2_haddr",
    )

    col_d1, col_d2 = st.columns(2)
    with col_d1:
      check_in_input = st.date_input(
          "入住日期", value=date.today(), key="t2_h_in"
      )
    with col_d2:
      check_out_input = st.date_input(
          "退房日期",
          value=date.today() + timedelta(days=2),
          key="t2_h_out",
      )

    hotel_nights = (check_out_input - check_in_input).days
    if hotel_nights < 1:
      hotel_nights = 1
      st.warning("退房日期需晚於入住日期，已自動設為 1 晚。")
    else:
      st.info(f"自動計算入住天數：{hotel_nights} 晚")

    hotel_note = st.text_area(
        "飯店備註", "含早餐、已付訂金", key="t2_hnote", height=68
    )

    if st.button("➕ 新增飯店", key="t2_add_hotel_btn"):
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
  st.subheader("📋 住宿飯店清單管理")

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
    if not edited_hotels.equals(st.session_state.hotels[hotel_cols_to_show]):
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
            st.session_state.hotels.drop(h_idx_to_remove).reset_index(drop=True)
        )
        st.session_state.hotels.to_csv("hotels.csv", index=False)
        st.success("已成功刪除該飯店！")
        st.rerun()
  else:
    st.markdown(
        """
        <div class="empty-state-card">
            <h4>🏨 尚無住宿預訂資料</h4>
            <p>點擊上方展開選單，填寫並加入你的第一個飯店吧！</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

# 【分頁 3：航班、票券與摘要】
with main_tab3:
  st.subheader("📋 旅程與航班總覽")
  st.markdown("✈️ **航班資訊：**")
  st.markdown(
      st.session_state.flight_info.replace("\n", "  \n")
      if st.session_state.flight_info
      else "尚未填寫航班資訊。"
  )

  st.markdown("---")
  st.subheader("🔗 重要連結與票券快捷區")

  with st.expander("➕ 新增常用連結或票券", expanded=False):
    col_l1, col_l2 = st.columns(2)
    with col_l1:
      link_title = st.text_input(
          "項目名稱", "例如：羅浮宮門票 / 歐洲之星車票", key="link_title_in"
      )
      link_category = st.selectbox(
          "分類",
          ["門票 🎫", "住宿確認 🏨", "交通車票 🚆", "實用網站 🌐", "其他備忘 📌"],
          key="link_cat_in",
      )
    with col_l2:
      link_url = st.text_input("網址 (URL)", "例如：https://...", key="link_url_in")
      link_note = st.text_input(
          "備註說明", "例如：已付費，須帶護照取票", key="link_note_in"
      )

    if st.button("➕ 加入快捷清單", key="add_link_btn"):
      if link_title and link_url:
        new_link_row = pd.DataFrame({
            "title": [link_title],
            "category": [link_category],
            "url": [link_url],
            "note": [link_note],
        })
        st.session_state.links = pd.concat(
            [st.session_state.links, new_link_row], ignore_index=True
        )
        st.session_state.links.to_csv("links.csv", index=False)
        st.success(f"成功新增「{link_title}」！")
        st.rerun()
      else:
        st.warning("請至少填寫項目名稱與網址！")

  links_df = st.session_state.links
  if not links_df.empty:
    edited_links = st.data_editor(
        links_df[["title", "category", "url", "note"]],
        key="links_editor",
        use_container_width=True,
        hide_index=True,
    )
    if not edited_links.equals(links_df[["title", "category", "url", "note"]]):
      st.session_state.links.update(edited_links)
      st.session_state.links.to_csv("links.csv", index=False)

    link_options = {}
    for idx, row in links_df.iterrows():
      label = f"[{row['category']}] {row['title']} ({row['url']})"
      link_options[label] = idx

    col_lk1, col_lk2 = st.columns([3, 1])
    with col_lk1:
      selected_link_label = st.selectbox(
          "選擇要移除的連結",
          list(link_options.keys()),
          key="del_link_sb",
          label_visibility="collapsed",
      )
    with col_lk2:
      if st.button("🗑️ 刪除連結", key="del_link_btn"):
        l_idx_to_remove = link_options[selected_link_label]
        st.session_state.links = (
            st.session_state.links.drop(l_idx_to_remove).reset_index(drop=True)
        )
        st.session_state.links.to_csv("links.csv", index=False)
        st.success("已成功刪除該項目！")
        st.rerun()
  else:
    st.markdown(
        """
        <div class="empty-state-card">
            <h4>🔗 尚無任何重要連結與票券</h4>
            <p>點擊上方展開選單，把你的門票網址、飯店確認信或實用工具連結存放在這裡吧！</p>
        </div>
    """,
        unsafe_allow_html=True,
    )