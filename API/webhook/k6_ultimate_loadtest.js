import http from 'k6/http';
import { check, sleep } from 'k6';
import { SharedArray } from 'k6/data';

// =============================================================================
// CẢNH GIỚI 3: K6 (GRAFANA) - NGÔN NGỮ GO CỐT LÕI
// =============================================================================

// Cấu hình chiến dịch nã đạn
export const options = {
    // Kịch bản (Scenarios) ép tải Server
    scenarios: {
        tsunami_attack: {
            // Loại kịch bản: Bắn đúng số lượng RPS chỉ định, kệ cho server sống hay chết
            executor: 'constant-arrival-rate',
            
            // Số lượng "Đạn" (Requests) muốn bắn ra MỖI GIÂY
            rate: 2000, 
            
            timeUnit: '1s', // Đo lường rate theo mỗi 1 giây
            
            // Kéo dài cuộc tấn công trong bao lâu
            duration: '30s',
            
            // "Súng" (VUs - Virtual Users) được chuẩn bị sẵn trong ổ đạn để bắn
            preAllocatedVUs: 500,
            
            // Nếu server lag, có thể sinh thêm tối đa bao nhiêu VUs để nhồi thêm đạn
            maxVUs: 2000,
        },
    },
    // Giới hạn chịu đựng
    thresholds: {
        // Tỉ lệ lỗi HTTP không được vượt quá 1%
        http_req_failed: ['rate<0.01'], 
        // 95% request phải được trả về dưới 500ms
        http_req_duration: ['p(95)<500'], 
    },
};

// Đọc file dữ liệu JSON (Đọc bằng cơ chế SharedArray siêu tối ưu RAM của Go)
const commentsData = new SharedArray('Car Comments', function () {
    const f = JSON.parse(open('./million_car_comments.json'));
    return f; 
});

const URL = __ENV.PREDICT_URL || 'http://192.168.1.99:8000/predict';
const API_KEY = __ENV.API_TOKEN || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc4Mjg5MTYyN30.2jESTdblm481_w9TACwdE8xMgFFRw9nw-24Vj6zMnVY';

export default function () {
    // Rút ngẫu nhiên 1 bình luận
    const randomText = commentsData[Math.floor(Math.random() * commentsData.length)];
    
    const payload = JSON.stringify({
        text: randomText,
        timer: new Date().toISOString()
    });

    const params = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${API_KEY}`,
        },
        timeout: '15s',
    };

    // Bóp cò (Bắn Request)
    const res = http.post(URL, payload, params);

    // Kiểm tra đạn có trúng đích không (HTTP 200)
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}

/*
=============================================================================
TÀI LIỆU CÁCH SỬ DỤNG VŨ KHÍ k6
=============================================================================
Để chạy file này, bạn KHÔNG DÙNG Python hay Node.js. 
Bạn phải dùng k6 CLI (viết bằng Golang).

Bước 1: Mở Terminal, gõ lệnh kích hoạt:
    k6 run Api/webhook/k6_ultimate_loadtest.js

Bước 2: Cấu hình động:
Bạn không cần sửa code nếu muốn thay đổi thông số. Có thể truyền thẳng qua CLI:
    k6 run --vus 500 --duration 1m Api/webhook/k6_ultimate_loadtest.js

(Lệnh trên: Huy động 500 lính ảo, xả đạn liên tục trong 1 phút)

VÌ SAO ĐÂY LÀ CẢNH GIỚI CAO NHẤT?
- Bản thân k6 được biên dịch thành "Mã máy" (Machine Code) bằng ngôn ngữ Go.
- Go có công nghệ Goroutine (siêu vi luồng), nhẹ hơn Python hàng chục lần.
- Một máy Mac M1/M2 chạy k6 có thể dễ dàng tạo ra 30,000 - 50,000 RPS.
- k6 tự động in ra một bảng Báo Cáo (Summary) cực kỳ chi tiết ở cuối bài test, 
  chuẩn form của kỹ sư Performance Testing quốc tế!
=============================================================================
*/
