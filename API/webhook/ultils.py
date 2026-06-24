import random


def generate_random_comment() -> str:
    """
    Tạo một comment ngẫu nhiên về ô tô bằng cách ghép các thành phần câu.
    Trả về một chuỗi comment tiếng Việt thực tế (có cả teencode).
    """
    subjects = [
        "em",
        "mình",
        "tui",
        "ae",
        "mọi người",
        "bác nào",
        "anh em",
        "các bác",
        "mn",
        "e",
    ]
    actions = [
        "mới mua",
        "đang chạy",
        "vừa chốt",
        "định múc",
        "đang cân nhắc",
        "mới lái thử",
        "đổi từ",
        "nên mua",
        "có ai dùng",
        "đang xài",
        "mới nhận xe",
        "vừa bán",
    ]
    cars = [
        "vf8",
        "cx5",
        "tucson",
        "xpander",
        "morning",
        "vios",
        "fadil",
        "sedona",
        "raize",
        "accent",
        "cx8",
        "santa fe",
        "ranger",
        "hilux",
        "fortuner",
        "corolla cross",
        "seltos",
        "civic",
        "mazda 3",
        "camry",
        "lux a",
        "lux sa",
    ]
    feelings_positive = [
        "chạy sướng quá",
        "ngon bổ rẻ",
        "chạy bốc phết",
        "nội thất đẹp lắm",
        "tiết kiệm xăng vl",
        "êm như ru",
        "k chê vào đâu đk",
        "quá xịn sò",
        "10 điểm không có nhưng",
        "ưng quá trời",
        "mượt mà phết",
        "đáng đồng tiền bát gạo",
    ]
    feelings_negative = [
        "máy yếu quá",
        "dịch vụ bảo hành tệ qa",
        "nội thất nhìn phèn",
        "hao xăng vl",
        "hay hư vặt",
        "gầm thấp quá",
        "giá cao mà đồ dỏm",
        "lái cứ rung rung",
        "cách âm kém",
        "đại lý chặt chém quá",
        "sơn mỏng dễ xước",
        "đi thì thích về thì sợ",
    ]
    feelings_neutral = [
        "thay nhớt loại j tốt hả",
        "giá bao nhiêu thì hợp lý",
        "nên chọn bản nào",
        "có ai tư vấn giúp ko",
        "so với đối thủ thì sao",
        "tầm giá bao nhiêu",
        "bản tiêu chuẩn hay cao cấp",
        "đăng kiểm mấy triệu",
        "bảo hiểm hết bao nhiêu",
    ]
    suffixes = [
        "ạ",
        ":v",
        "hehe",
        "hihi",
        "nhỉ",
        "vậy",
        "ha",
        "mọi người",
        "nè",
        "đây",
        "🔥",
        "👍",
        "",
    ]

    car = random.choice(cars)
    sentiment = random.choice(["positive", "negative", "neutral"])

    if sentiment == "positive":
        feeling = random.choice(feelings_positive)
        comment = f"{random.choice(subjects)} {random.choice(actions)} {car}, {feeling} {random.choice(suffixes)}"
    elif sentiment == "negative":
        feeling = random.choice(feelings_negative)
        comment = f"{random.choice(subjects)} {random.choice(actions)} {car}, {feeling} {random.choice(suffixes)}"
    else:
        feeling = random.choice(feelings_neutral)
        comment = f"{random.choice(subjects)} {random.choice(actions)} {car}, {feeling} {random.choice(suffixes)}"

    return comment
