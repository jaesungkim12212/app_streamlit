import streamlit as st
import mysql.connector
import pandas as pd

# MySQL 서버에 연결하는 함수
def get_data_from_db(query, params=None, single_column=False):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="tim5312+@@705300",
        database="shopping_db"
    )
    mycursor = mydb.cursor()
    mycursor.execute(query, params)
    result = mycursor.fetchall()
    columns = [desc[0] for desc in mycursor.description]
    
    if single_column:
        df = pd.DataFrame(result, columns=['column'])
    else:
        df = pd.DataFrame(result, columns=columns)
        
    mydb.close()
    return df


# 상위 카테고리 목록을 가져오는 함수
def get_top_categories():
    query = "SELECT DISTINCT 상위카테고리 FROM new_products"
    df = get_data_from_db(query, single_column=True)
    return df['column'].tolist()

# 중간 카테고리 목록을 가져오는 함수
def get_middle_categories(top_category):
    query = "SELECT DISTINCT 중간카테고리 FROM new_products WHERE 상위카테고리 = %s"
    df = get_data_from_db(query, (top_category,), single_column=True)
    return df['column'].tolist()

# 하위 카테고리 목록을 가져오는 함수
def get_bottom_categories(top_category, middle_category):
    query = "SELECT DISTINCT 하위카테고리 FROM new_products WHERE 상위카테고리 = %s AND 중간카테고리 = %s"
    df = get_data_from_db(query, (top_category, middle_category), single_column=True)
    return df['column'].tolist()

# 선택한 카테고리의 상품 목록을 가져오는 함수
def get_products(top_category, middle_category, bottom_category):
    query = "SELECT * FROM new_products WHERE 상위카테고리 = %s AND 중간카테고리 = %s AND 하위카테고리 = %s"
    df = get_data_from_db(query, (top_category, middle_category, bottom_category))
    return df



# 사용자 구매내역을 기반으로 하위카테고리별 할인율이 가장 높은 상품을 추천하는 함수
def recommend_products(user_id):
    # 사용자가 구매한 하위카테고리 목록 가져오기
    query = """
    SELECT DISTINCT 상위카테고리, 중간카테고리, 하위카테고리
    FROM purchase_history
    WHERE 사용자ID = %s
    """
    purchased_categories = get_data_from_db(query, (user_id,))


    # 추천 상품 목록 초기화
    recommended_products = pd.DataFrame(columns=[
        '상위카테고리', '중간카테고리', '하위카테고리', '상품명', '할인가격', 
        '정가', '할인율'
    ]) # 사용자ID, 구매수량 제거


    # 각 하위카테고리별로 할인율이 가장 높은 상품 선택
    for _, row in purchased_categories.iterrows():
        top_category = row['상위카테고리']
        middle_category = row['중간카테고리']
        bottom_category = row['하위카테고리']
        

        query = """
        SELECT 상위카테고리, 중간카테고리, 하위카테고리, 상품명, 할인가격, 정가, 할인율
        FROM new_products 
        WHERE 상위카테고리 = %s AND 중간카테고리 = %s AND 하위카테고리 = %s
        ORDER BY 할인율 DESC 
        LIMIT 1
        """
        top_product = get_data_from_db(query, (top_category, middle_category, bottom_category))
    

        # 반환된 데이터가 비어있지 않은지 확인하고 추가
        if not top_product.empty:
            recommended_products = pd.concat([recommended_products, top_product], ignore_index=True)
        else:
            st.write(f"카테고리에 맞는 추천 상품이 없습니다: {top_category}, {middle_category}, {bottom_category}")
    
    return recommended_products


# Streamlit 앱
def main():
    st.title("할인 쇼핑 앱")
    
    # 세션 상태 초기화
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = None

    # 로그인 상태에 따라 페이지 결정
    if st.session_state['logged_in']:
        page = st.sidebar.selectbox("메뉴", ["홈 화면", "상품 목록", "마이페이지"])
        if page == "홈 화면":
            show_home_page()
        elif page == "상품 목록":
            show_product_list_page()
        elif page == "마이페이지":
            show_my_page()
    else:
        show_login_page()


# 사용자 ID 존재 여부 확인 함수
def user_id_exists(user_id):
    query = "SELECT COUNT(*) FROM purchase_history WHERE 사용자ID = %s"
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="tim5312+@@705300",
        database="shopping_db"
    )
    mycursor = mydb.cursor()
    mycursor.execute(query, (user_id,))
    result = mycursor.fetchone()
    mydb.close()
    return result[0] > 0


def show_login_page():
    st.header("로그인 화면")
    user_id = st.text_input("사용자 ID를 입력하세요:", "")

    if st.button("로그인"):
        if user_id:
            if user_id_exists(user_id):
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user_id
                #st.experimental_rerun()
                st.rerun()  # st.experimental_rerun()을 st.rerun()으로 교체
            else:
                st.warning("존재하지 않는 사용자 ID입니다.")
        else:
            st.warning("사용자 ID를 입력하세요.")



def show_home_page():
    st.header("홈 화면")

    # 사용자 ID 가져오기
    user_id = st.session_state['user_id']

    # 사용자에게 추천 상품 목록 보여주기
    st.subheader(f"{user_id} 님을 위한 추천 상품")
    recommended_products = recommend_products(user_id)


    # 디버깅: 추천 상품 출력
    st.write("추천 상품:", recommended_products)

    


def show_product_list_page():
    st.header("상품 목록")

    # 상위 카테고리 선택
    top_category = st.selectbox("상위 카테고리 선택", [""] + get_top_categories())

    if top_category:
        # 중간 카테고리 선택
        middle_category = st.selectbox("중간 카테고리 선택", [""] + get_middle_categories(top_category))

        if middle_category:
            # 하위 카테고리 선택
            bottom_category = st.selectbox("하위 카테고리 선택", [""] + get_bottom_categories(top_category, middle_category))

            if bottom_category:
                # 선택한 카테고리의 상품 목록 가져오기
                df = get_products(top_category, middle_category, bottom_category)

                # 중복 제거
                df = df.drop_duplicates()

                # 필요한 열만 선택
                df = df[['상위카테고리', '중간카테고리', '하위카테고리', '상품명', '할인가격', '정가', '할인율']]

                # 검색어 입력
                search_query = st.text_input("상품 검색", "")

                # 검색어에 따라 데이터 필터링
                if search_query:
                    df = df[df['상품명'].str.contains(search_query, case=False, na=False)]

                # 검색된 상품 개수 출력
                st.write(f"검색된 상품 개수: {len(df)}")

                if df.empty:
                    st.write("상품이 없습니다.")
                else:
                    st.write(df)
            else:
                st.write("하위 카테고리를 선택하세요.")
        else:
            st.write("중간 카테고리를 선택하세요.")
    else:
        st.write("상위 카테고리를 선택하세요.")
    

def show_my_page():
    st.header("마이페이지")
    user_id = st.session_state['user_id']
    st.write(f"{user_id} 님의 마이페이지입니다.")

    # 사용자 구매내역 가져오기
    user_id = st.session_state['user_id']
    query = """
    SELECT p.상품명, p.하위카테고리, p.정가, p.할인가격, ph.구매수량
    FROM purchase_history ph
    JOIN new_products p ON ph.상품명 = p.상품명
    WHERE ph.사용자ID = %s
    ORDER BY ph.구매수량 DESC
    """
    df = get_data_from_db(query, (user_id,))
    

    # 구매내역 출력
    st.subheader("구매내역")
    if df.empty:
        st.write("구매내역이 없습니다.")
    else:
        st.write(df)

if __name__ == "__main__":
    main()