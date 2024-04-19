import psycopg2
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io


def image_to_text(path):

    input_img= Image.open(path)
    
    #conver image to array format
    image_array= np.array(input_img)
    
    reader = easyocr.Reader(['en'])
    text= reader.readtext(image_array, detail=0)

    return text, input_img


def extracted_text(texts):

    extracted_dict ={'NAME':[],'DESIGNATION':[],'COMPANY_NAME':[],'CONTACT':[],'EMAIL':[],'WEBSITE':[],'ADDRESS':[],'PINCODE':[]}

    extracted_dict['NAME'].append(texts[0])
    extracted_dict['DESIGNATION'].append(texts[1])

    for i in range (2,len(texts)):
        if texts[i].startswith('+') or (texts[i].replace('-','').isdigit()and'-'in texts[i]):
            extracted_dict['CONTACT'].append(texts[i])

        elif 'WWW' in texts[i] or 'www' in texts[i] or 'Www' in texts[i] or 'WWw' in texts[i] or 'wWw' in texts[i] or 'WwW' in texts[i] or 'wwW' in texts[i]:
            small= texts[i].lower()
            extracted_dict['WEBSITE'].append(small)

        elif '@' in texts[i]and'.com' in texts[i]:
            extracted_dict['EMAIL'].append(texts[i])

        elif 'Tamil Nadu' in texts[i] or 'TamilNadu' in texts[i] or texts[i].isdigit():
            extracted_dict['PINCODE'].append(texts[i])

        elif re.match(r'^[A-Za-z]',texts[i]):
            extracted_dict['COMPANY_NAME'].append(texts[i])

        else:
            remove_colon= re.sub(r'[,;]','',texts[i])
            extracted_dict['ADDRESS'].append(texts[i])
    
    for key,value in extracted_dict.items():
        if len(value)>0:
            concadenate=''.join(value)
            extracted_dict[key]= [concadenate]

        else:
            value = 'NA'
            extracted_dict[key]= [value]
            

    return extracted_dict
            



#streamlit part

st.set_page_config(layout ='wide')
st.title("EXTRACTING BUSINESS CARD DATA WITH 'OCR'")

with st.sidebar:
    
    st.image('Automate-Data-Extraction-from-Docuemnts-Software.jpg')
    select= option_menu('Main Menu',['Home','Upload & Modifying'])

if select == 'Home':
    st.image('bizcardX image.png')
    st.caption('Stored Data')
    mydb= psycopg2.connect(host='localhost',
                           user='postgres',
                           password='postgres',
                           database='BizCard_Data',
                           port='5432')
    cursor=mydb.cursor()

    #select_query
    select_query = 'SELECT * FROM BizCard_details'

    cursor.execute(select_query)
    table= cursor.fetchall()
    mydb.commit()

    table_df = pd.DataFrame(table, columns=('NAME','DESIGNATION','COMPANY_NAME','CONTACT','EMAIL','WEBSITE',
                                            'ADDRESS','PINCODE','IMAGE'))
    table_df
    

    

