-- =============================================================================
-- CẢNH GIỚI TỐI THƯỢNG CỦA MỌI CẢNH GIỚI: VŨ KHÍ HẠT NHÂN WRK (Ngôn ngữ LUA + C)
-- =============================================================================
-- Bản thân 'wrk' là một cỗ máy hủy diệt được viết 100% bằng C thuần túy để tối 
-- ưu hóa tận xương tủy nhân Linux/Unix. 
-- Kịch bản bên dưới được viết bằng LUA để "bơm đạn" (payload) cho nòng súng C.

-- 1. Nạp file dữ liệu khổng lồ vào RAM (Chỉ nạp 1 lần duy nhất lúc khởi động)
local json_file = io.open("Api/webhook/million_car_comments.json", "r")
local content = json_file:read("*all")
json_file:close()

-- LUA không có sẵn hàm parse JSON siêu tốc, để giữ cho file này "sạch" và "nhanh",
-- ta sẽ dùng Regex pattern để bóc tách thô (hacky way) các câu comment ra khỏi JSON.
-- Vì mục tiêu của 'wrk' là BẮN NHANH CHỨ KHÔNG PHẢI XỬ LÝ LỌC LÕI NGÔN NGỮ.
local comments = {}
for comment in string.gmatch(content, '"([^"]+)"') do
    -- Bỏ qua các chuỗi không phải là comment (như móc nhọn, dấu phẩy)
    if string.len(comment) > 5 then
        table.insert(comments, comment)
    end
end
print(string.format("Đã nạp thành công %d viên đạn (bình luận) vào nòng súng LUA!", #comments))

-- Đặt Authorization Key
local API_KEY = os.getenv("N8N_API_KEY") or "matgroup_n8n_secret_2026"

-- =============================================================================
-- HÀM NÀY ĐƯỢC GỌI TRƯỚC MỖI LẦN BÓP CÒ (Sinh ra từng Request)
-- =============================================================================
request = function()
    -- Bốc ngẫu nhiên 1 viên đạn
    local random_index = math.random(1, #comments)
    local text = comments[random_index]
    
    -- Lấy thời gian thực
    local timer = os.date("!%Y-%m-%d %H:%M:%S")

    -- Ghép tay chuỗi JSON (Ghép chuỗi tĩnh trong C/LUA luôn nhanh hơn Parse Object)
    local payload = string.format('{"text": "%s", "timer": "%s"}', text, timer)

    -- Lắp đạn vào súng
    local headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " .. API_KEY
    
    return wrk.format("POST", "/webhook/test1", headers, payload)
end

-- =============================================================================
-- TÀI LIỆU KÍCH HOẠT VŨ KHÍ HẠT NHÂN WRK
-- =============================================================================
-- Để bắn thử vũ khí này, bạn mở Terminal và gõ:
-- 
-- wrk -t12 -c400 -d30s -s Api/webhook/wrk_nuclear_bomb.lua http://192.168.1.99:56781
--
-- GIẢI THÍCH THÔNG SỐ:
-- -t12 : Dùng 12 luồng vật lý của CPU (Threads).
-- -c400: Giữ 400 kết nối HTTP luôn mở xuyên suốt (Connections).
-- -d30s: Nã liên tục trong 30 giây (Duration).
-- -s   : Nạp viên đạn LUA ở trên vào súng.
--
-- TẠI SAO WRK ĐƯỢC GỌI LÀ VŨ KHÍ HẠT NHÂN?
-- Trong khi Python chật vật đạt 2,000 RPS, Node.js đạt 10,000 RPS, Golang đạt 40,000 RPS...
-- Thì 'wrk' (viết bằng C) dễ dàng đạt TỪ 100,000 ĐẾN 500,000 RPS trên một máy Mac!
-- Nó tàn bạo đến mức: Nếu bạn chạy 'wrk', nó có thể đánh sập chính Card Mạng (NIC) 
-- hoặc Router WiFi của bạn trước cả khi Server đối phương kịp chết!
-- Dùng cẩn thận!
-- =============================================================================
