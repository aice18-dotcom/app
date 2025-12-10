import os
from datetime import datetime
import textwrap

import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


# -----------------------------
# 기본 설정 & 상태 초기화
# -----------------------------
st.set_page_config(
    page_title="예산 장보기 미션",
    page_icon="🛒",
    layout="wide",
)

if "page" not in st.session_state:
    st.session_state.page = "mission"  # mission, shop, result

if "mission" not in st.session_state:
    st.session_state.mission = None

if "budget" not in st.session_state:
    st.session_state.budget = 0

if "cart" not in st.session_state:
    st.session_state.cart = []  # [{"name":..., "price":..., "image_url":...}, ...]

if "reason" not in st.session_state:
    st.session_state.reason = ""


# -----------------------------
# 미션 / 예산 설정
# -----------------------------
MISSIONS = {
    "절약형 장보기 (예산 10,000원)": 10_000,
    "균형 잡힌 장보기 (예산 20,000원)": 20_000,
    "풍성한 장보기 (예산 30,000원)": 30_000,
}
# 선생님이 원하면 위 딕셔너리를 수정해서 미션과 예산을 바꿀 수 있습니다.


# -----------------------------
# 유틸 함수
# -----------------------------
def load_products(csv_path: str = "products.csv") -> pd.DataFrame:
    """
    products.csv 파일을 불러옵니다.
    예상 컬럼명: 품명, 가격, 이미지url (또는 name, price, image_url)
    """
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except FileNotFoundError:
        st.error(
            f"'products.csv' 파일을 찾을 수 없습니다. "
            f"앱과 같은 폴더에 'products.csv'를 넣어 주세요."
        )
        return pd.DataFrame()

    return df


def get_column_name(df: pd.DataFrame, kor: str, eng: str, label: str) -> str:
    """
    한국어 컬럼명과 영어 컬럼명 둘 다 지원.
    예: kor='품명', eng='name'
    """
    if kor in df.columns:
        return kor
    if eng in df.columns:
        return eng
    st.error(f"products.csv에 '{kor}' 또는 '{eng}' 열이 필요합니다. ({label})")
    st.stop()


def add_to_cart(name: str, price: float, image_url: str | None = None):
    st.session_state.cart.append(
        {"name": name, "price": float(price), "image_url": image_url}
    )


def calc_cart_total() -> float:
    return sum(item["price"] for item in st.session_state.cart)


def create_submission_png(
    mission: str,
    budget: float,
    cart: list[dict],
    reason_text: str,
) -> str:
    """
    제출 내용을 PNG 이미지로 생성하고 파일 경로를 반환합니다.
    """
    # 텍스트 구성
    lines = []
    lines.append(f"미션: {mission}")
    lines.append(f"예산: {int(budget):,}원")
    lines.append("")
    lines.append("▶ 구매한 물품")
    if cart:
        for item in cart:
            lines.append(f"- {item['name']} ({int(item['price']):,}원)")
    else:
        lines.append("- (구매한 물품 없음)")
    lines.append("")
    lines.append("▶ 구매 이유")
    # 구매 이유는 줄바꿈 및 텍스트 래핑
    wrap_width = 30
    for para in reason_text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        for wrapped in textwrap.wrap(para, width=wrap_width):
            lines.append(wrapped)

    # 이미지 크기 설정 (줄 수에 따라 높이 조절)
    margin = 40
    line_height = 30
    width = 800
    height = margin * 2 + line_height * (len(lines) + 3)

    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # 기본 폰트 사용 (시스템 폰트 설정이 필요하면 여기서 수정)
    font = ImageFont.load_default()

    y = margin
    for line in lines:
        draw.text((margin, y), line, fill="black", font=font)
        y += line_height

    # 저장 폴더
    save_dir = "submissions"
    os.makedirs(save_dir, exist_ok=True)
    filename = f"submission_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(save_dir, filename)
    img.save(filepath, format="PNG")

    return filepath


# -----------------------------
# 화면 1: 미션(예산) 선택 화면
# -----------------------------
def show_mission_page():
    st.title("🧾 예산 장보기 미션")
    st.subheader("1. 미션(예산) 선택하기")

    st.write("학생은 아래 세 가지 미션 중 하나를 선택하여 장보기를 진행합니다.")

    mission = st.radio(
        "원하는 미션을 선택하세요.",
        options=list(MISSIONS.keys()),
        index=0,
    )

    budget = MISSIONS[mission]

    st.info(f"선택한 미션: **{mission}**  \n예산: **{budget:,}원**")

    if st.button("미션 선택 완료 ➜ 쇼핑하러 가기"):
        st.session_state.mission = mission
        st.session_state.budget = budget
        st.session_state.page = "shop"


