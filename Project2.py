import pandas as pd
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO
import streamlit as st
import textwrap
import zipfile
from oauth2client.service_account import ServiceAccountCredentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from google.oauth2 import service_account
import time
import gspread
import os
import json

st.title("Hai Everyone, Ini Versi ke-2")
st.write("Di versi ini bisa dibuat dengan cara manual 1 per 1, upload foto yang mau di update, terus lalu kodenya untuk dimasukkin ke keterangan.")
st.divider()
@st.cache_data
def get_data_from_google():
    with st.spinner("Getting data from Google Sheets..."):
        # Path ke file getlink.json Anda
        SERVICE_ACCOUNT_FILE = 'api.json'
        # Scopes yang diperlukan untuk Google Drive API
        SCOPES = ['https://www.googleapis.com/auth/drive']
        # Autentikasi menggunakan service account
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        # Membangun layanan Google Drive API
        client = gspread.authorize(credentials)
        sheet = client.open_by_key("1-mAmI6-XiWEM5vBlT6TLbeCmqus0ZvvSD_UHvN7zLnM")
        worksheet = sheet.worksheet('CatalogueUpdate')
        # Mendapatkan semua record dari worksheet
        catalogue = worksheet.get_all_records()
        catalogue = pd.DataFrame(catalogue)
        catalogue = catalogue.rename(columns={'Item No.': 'ItemCode'})
        return catalogue

if 'catalogue' not in st.session_state:
    st.session_state.catalogue = get_data_from_google()
catalogue = st.session_state.catalogue
# Pilihan untuk mengupload foto
photo = st.file_uploader("Upload your Photo", type=["jpg", "jpeg", "png"], key="photo")

if photo:
    # Pilihan untuk memilih harga dan itemcode
    selectprice = st.selectbox("Choose", options=['Harga Under', 'HargaLusin', 'HargaKoli', 'HargaSpecial'])
    itemcode = st.selectbox("ItemCode", options=catalogue['ItemCode'].unique())
    start = st.button("Start")
    file_user = catalogue[catalogue['ItemCode'] == itemcode]
    # Update foto ke Google Drive
    if start:
        # Mengambil file gambar yang di-upload
        img = Image.open(photo).convert("RGBA")
        img = img.resize((750, 750))  # Menyesuaikan ukuran gambar
        # Membuat template gambar
        template = Image.new("RGBA", (800, 1200), "white")
        image_x = (template.width - img.width) // 2
        image_y = 25
        template.paste(img, (image_x, image_y))
        # Menambahkan teks ke gambar
        font_path = "./Poppins-Regular.ttf"
        font_harga = ImageFont.truetype("./Poppins-SemiBold.ttf", size=20)
        current_font = ImageFont.truetype(font_path, size=20)
        if selectprice == 'Harga Under':
            colour = (250,250,250)  # N
        elif selectprice == 'HargaKoli':
            colour = (255,163,208)  # Pink
        elif selectprice == 'HargaLusin':
            colour = (250, 225, 135)  # Oranye
        elif selectprice == 'HargaSpecial':
            colour = (154,210,172)  # Hijau
        def wrap_text(text, font, max_width):
            wrapped_text = textwrap.fill(text, width=max_width // (font.getbbox('a')[2] - font.getbbox('a')[0]))
            return wrapped_text.splitlines()
        def add_text(template, draw, row, font, selectprice):
            item_code = row['ItemCode']
            item_name = row['ItemName']
            try:
                price = float(row[selectprice])
                harga_jual = f"Rp. {price:,.0f} / {row['Uom']}"
            except ValueError:
                harga_jual = f"Rp. {row[selectprice]} / {row['Uom']}"
            ctn = f"Isi Karton: {int(row['IsiCtn'])} {row['Uom']}" if pd.notna(row['IsiCtn']) else "N/A"
            # Wrap each line of text
            lines_item_code = wrap_text(f"{item_code}", font, max_width=450)
            lines_item_name = wrap_text(f"{item_name}", font, max_width=450)
            lines_harga_jual = wrap_text(harga_jual, font, max_width=450)
            lines_ctn = wrap_text(ctn, font, max_width=450)
            # Gabungkan semua teks
            all_lines = lines_item_code + lines_item_name + lines_harga_jual + lines_ctn
            # Gambar latar belakang untuk teks
            background_width = 735
            background_margin = 10
            x_position = 32.5
            y_start = 825
            # Hitung tinggi total teks
            total_text_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in all_lines)
            total_height = total_text_height + (len(all_lines) + 1) * 2 * background_margin
            # Gambar latar belakang
            rect_coords = [
                (x_position - background_margin, y_start),
                (x_position + background_width + background_margin, y_start + total_height),
            ]
            draw.rounded_rectangle(
                rect_coords,
                fill=colour,  # Warna latar belakang
                radius=15,  # Radius sudut
            )
            # Gambar semua teks di atas latar belakang
            y_offset = y_start + background_margin
            for line in all_lines:
                if line in lines_item_code:
                    font=font_harga
                elif line in lines_harga_jual:
                    font=font_harga
                elif line in lines_ctn:
                    font=current_font
                elif line in lines_item_name:
                    font=current_font
                text_width, text_height = draw.textbbox((0, 0), line, font=font)[2:4]
                text_x = x_position + (background_width - text_width) // 2
                draw.text((text_x, y_offset), line, font=font, fill="black")
                y_offset += text_height + 2 * background_margin
        # Menambahkan teks ke template
        draw = ImageDraw.Draw(template)
        add_text(template, draw, file_user.iloc[0], current_font, selectprice)
        # Menyimpan gambar dan membuat file download
        buf = BytesIO()
        template.save(buf, format='PNG')
        buf.seek(0)
        # Menyimpan file gambar
        file_name = f"{file_user.iloc[0]['ItemCode']}.jpg"
        st.image(buf)  # Menampilkan gambar di Streamlit
        st.download_button(
            label="Download Image",
            data=buf.getvalue(),
            file_name=file_name,
            mime="image/jpeg"
        )