elif select =='Upload & Modifying':
    img = st.file_uploader('Upload The Image', type=['png','jpg','jpeg'])

    if img is not None:
        st.image(img,width=300)

        text_img,input_img= image_to_text(img)

        text_dict =extracted_text(text_img)

        if text_dict:
            st.success('TEXT IS EXTRACTED SUCCESSFULLY')

        df=pd.DataFrame(text_dict)

        #converting Image into bytes
        
        Image_bytes = io.BytesIO()
        input_img.save(Image_bytes,format='PNG')
        
        image_data = Image_bytes.getvalue()
        
        #creating dictionary
        data = {'IMAGE':[image_data]}
        
        df_1 = pd.DataFrame(data)
        
        concat_df = pd.concat([df,df_1],axis=1)
        st.dataframe(concat_df)

        button_1= st.button('SAVE')

        if button_1:
            mydb= psycopg2.connect(host='localhost',
                                   user='postgres',
                                   password='postgres',
                                   database='BizCard_Data',
                                   port='5432')
            cursor=mydb.cursor()
            
            #Table creation
            create_query ='''CREATE TABLE IF NOT EXISTS BizCard_details(name varchar(200),
                                                                        designation varchar(200),
                                                                        company__name varchar(200),
                                                                        contact varchar(200),
                                                                        email varchar(200),
                                                                        website text,
                                                                        address text,
                                                                        pincode varchar(200),
                                                                        image text)'''
            cursor.execute(create_query)
            mydb.commit()
            #insert query
            insert_query ='''insert into BizCard_details(name,
                                                        designation,
                                                        company__name,
                                                        contact,
                                                        email,
                                                        website,
                                                        address,
                                                        pincode,
                                                        image)
            
                                                        values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            datas = concat_df.values.tolist()[0]
            cursor.execute(insert_query,datas)
            mydb.commit
            #select_query
            select_query = 'SELECT * FROM bizcard_details'
            
            cursor.execute(select_query)
            table= cursor.fetchall()
            mydb.commit()
            
            table_df = pd.DataFrame(table, columns=('NAME','DESIGNATION','COMPANY_NAME','CONTACT','EMAIL','WEBSITE',
                                                    'ADDRESS','PINCODE','IMAGE'))

            st.success('EXTRACTED DATA SAVED SUCCESSFULLY')

    method = st.radio('Select The Process',['None','Modify'])
    
    if method == 'None':
        st.write('')

    elif method == 'Modify':
        mydb= psycopg2.connect(host='localhost',
                               user='postgres',
                               password='postgres',
                               database='BizCard_Data',
                               port='5432')
        cursor=mydb.cursor()
    
        #select_query
        select_query = 'SELECT * FROM BizCard_details'
    
        cursor.execute(select_query)
        table= cursor.fetchall()
        mydb.commit()
    
        table_df = pd.DataFrame(table, columns=('NAME','DESIGNATION','COMPANY_NAME','CONTACT','EMAIL','WEBSITE',
                                                'ADDRESS','PINCODE','IMAGE'))

        col1,col2 = st.columns(2)
        with col1:

            selected_name = st.selectbox('select the name',table_df['NAME'])

        df_3 = table_df[table_df['NAME'] ==selected_name]

        st.dataframe(df_3)

        df_4 = df_3.copy()

        

        col1,col2 =st.columns(2)
        with col1:
            mo_name = st.text_input('Name',df_3['NAME'].unique()[0])
            mo_desi = st.text_input('Designation',df_3['DESIGNATION'].unique()[0])
            mo_com_name = st.text_input('Company_Name',df_3['COMPANY_NAME'].unique()[0])
            mo_contact = st.text_input('Contact',df_3['CONTACT'].unique()[0])
            mo_email = st.text_input('Email',df_3['EMAIL'].unique()[0])

            df_4['NAME'] = mo_name
            df_4['DESIGNATION'] = mo_desi
            df_4['COMPANY_NAME'] =  mo_com_name
            df_4['CONTACT'] = mo_contact
            df_4['EMAIL'] = mo_email

        with col2:
            mo_webite = st.text_input('Website',df_3['WEBSITE'].unique()[0])
            mo_address = st.text_input('Address',df_3['ADDRESS'].unique()[0])
            mo_pincode = st.text_input('Pincode',df_3['PINCODE'].unique()[0])
            mo_image = st.text_input('Image',df_3['IMAGE'].unique()[0])

            df_4['WEBSITE'] = mo_webite
            df_4['ADDRESS'] = mo_address
            df_4['PINCODE'] = mo_pincode
            df_4['IMAGE'] = mo_image

        st.dataframe(df_4)
        
        col1,col2 =st.columns(2)
        with col1:
            button_3 = st.button('Modify')

        if button_3:
            mydb= psycopg2.connect(host='localhost',
                                   user='postgres',
                                   password='postgres',
                                   database='BizCard_Data',
                                   port='5432')
            cursor=mydb.cursor()

            cursor.execute(f"DELETE FROM BizCard_details WHERE NAME ='{selected_name}'")
            mydb.commit()


            #insert query
            insert_query ='''insert into BizCard_details(name,
                                                        designation,
                                                        company__name,
                                                        contact,
                                                        email,
                                                        website,
                                                        address,
                                                        pincode,
                                                        image)
            
                                                        values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
          
            datas = df_4.values.tolist()[0]
            cursor.execute(insert_query,datas)
            mydb.commit
            
            select_query
            select_query = 'SELECT * FROM BizCard_details'
            
            cursor.execute(select_query)
            table= cursor.fetchall()
            mydb.commit()
            
            table_df = pd.DataFrame(table, columns=('NAME','DESIGNATION','COMPANY_NAME','CONTACT','EMAIL','WEBSITE',
                                                    'ADDRESS','PINCODE','IMAGE'))


            st.success('EXTRACTED DATA MODIFIED SUCCESSFULLY')

            
        
    