# -----------------------------
# 화면 2: 쇼핑(물품 선택) 화면
# -----------------------------
def show_shop_page():
    st.title("🛒 쇼핑 화면")
    st.subheader("2. 물품 선택하기")

    if st.session_state.mission is None:
        st.warning("먼저 미션을 선택해주세요.")
        if st.button("미션 선택 화면으로 돌아가기"):
            st.session_state.page = "mission"
        return

    st.write(f"**현재 미션:** {st.session_state.mission}")
    st.write(f"**예산:** {int(st.session_state.budget):,}원")

    df = load_products("products.csv")
    if df.empty:
        return

    # 컬럼 이름 매핑 (품명 / 가격 / 이미지url)
    name_col = get_column_name(df, "품명", "name", "품명(상품명)")
    price_col = get_column_name(df, "가격", "price", "가격")
    image_col = None
    if "이미지url" in df.columns:
        image_col = "이미지url"
    elif "이미지URL" in df.columns:
        image_col = "이미지URL"
    elif "image_url" in df.columns:
        image_col = "image_url"

    # 상품 목록 표시
    st.markdown("### 상품 목록")
    for idx, row in df.iterrows():
        cols = st.columns([1, 3, 1])
        with cols[0]:
            if image_col is not None and pd.notna(row[image_col]):
                try:
                    st.image(
                        row[image_col],
                        use_column_width=True,
                    )
                except Exception:
                    st.write("(이미지를 불러올 수 없습니다)")
            else:
                st.write("(이미지 없음)")

        with cols[1]:
            st.markdown(f"**{row[name_col]}**")
            try:
                price_value = float(row[price_col])
            except ValueError:
                price_value = 0
            st.write(f"가격: {int(price_value):,}원")

        with cols[2]:
            if st.button("담기", key=f"add_{idx}"):
                add_to_cart(
                    name=row[name_col],
                    price=price_value,
                    image_url=row[image_col] if image_col else None,
                )
                st.success(f"장바구니에 '{row[name_col]}'을(를) 담았습니다.")

        st.markdown("---")

    # 장바구니 요약
    st.markdown("### 🧺 장바구니")
    cart = st.session_state.cart
    total = calc_cart_total()

    if cart:
        cart_df = pd.DataFrame(cart)
        cart_df_display = cart_df[["name", "price"]].rename(
            columns={"name": "품명", "price": "가격"}
        )
        cart_df_display["가격"] = cart_df_display["가격"].astype(int)
        st.dataframe(cart_df_display, use_container_width=True)
        st.write(f"**합계:** {int(total):,}원")
        remaining = st.session_state.budget - total
        if remaining >= 0:
            st.success(f"남은 예산: {int(remaining):,}원")
        else:
            st.error(f"예산을 {int(-remaining):,}원 초과했습니다!")
    else:
        st.write("장바구니가 비어 있습니다.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("◀ 미션 선택 화면으로 돌아가기"):
            st.session_state.page = "mission"

    with col2:
        if st.button("구매하기 ➜ 결과 화면으로 이동"):
            if not cart:
                st.warning("장바구니에 물품을 한 개 이상 담아주세요.")
            else:
                st.session_state.page = "result"


# -----------------------------
# 화면 3: 결과(제출) 화면
# -----------------------------
def show_result_page():
    st.title("📋 결과 화면")
    st.subheader("3. 구매 결과 확인 및 이유 작성")

    if st.session_state.mission is None:
        st.warning("먼저 미션을 선택하고 쇼핑을 완료해주세요.")
        if st.button("미션 선택 화면으로 가기"):
            st.session_state.page = "mission"
        return

    st.write(f"**미션:** {st.session_state.mission}")
    st.write(f"**예산:** {int(st.session_state.budget):,}원")

    cart = st.session_state.cart
    total = calc_cart_total()
    remaining = st.session_state.budget - total

    st.markdown("### 🧺 내가 구매한 물품")
    if cart:
        cart_df = pd.DataFrame(cart)
        cart_df_display = cart_df[["name", "price"]].rename(
            columns={"name": "품명", "price": "가격"}
        )
        cart_df_display["가격"] = cart_df_display["가격"].astype(int)
        st.dataframe(cart_df_display, use_container_width=True)
        st.write(f"**합계:** {int(total):,}원")
        if remaining >= 0:
            st.success(f"남은 예산: {int(remaining):,}원")
        else:
            st.error(f"예산을 {int(-remaining):,}원 초과했습니다!")
    else:
        st.write("구매한 물품이 없습니다.")

    st.markdown("### ✏️ 구매 이유 작성")
    st.session_state.reason = st.text_area(
        "왜 이렇게 구매했는지 이유를 적어보세요.",
        value=st.session_state.reason,
        height=200,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("◀ 쇼핑 화면으로 돌아가기"):
            st.session_state.page = "shop"

    with col2:
        if st.button("제출 (PNG로 출력)"):
            if not st.session_state.reason.strip():
                st.warning("구매 이유를 입력해주세요.")
            else:
                filepath = create_submission_png(
                    mission=st.session_state.mission,
                    budget=st.session_state.budget,
                    cart=cart,
                    reason_text=st.session_state.reason,
                )
                with open(filepath, "rb") as f:
                    png_bytes = f.read()

                st.success("제출이 완료되었습니다! 아래 버튼을 눌러 PNG를 다운로드하세요.")
                st.download_button(
                    label="결과 PNG 다운로드",
                    data=png_bytes,
                    file_name=os.path.basename(filepath),
                    mime="image/png",
                )


# -----------------------------
# 메인
# -----------------------------
def main():
    if st.session_state.page == "mission":
        show_mission_page()
    elif st.session_state.page == "shop":
        show_shop_page()
    elif st.session_state.page == "result":
        show_result_page()
    else:
        st.session_state.page = "mission"
        show_mission_page()


if __name__ == "__main__":
    main()
