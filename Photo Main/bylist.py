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

st.set_page_config("Sukses Jaya - Create Photos")


start = st.button("Update Photos")


@st.cache_data
def get_data_from_google():
    with st.spinner("Getting data from Google Sheets..."):
        # Path ke file getlink.json Anda
        SERVICE_ACCOUNT_FILE = 'api.json'

        # Scopes yang diperlukan untuk Google Drive API
        SCOPES = ['https://www.googleapis.com/auth/drive']

        # Autentikasi menggunakan service account
        credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        # Membangun layanan Google Drive API
        service = build('drive', 'v3', credentials=credentials)
        client = gspread.authorize(credentials)
        sheet = client.open_by_key("18t23AKiAQmK4A4dmkwqYTOGj4gNuFMEAsBpY50zJLNY")
        worksheet = sheet.sheet1

        database = worksheet.get_all_records()
        database = pd.DataFrame(database)

        worksheet = sheet.worksheet('CatalogueUpdate')
        catalogue = worksheet.get_all_records()
        catalogue = pd.DataFrame(catalogue)
        catalogue['ItemCode'] = catalogue['ItemCode'].astype(str)
        return database, catalogue
    

st.session_state.database = get_data_from_google()[0]
st.session_state.catalogue = get_data_from_google()[1]

database = st.session_state.database
file_catalogue = st.session_state.catalogue
file_catalogue['U_Kategori'] = file_catalogue['U_Kategori'].astype(str)

if start:
    # Path ke file getlink.json Anda
    SERVICE_ACCOUNT_FILE = 'api.json'

    # Scopes yang diperlukan untuk Google Drive API
    SCOPES = ['https://www.googleapis.com/auth/drive']

    # Autentikasi menggunakan service account
    credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # Membangun layanan Google Drive API
    service = build('drive', 'v3', credentials=credentials)
    client = gspread.authorize(credentials)

    # Fungsi untuk mendapatkan daftar file dalam folder tertentu di Google Drive
    def list_files_in_folder(folder_id):
        query = f"'{folder_id}' in parents"
        page_token = None
        file_data = []

        while True:
            response = service.files().list(
                q=query, 
                spaces='drive', 
                fields="nextPageToken, files(id, name, mimeType, createdTime)", 
                pageToken=page_token
            ).execute()
            items = response.get('files', [])

            if not items:
                print('No files found.')
            else:
                for item in items:
                    if item['mimeType'].startswith('image/'):  # Pastikan hanya file gambar yang diambil
                        file_data.append({
                            'Name': item['name'],
                            'Link': f"https://drive.google.com/uc?export=download&id={item['id']}",
                            'Upload Date': item['createdTime']
                        })

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return file_data

    # ID folder yang ingin diakses
    FOLDER_ID = '1ugcMd2qFiQds85XyGqoHlEBpldLiohRH'

    # Mendapatkan data file dari folder
    fancy_data = list_files_in_folder("1_OA3QRfZU0tbBPyYrjnifmOcRdczdWtP")

    file_data = list_files_in_folder(FOLDER_ID)
    df_fancy = pd.DataFrame(fancy_data)
    # Membuat DataFrame dari data file
    df_foto = pd.DataFrame(file_data)

    # concat
    df_foto = pd.concat([df_fancy, df_foto], ignore_index=True)
    # df_foto = pd.append(df_fancy, df_foto, ignore_index=True)


    df_foto['Item No.'] = df_foto['Name'].str.replace('.jpg','', regex=False)
    df_foto['Item No.'] = df_foto['Item No.'].str.replace('.jpeg','', regex=False)
    df_foto['Item No.'] = df_foto['Item No.'].str.replace('.mp4','', regex=False)
    df_foto['Item No.'] = df_foto['Item No.'].str.replace('.Ink','', regex=False)
    df_foto['Item No.'] = df_foto['Item No.'].str.replace('.png','', regex=False)
    df_foto['Item No.'] = df_foto['Item No.'].str.replace('.ini','', regex=False)
    df_foto['Item No.'] = df_foto['Item No.'].str.replace('.jfif','', regex=False)
    df_foto.rename(columns={'Item No.' : 'Verse1'}, inplace=True)

    df_foto['MatchStatus'] = df_foto['Verse1'].apply(lambda x: 'Match' if x in file_catalogue['ItemCode'].values else 'Tidak Match')
    df_foto['ItemCode'] = df_foto.apply(
    lambda row: row['Verse1'] if row['MatchStatus'] == 'Match' else row['Verse1'].split(' ')[0],
    axis=1
)
    df_foto = df_foto.sort_values(by='Upload Date', ascending=False)

    # togooglesheets
    sheet = client.open_by_key("18t23AKiAQmK4A4dmkwqYTOGj4gNuFMEAsBpY50zJLNY")
    worksheet = sheet.sheet1
    worksheet.update([df_foto.columns.values.tolist()] + df_foto.values.tolist())

    st.success("Success Update Data")
    st.dataframe(df_foto)
    st.session_state.database = get_data_from_google()[0]
    st.session_state.catalogue = get_data_from_google()[1]








