# Alert rules và runbook

Các alert dưới đây theo triệu chứng người dùng/SLI, gửi tới Slack `#llmops-alerts`. Chỉ kích hoạt sau khi điều kiện duy trì đủ duration; correlation ID được dùng để nối log và trace.

## Alert 1 — ElevatedRequestErrorRate

- **Severity / duration:** critical / 5 phút.
- **Điều kiện:** error rate trên 2% trong 5 phút; mẫu số là request nhận được.
- **SLI/SLO:** fast successful requests, mục tiêu 99.5% trong 28 ngày; lỗi làm tiêu hao error budget.
- **Ảnh hưởng:** người dùng thường xuyên nhận lỗi thay vì câu trả lời.
- **Kiểm tra:** (1) xác nhận số request và lỗi trên dashboard; (2) lọc `request_failed` theo khoảng thời gian, phân loại `error_type`; (3) lấy `correlation_id`, mở trace cùng ID để thấy span lỗi.
- **Mitigation:** nếu lỗi theo retrieval, tạm chuyển sang fallback/general response; nếu lỗi tập trung ở bản phát hành mới, rollback bản đó; tiếp tục theo dõi error rate và thông báo trạng thái.
- **Owner:** LLMOps on-call. Config: `config/alert_rules.yaml`.

## Alert 2 — HighRequestLatency

- **Severity / duration:** warning / 10 phút.
- **Điều kiện:** latency P95 vượt 3,000 ms liên tục 10 phút.
- **SLI/SLO:** ngưỡng tốt của SLI là response thành công trong 3 giây.
- **Ảnh hưởng:** phản hồi chậm với phần request ở tail latency.
- **Kiểm tra:** (1) xác nhận P50/P95/P99 và TTFT trong panel latency; (2) xác định request chậm qua log `response_sent` và correlation ID; (3) mở trace và so thời lượng retrieval với generation.
- **Mitigation:** giảm concurrency/traffic không thiết yếu hoặc chuyển prompt/model sang cấu hình đã biết ổn định; nếu retrieval là span chậm, dùng cache/fallback; xác nhận P95 giảm trước khi đóng alert.
- **Owner:** API on-call. Config: `config/alert_rules.yaml`.

## Alert 3 — LowRetrievalSuccess

- **Severity / duration:** warning / 5 phút.
- **Điều kiện:** retrieval success dưới 90% trong 5 phút.
- **SLI/guardrail:** `retrieval_success_rate_pct_min: 90`.
- **Ảnh hưởng:** câu trả lời có thể thiếu ngữ cảnh hoặc dùng fallback.
- **Kiểm tra:** (1) xác nhận retrieval success và error breakdown; (2) lọc request có `tool_success=false`, lấy correlation ID; (3) mở trace để xác định retrieval timeout, lỗi truy vấn hay nguồn dữ liệu.
- **Mitigation:** chuyển sang fallback an toàn hoặc nguồn dự phòng, giảm tải truy vấn nếu có nghẽn, khôi phục đường retrieval sau khi kiểm tra health và thử request mẫu.
- **Owner:** Retrieval on-call. Config: `config/alert_rules.yaml`.

## Sau khi xử lý

Ghi thời điểm bắt đầu/kết thúc, phạm vi ảnh hưởng, metric, correlation ID, trace ID, root cause và hành động khắc phục trong incident note. Không đưa prompt/output thô chứa PII vào log hoặc runbook.
