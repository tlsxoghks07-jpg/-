import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import re
from collections import Counter

# 한글 폰트 설정 (윈도우: Malgun Gothic, 맥: AppleGothic)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 앱 메인 타이틀
st.title("📊 학과별 대학 생활습관 및 만족도 분석 대시보드")

# 1. CSV 파일 업로드 인터페이스
uploaded_file = st.file_uploader("캠퍼스 생활 데이터(CSV)를 업로드하세요.", type=['csv'])

if uploaded_file:
    # 2. 데이터 불러오기 및 미리보기
    df = pd.read_csv(uploaded_file)
    st.subheader("👀 업로드된 데이터 미리보기")
    st.dataframe(df.head())  # 상위 5개 행 미리보기

    # 3. 데이터 전처리 (결측치 및 이상치 처리)
    initial_count = len(df)

    # 결측치(NaN)가 포함된 행 제거
    df_cleaned = df.dropna().copy()

    # '만족도' 열을 숫자(numeric) 타입으로 강제 변환 (문자가 섞여 있으면 NaN으로 처리)
    df_cleaned['만족도'] = pd.to_numeric(df_cleaned['만족도'], errors='coerce')

    # 변환 과정에서 생성된 결측치 제거
    df_cleaned = df_cleaned.dropna(subset=['만족도'])

    # 만족도가 1~10점 사이인 정상 데이터만 유지
    df_cleaned = df_cleaned[(df_cleaned['만족도'] >= 1) & (df_cleaned['만족도'] <= 10)]

    # 전처리 제외 건수 표시
    excluded_count = initial_count - len(df_cleaned)
    st.info(f"**전처리 결과:** 총 {initial_count}건 중 데이터 누락 및 이상치 {excluded_count}건 제외 (현재 분석 대상: {len(df_cleaned)}건)")

    # 4. 학과 선택 필터 구현
    st.divider()
    major_list = ["전체"] + sorted(list(df_cleaned['학과'].unique()))
    selected_major = st.selectbox("🎯 분석할 학과를 선택하세요:", major_list)

    # 선택된 학과에 맞춰 데이터 필터링
    if selected_major == "전체":
        filtered_df = df_cleaned
        st.subheader("📌 전체 학과 통합 분석 결과")
    else:
        filtered_df = df_cleaned[df_cleaned['학과'] == selected_major]
        st.subheader(f"📌 [{selected_major}] 전용 분석 결과")

        # [추가 기능] 선택한 학과에 속한 학생들의 데이터만 따로 모아서 보여주기
        with st.expander(f"📁 {selected_major} 소속 학생 원본 데이터 보기"):
            st.dataframe(filtered_df)

    # 데이터가 비어있는 경우 예외 처리
    if len(filtered_df) == 0:
        st.warning(f"'{selected_major}'에 해당하는 데이터가 존재하지 않습니다.")
    else:
        # 5. 평균 만족도 표시 (학과 선택에 따라 동적 변경)
        avg_satisfaction = filtered_df['만족도'].mean()
        st.markdown(f"### 🎯 [{selected_major}] 평균 학교생활 만족도")
        st.metric(label="만족도 (10점 만점)", value=f"{avg_satisfaction:.2f}점")

        # 6. 막대그래프: 생활습관 차이 분석
        st.divider()
        st.subheader("📈 생활습관 평균 시간 비교 (막대그래프)")
        habit_means = filtered_df[['공부시간', '수면시간', '스마트폰']].mean().reset_index()
        habit_means.columns = ['항목', '평균시간(시간)']

        fig_bar, ax_bar = plt.subplots(figsize=(8, 4))
        sns.barplot(data=habit_means, x='항목', y='평균시간(시간)', ax=ax_bar, palette='Pastel1')
        ax_bar.set_title(f"[{selected_major}] 주요 생활습관 평균 시간")
        st.pyplot(fig_bar)

        # 7. 산점도: 생활습관과 만족도의 관련성 분석
        st.divider()
        st.subheader("📍 생활습관과 만족도의 상관관계 (산점도)")
        x_axis = st.radio("만족도와 비교할 요인을 선택하세요:", ['공부시간', '수면시간', '스마트폰'], horizontal=True)

        fig_scatter, ax_scatter = plt.subplots(figsize=(8, 4))
        sns.scatterplot(data=filtered_df, x=x_axis, y='만족도', ax=ax_scatter, color='cornflowerblue', alpha=0.7)
        ax_scatter.set_title(f"[{selected_major}] {x_axis} vs 학교생활 만족도")
        st.pyplot(fig_scatter)

        # 8. 워드클라우드: 한 줄 의견 주요 단어 분석
        st.divider()
        st.subheader("☁️ 학생들의 한 줄 의견 (워드클라우드)")
        text_data = " ".join(filtered_df['한줄의견'].astype(str).tolist())

        if text_data.strip():
            wc = WordCloud(font_path='malgun.ttf', background_color='white', width=800, height=400).generate(text_data)
            fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
            ax_wc.imshow(wc, interpolation='bilinear')
            ax_wc.axis('off')
            st.pyplot(fig_wc)
        else:
            st.write("해당 학과에 표시할 의견 데이터가 없습니다.")

        # 9. 한 줄 의견 심층 분석 (상위 단어 TOP 10 및 긍/부정 분석)
        st.divider()
        st.subheader("📝 한 줄 의견 심층 분석 (상위 단어 및 감성 분석)")

        if text_data.strip():
            # 한글 단어 추출 (2글자 이상)
            words = re.findall(r'[가-힣]{2,}', text_data)
            stopwords = {'어요', '이에요', '에서', '그리고', '하지만', '것같아요', '정도', '조금', '너무', '자주'}
            filtered_words = [w for w in words if w not in stopwords]

            # 상위 10개 단어 빈도수 계산
            word_counts = Counter(filtered_words).most_common(10)

            if word_counts:
                df_words = pd.DataFrame(word_counts, columns=['단어', '빈도수'])

                # 상위 10개 단어 막대그래프
                fig_top10, ax_top10 = plt.subplots(figsize=(10, 4))
                sns.barplot(data=df_words, x='단어', y='빈도수', ax=ax_top10, palette='Blues_r')
                ax_top10.set_title(f"[{selected_major}] 한 줄 의견 상위 단어 TOP 10")
                plt.xticks(rotation=45)
                st.pyplot(fig_top10)

                # 긍정 / 부정 단어 사전 기반 분류
                positive_keywords = {'좋', '예뻐', '도움', '만족', '편해', '최고', '알차', '뿌듯', '친절', '유익'}
                negative_keywords = {'힘들', '피곤', '부족', '어려', '지쳐', '스트레스', '과제', '불편', '졸려', '길어'}

                pos_count = 0
                neg_count = 0

                for comment in filtered_df['한줄의견'].astype(str):
                    for pk in positive_keywords:
                        if pk in comment:
                            pos_count += comment.count(pk)
                    for nk in negative_keywords:
                        if nk in comment:
                            neg_count += comment.count(nk)

                # 긍정/부정 등장 횟수 메트릭 출력
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="😊 긍정 성향 단어 감지 횟수", value=f"{pos_count}회")
                with col2:
                    st.metric(label="😞 부정 성향 단어 감지 횟수", value=f"{neg_count}회")

                # 긍부정 비교 막대그래프
                fig_sentiment, ax_sentiment = plt.subplots(figsize=(6, 3))
                sentiment_df = pd.DataFrame({
                    '감성 성향': ['긍정 성향', '부정 성향'],
                    '등장 횟수': [pos_count, neg_count]
                })
                sns.barplot(data=sentiment_df, x='감성 성향', y='등장 횟수', ax=ax_sentiment, palette=['#66b3ff', '#ff9999'])
                ax_sentiment.set_title(f"[{selected_major}] 감성 성향 비교")
                st.pyplot(fig_sentiment)
            else:
                st.write("추출된 유의미한 단어가 부족합니다.")
        else:
            st.write("분석할 한 줄 의견 데이터가 없습니다.")