st.title("Hai Everyone! made by: V")
st.write("Ini versi pake list, bikin List excel dengan:")
st.write("judul Column1 = 'ItemCode' (isinya list ItemCode yang ingin dibuat fotonya)")
st.write("judul Column2 = 'List' (ini akan menjadi nama foldernya) ")
st.warning("Update Photo memerlukan ± 10 menit (tergantung internet)")
# Upload file Excel pengguna

file_upload = st.file_uploader("Upload File", type=["xlsx", "xls", "csv"])


if file_upload:
    try:
        # Membaca file berdasarkan ekstensi
        if file_upload.name.endswith(('.xls', '.xlsx')):
            file_user = pd.read_excel(file_upload)
        elif file_upload.name.endswith('.csv'):
            file_user = pd.read_csv(file_upload)

        file_user['ItemCode'] = file_user['ItemCode'].astype(str)
        start2 = st.button("Start Now")
    except Exception as e:
        st.error(f"Error reading files: {e}")
        st.stop()
else:
    st.warning("Please Upload all files.")
    st.stop()


# Dropdown untuk memilih harga
selectprice = st.selectbox(
    "Select", options=['Harga Under', 'HargaLusin', 'HargaSpecial']
)





if start2:
    with st.spinner("Waiting..."):
        database = database.sort_values(by='Upload Date', ascending=False)
        database['ItemCode'] = database['ItemCode'].astype(str)
        database['ItemCode'] = database['ItemCode'].str.upper()
        file_user['ItemCode'] = file_user['ItemCode'].astype(str)
        file_user['ItemCode'] = file_user['ItemCode'].str.upper()
        database['Upload Date'] = pd.to_datetime(database['Upload Date'], errors='coerce')
        database = database.loc[database.groupby('ItemCode')['Upload Date'].idxmax()]
        selected_df = pd.merge(file_user, database[['ItemCode', 'Link']], on='ItemCode', how='left')
        df_kosong = selected_df[selected_df['Link'].isna()]
        selected_df = selected_df[~selected_df['Link'].isna()]
        selected_df = pd.merge(selected_df, file_catalogue[['ItemCode', 'ItemName','Uom','IsiCtn', 'U_Kategori', 'Harga Under', 'HargaLusin', 'HargaKoli', 'HargaSpecial']], on='ItemCode', how='left')
        st.write("Yang dibuat:")
        st.dataframe(selected_df)
        st.write("Yang Tidak ada di Google Drive:")
        st.dataframe(df_kosong)

        font_path = "./Poppins-Regular.ttf"
        font_harga = ImageFont.truetype("./Poppins-SemiBold.ttf", size =20)
        current_font = ImageFont.truetype(font_path, size=20)
        font = ImageFont.truetype(font_path, size=20)
        if selectprice == 'Harga Under':
                colour = (255,163,208)  # Pink
        elif selectprice == 'HargaLusin':
            colour = (250, 225, 135)  # Oranye
        elif selectprice == 'HargaSpecial':
            colour = (154,210,172)  # Hijau
    with st.spinner("Making Image..."):
        def wrap_text(text, font, max_width):
            # Pembungkusan teks menggunakan textwrap
            wrapped_text = textwrap.fill(text, width=max_width // (font.getbbox('a')[2] - font.getbbox('a')[0]))  # Perhitungan dengan ukuran karakter 'a'

            return wrapped_text.splitlines()

        
        def add_image(img_url, row):

            try:
                template = Image.new("RGBA", (800, 1200), "white")  # Menambahkan warna RGB pada background
                response = requests.get(img_url)
                img = Image.open(BytesIO(response.content)).convert("RGBA")
                img = img.resize ((750,750))
                image_x = (template.width - img.width) // 2
                image_y = 25
                if row['U_Kategori'] == 'AKSESORIS RAMBUT KAMINO':
                    image_y = 100
                    logo = "./logo-kamino-for-web-new.png"
                    logo = Image.open(logo).convert("RGBA") 
                    logo = logo.resize((200, 100))
                    logo_x = (template.width - logo.width) // 2
                    template.paste(logo,(logo_x, 0), logo)

                if row['U_Kategori'] == 'LOLI & MOLI':
                    image_y = 100
                    logo = "./Lolimoli Logo-02.png"
                    logo = Image.open(logo).convert("RGBA") 
                    logo = logo.resize((150, 75))
                    logo_x = (template.width - logo.width) // 2
                    template.paste(logo,(logo_x, 15), logo)
                template.paste(img, (image_x, image_y))

            except Exception as e:
                st.error(f"Error loadingimage: {e} {row['ItemCode']}")

            return template
        
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

            # Gabungkan semua teks untuk menghitung tinggi total
            all_lines = lines_item_code + lines_item_name + lines_harga_jual + lines_ctn

            

            # Konfigurasi latar belakang
            background_width = 735
            background_margin = 10  # Margin sekitar teks
            corner_radius = 15  # Radius untuk rounded rectangle
            x_position = 32.5  # Posisi X tetap
            y_start = 825  # Posisi Y awal
            if row['U_Kategori'] in (['AKSESORIS RAMBUT KAMINO', 'LOLI & MOLI']):
                y_start = 900

            # Hitung tinggi total teks dan latar belakang
            total_text_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in all_lines)
            total_height = total_text_height + (len(all_lines) + 1) * 2 * background_margin  # Tambahkan margin antar baris

            # Gambar latar belakang
            rect_coords = [
                (x_position - background_margin, y_start),
                (x_position + background_width + background_margin, y_start + total_height),
            ]
            draw.rounded_rectangle(
                rect_coords,
                fill=colour,  # Warna latar belakang
                radius=corner_radius,  # Radius sudut
            )

            # Gambar semua teks di atas latar belakang
            y_offset = y_start + background_margin
            for line in all_lines:
                if line in lines_item_code:
                    font = font_harga
                elif line in lines_item_name:
                    font = current_font
                elif line in lines_harga_jual:
                    font = font_harga
                elif line in lines_ctn:
                    font = current_font
                    
                text_width, text_height = draw.textbbox((0, 0), line, font=font)[2:4]

                # Pusatkan teks secara horizontal dalam latar belakang
                text_x = x_position + (background_width - text_width) // 2
                draw.text((text_x, y_offset), line, font=font, fill="black")

                # Perbarui posisi Y untuk baris berikutnya
                y_offset += text_height + 2 * background_margin


    with st.spinner("Paste to template..."):
        category_dict = {}
        image_paths = []

        for index, row in selected_df.iterrows():
            img_template = add_image(row['Link'], row)
            draw = ImageDraw.Draw(img_template)
            add_text(img_template, draw, row, font, selectprice)
            

            buf = BytesIO()
            img_template.save(buf, format='PNG')
            buf.seek(0)
            file_name = f"{row['ItemCode']}.jpg"
            image_paths.append((file_name, buf.getvalue()))
            category = row['List']
            if category not in category_dict:
                category_dict[category] = []
            category_dict[category].append((file_name, buf.getvalue()))

        if image_paths:
            st.image(image_paths[0][1])
    with st.spinner("Create Zip File..."):
        # Membuat ZIP file dengan struktur folder berdasarkan kategori
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for category, files in category_dict.items():
                for file_name, image_data in files:
                    file_path = f"{category}/{file_name}"  # Menyimpan gambar dalam folder kategori
                    zipf.writestr(file_path, image_data)

        zip_buffer.seek(0)

        # Tombol download ZIP
        st.download_button(
            label="Download ZIP",
            data=zip_buffer,
            file_name="Ready_to_Upload.zip",
            mime="application/zip"
        )
