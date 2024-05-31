import pandas as pd
import mysql.connector
import re

# 엑셀 파일 경로
file_path = "C:\\Users\\jaesu\\Desktop\\complete.xlsx"

# 엑셀 파일 읽기
df = pd.read_excel(file_path)

# 데이터프레임 열 이름 출력 (확인용)
print("열 이름:", df.columns)

# 엑셀 파일의 열 이름 확인 후 변경
df = df.rename(columns={
    'top_category': '상위카테고리', 
    'middle_category': '중간카테고리',
    'bottom_category': '하위카테고리',
    'name': '상품명',
    'opt_price': '할인가격',
    'org_price': '정가',
    'sale_rate': '할인율',
    'review': '리뷰점수',
    'review_number': '리뷰개수',
    'ID': '사용자ID',
    '구매수량': '구매수량'
}) # 엑셀 파일의 열 이름과 MySQL 테이블의 열 이름이 일치하도록 해야함.


# 필요한 열만 선택
df_new_products = df[['상위카테고리', '중간카테고리', '하위카테고리', '상품명', '할인가격', '정가', '할인율', '리뷰점수', '리뷰개수', '사용자ID', '구매수량']]

# NaN 값을 적절한 기본값으로 대체
df_new_products = df_new_products.fillna({
    '상위카테고리': 'unknown',
    '중간카테고리': 'unknown',
    '하위카테고리': 'unknown',
    '상품명': 'unknown',
    '할인가격': 0,
    '정가': 0,
    '할인율': 0,
    '리뷰점수': 0,
    '리뷰개수': 0,
    '사용자ID': 'unknown',
    '구매수량': 0
})


# 쉼표 제거 및 숫자로 변환
df_new_products['할인가격'] = df_new_products['할인가격'].astype(str).str.replace(',', '').astype(float)
df_new_products['정가'] = df_new_products['정가'].astype(str).str.replace(',', '').astype(float)
df_new_products['할인율'] = df_new_products['할인율'].astype(str).str.replace(',', '').astype(float)
#df_new_products['상위카테고리'] = df_new_products['상위카테고리'].fillna('unknown')
#df_new_products['중간카테고리'] = df_new_products['중간카테고리'].fillna('unknown')
#df_new_products['하위카테고리'] = df_new_products['하위카테고리'].fillna('unknown')
#df_new_products['상품명'] = df_new_products['상품명'].fillna('unknown')

df_new_products['리뷰개수'] = df_new_products['리뷰개수'].astype(str).str.replace(',', '').astype(float).fillna(0).astype(int)  # NaN 값을 0으로 대체
df_new_products['구매수량'] = df_new_products['구매수량'].astype(str).str.replace(',', '').astype(float).fillna(0).astype(int)  # NaN 값을 0으로 대체
# 리뷰 열에서 숫자만 추출하여 float으로 변환, 빈 문자열은 0으로 대체
df_new_products['리뷰점수'] = df_new_products['리뷰점수'].apply(lambda x: float(re.sub(r'[^\d.]', '', str(x)) if re.sub(r'[^\d.]', '', str(x)) != '' else 0)).fillna(0)
# '사용자ID' 열의 NaN 값을 적절한 기본값으로 대체 (예: 'unknown' 또는 '0')
#df_new_products['사용자ID'] = df_new_products['사용자ID'].fillna('unknown')


# 엑셀 데이터 출력(확인용)
print(df_new_products.head())



# purchase_history 데이터프레임 생성
df_purchase_history = df[['사용자ID', '상품명', '구매수량', '상위카테고리', '중간카테고리', '하위카테고리']]
df_purchase_history = df_purchase_history.fillna({
    '사용자ID': 'unknown',
    '상품명': 'unknown',
    '구매수량': 0,
    '상위카테고리': 'unknown',
    '중간카테고리': 'unknown',
    '하위카테고리': 'unknown'
})



# purchase_history 데이터프레임 생성 및 필터링
#df_purchase_history = df_new_products[['사용자ID', '상품명', '구매수량']]
df_purchase_history = df_purchase_history[df_purchase_history['사용자ID'] != 'unknown']  # 사용자ID가 'unknown'인 데이터 제외



# MySQL 서버에 연결
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="tim5312+@@705300",
  database="shopping_db"
)

# 커서 생성
mycursor = mydb.cursor()


# new_products 테이블 생성 (한번만 실행 필요)
mycursor.execute("""
CREATE TABLE IF NOT EXISTS new_products (
    상위카테고리 VARCHAR(255),
    중간카테고리 VARCHAR(255),
    하위카테고리 VARCHAR(255),
    상품명 VARCHAR(255),
    할인가격 DECIMAL(10, 2),
    정가 DECIMAL(10, 2),
    할인율 DECIMAL(10, 2),
    리뷰점수 FLOAT,
    리뷰개수 INT,
    사용자ID VARCHAR(255),
    구매수량 INT
)
""")


# new_products 테이블에 데이터 삽입
for index, row in df_new_products.iterrows():
    sql = """
    INSERT INTO new_products (상위카테고리, 중간카테고리, 하위카테고리, 상품명, 할인가격, 정가, 할인율, 리뷰점수, 리뷰개수, 사용자ID, 구매수량)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    val = (
        row['상위카테고리'],
        row['중간카테고리'],
        row['하위카테고리'],
        row['상품명'],
        row['할인가격'],
        row['정가'],
        row['할인율'],
        row['리뷰점수'],
        row['리뷰개수'],
        row['사용자ID'],
        row['구매수량']
    )
    mycursor.execute(sql, val)

# purchase_history 테이블 생성 (한 번만 실행)
mycursor.execute("""
CREATE TABLE IF NOT EXISTS purchase_history (
    사용자ID VARCHAR(255),
    상품명 VARCHAR(255),
    구매수량 INT,
    상위카테고리 VARCHAR(255),
    중간카테고리 VARCHAR(255),
    하위카테고리 VARCHAR(255)
)
""")

# purchase_history 테이블에 데이터 삽입
for index, row in df_purchase_history.iterrows():
    sql = """
    INSERT INTO purchase_history (사용자ID, 상품명, 구매수량, 상위카테고리, 중간카테고리, 하위카테고리)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    val = (
        row['사용자ID'],
        row['상품명'],
        row['구매수량'],
        row['상위카테고리'],
        row['중간카테고리'],
        row['하위카테고리']
    )
    mycursor.execute(sql, val)

# 변경사항 저장
mydb.commit()

# 연결 종료
mydb.close()
