import json
import random

# Danh sách xe phổ biến
cars = [
    "vios",
    "accent",
    "city",
    "mazda 3",
    "cerato",
    "k3",
    "civic",
    "altis",
    "camry",
    "vinfast vf5",
    "vf8",
    "vf9",
    "fadil",
    "lux a",
    "lux sa",
    "santafe",
    "tucson",
    "crv",
    "cx5",
    "cx8",
    "ranger",
    "everest",
    "fortuner",
    "innova",
    "xpander",
    "veloz",
    "carnival",
    "sedona",
    "morning",
    "i10",
    "raize",
    "sonet",
    "creta",
    "seltos",
]

# Danh sách teencode
teencode_map = {
    "không": ["ko", "k", "kh", "khum", "hông", "hong"],
    "được": ["đc", "dc", "đk"],
    "quá": ["qá", "qa", "qúa", "wa"],
    "gì": ["j", "zì", "giề"],
    "rồi": ["r", "rùi", "zồi"],
    "biết": ["bít", "biếc"],
    "nhiều": ["nhìu"],
    "thích": ["thik", "thít", "thick"],
    "phải": ["phẩy", "fai"],
    "đẹp": ["đẹp", "đẹp vãi", "đỉnh", "xuất sắc"],
    "chạy": ["chại", "chạy"],
    "xe": ["xe", "xế", "vk 2", "zợ 2"],
    "ngon": ["ngon", "ngon choét", "đỉnh chóp", "hết nước chấm"],
    "chán": ["chán", "chán ốm", "tệ", "tởm", "phèn"],
    "mọi người": ["mn", "m.n", "các bác", "500ae", "ae"],
    "xin": ["xin", "hỏi"],
    "tư vấn": ["tv", "t.vấn"],
    "giá": ["giá", "rổ giá", "thiệt hại"],
    "mua": ["múc", "chốt", "xuống tiền"],
}

positive_templates = [
    "xe {car} này {chạy} {ngon} {quá} {mọi người} ơi",
    "mới {mua} con {car}, {đẹp} {không} tả {được}",
    "nội thất {car} {đẹp} {quá}, {thích} cực kì",
    "{mọi người} cho em hỏi {car} {giá} ntn, em {thích} {quá} {rồi}",
    "{car} {chạy} bốc {quá}, {không} chê vào đâu {được}",
    "{xe} {car} này tiết kiệm xăng {quá}, {ngon} {rồi}",
    "quyết định {mua} {car} là chuẩn bài, {ngon} {quá}",
    "công nghệ trên {car} {nhiều} {quá}, xài {không} hết",
    "{car} đi đầm chắc, cách âm {ngon} {không} các bác",
    "mới {mua} {car} {chạy} sướng {quá} {mọi người} ạ",
]

negative_templates = [
    "{car} {chạy} ồn {quá}, {chán} {không} chịu {được}",
    "mới {mua} {car} mà lỗi {nhiều} {quá}, {chán} hẳn",
    "dịch vụ bảo hành {car} {tệ} {quá}, {không} bao giờ {mua} lại",
    "{xe} {car} này hao xăng {quá}, {phải} làm sao đây {mọi người}",
    "nội thất {car} nhìn {phèn} {quá}, {không} {đẹp} như quảng cáo",
    "{car} đi hay hỏng vặt {quá}, {biết} thế {không} {mua}",
    "{mọi người} đừng {mua} {car} nhé, {chạy} {chán} {lắm}",
    "đi {car} mà ù tai {quá}, cách âm {không} {được} tốt",
    "màn hình {car} lag {quá}, xài bực mình {không} chịu {được}",
    "máy {car} yếu {quá}, vượt {xe} khác {không} nổi",
]

neutral_templates = [
    "{mọi người} cho em {xin} đánh giá về {car} với ạ",
    "tầm 600 củ thì nên {mua} {car} {không} {mọi người}?",
    "{car} thay nhớt loại {gì} thì tốt hả {mọi người}",
    "bác nào đang {chạy} {car} cho em {xin} ít review",
    "chuẩn bị lấy {car}, cần chú ý {gì} {không} {mọi người}",
    "{xe} {car} đi bảo dưỡng cấp 4 vạn hết khoảng bao nhiêu {gì}?",
    "{mọi người} tư vấn giúp em {car} bản tiêu chuẩn hay cao cấp",
    "có nên phủ ceramic cho {car} {không} các bác?",
    "em định {múc} {car} cũ đời 2019, giá bao nhiêu thì hợp lý",
    "xin địa chỉ gara uy tín sửa {car} ở Hà Nội",
]


def apply_teencode(text):
    words = text.split()
    new_words = []
    for word in words:
        clean_word = word.strip("?,.!")
        punct = word[len(clean_word) :]

        # Tìm teencode
        matched = False
        for k, v in teencode_map.items():
            if clean_word.lower() == k:
                # Thay thế với xác suất 70%
                if random.random() < 0.7:
                    new_clean_word = random.choice(v)
                    # Giữ nguyên case
                    if clean_word.istitle():
                        new_clean_word = new_clean_word.title()
                    elif clean_word.isupper():
                        new_clean_word = new_clean_word.upper()
                    new_words.append(new_clean_word + punct)
                else:
                    new_words.append(word)
                matched = True
                break

        if not matched:
            new_words.append(word)
    return " ".join(new_words)


def generate_data(num_samples=1000):
    data = []
    for _ in range(num_samples):
        car = random.choice(cars)
        sentiment = random.choice(["positive", "negative", "neutral"])

        if sentiment == "positive":
            template = random.choice(positive_templates)
        elif sentiment == "negative":
            template = random.choice(negative_templates)
        else:
            template = random.choice(neutral_templates)

        # fill template
        text = template.replace("{car}", car)
        for k in teencode_map.keys():
            if f"{{{k}}}" in text:
                text = text.replace(f"{{{k}}}", k)

        # Thêm vài từ thừa ngẫu nhiên
        if random.random() < 0.3:
            text += random.choice(
                [" ạ", " nhé", " nha", " hihi", " kk", " =))", " :v", " vãi"]
            )

        text = apply_teencode(text)

        # Thỉnh thoảng bỏ dấu câu cuối
        if text.endswith(("?", ".", "!")) and random.random() < 0.5:
            text = text[:-1]

        # Thỉnh thoảng viết thường hoàn toàn
        if random.random() < 0.4:
            text = text.lower()

        data.append({"text": text, "label": sentiment})
    return data


if __name__ == "__main__":
    mock_data = generate_data(1000)
    with open(
        "/Users/daoson/MyProject/API/car_sentiment_mock_data.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(mock_data, f, ensure_ascii=False, indent=4)
    print(f"Generated {len(mock_data)} items to car_sentiment_mock_data.json")
