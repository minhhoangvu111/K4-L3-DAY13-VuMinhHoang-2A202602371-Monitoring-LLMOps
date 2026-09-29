# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** 
- **MSSV:**
- **Lớp:** K4-L3A
- **Repository URL:**
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-<MSSV>`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | Chưa lưu kết quả baseline riêng trước CP1 | 100/100; 21 log records, 10 correlation IDs, 0 thiếu field, 0 PII leak | Chạy workload mới sau khi giữ log cũ làm baseline; evidence ở `evidence/02-log-validator.txt` |
| `validate_dashboard.py` | Chưa chạy | HỢP LỆ: 6/6 panel | Contract sáu panel đạt; dashboard runtime tại `/dashboard` |
| `pytest` | Chưa chạy | 25 passed | Chạy toàn bộ test sau thay đổi CP2 |
| Số traces hợp lệ | Chưa đo | Chưa tạo trong Langfuse | `.env` hiện chưa cấu hình public/secret key nên chưa có trace runtime |
| Số PII leak | | | |
| Latency P95 / TTFT P95 | | | |
| Retrieval success rate | | | |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware nhận `x-request-id` đúng định dạng `req-<8-hex>`, nếu thiếu/sai định dạng thì sinh ID mới; bind vào structlog contextvars, trả trong response header và body.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env`; log request/response cũng có timestamp, event, correlation ID và latency/TTFT, token, cost, quality.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor đệ quy scrub mọi chuỗi trong log event trước JSONL writer/renderer; pattern che email, số điện thoại Việt Nam, CCCD 12 số và thẻ thanh toán.
- **Cách kiểm chứng kết quả:** Workload sinh 10 correlation IDs; validator báo 21 records, 0 trường bắt buộc thiếu, 0 metadata thiếu và 0 PII leak (100/100). Evidence: `evidence/02-log-validator.txt`, `evidence/04-structured-log.txt`, `evidence/05-pii-redaction.txt`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Chưa có trace runtime; cần cấu hình key của project cá nhân `day13-k4-l3a-<MSSV>` trước khi chạy workload.
- **Cấu trúc root/retrieval/generation observations:** Code tạo root agent observation, child retriever `knowledge-retrieval` và generation `llm-generation`; generation ghi model, prompt metadata, usage và cost. Trace input/output giữ dạng độ dài/metadata, không capture prompt/output thô.
- **Cách nối trace với log:** `correlation_id` được đưa vào trace metadata; log request/response mang cùng ID.
- **Prompt name:** `day13-chat` (cấu hình mặc định).
- **Version/label baseline:** Chưa tạo trong Langfuse.
- **Version/label candidate:** Chưa tạo trong Langfuse.
- **Trace ID của mỗi version:** Chưa có vì Langfuse key chưa cấu hình.
- **Cách promote và rollback `production`:** Chưa thực hiện runtime; thao tác cần làm trong project cá nhân theo `docs/PROMPT_VERSIONING.md` sau khi cấu hình keys.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Contract `config/dashboard.yaml` đạt 6/6; dashboard HTML chạy tại `/dashboard`, đọc `data/logs.jsonl`, time range 60 phút, refresh 30 giây. Evidence: `evidence/11-dashboard-overview.html`.
- **SLO và lý do chọn:** 99.5% request thành công trong ≤3 giây trên cửa sổ 28 ngày; guardrails lấy từ ngưỡng dashboard và baseline.
- **Cách tính error budget:** 100% - 99.5% = 0.5%; với 10,000 request, budget tương ứng tối đa 50 request không đạt.
- **Ba alert và runbook tương ứng:** `ElevatedRequestErrorRate` → `docs/alerts.md#alert-1`; `HighRequestLatency` → `#alert-2`; `LowRetrievalSuccess` → `#alert-3`. Cả ba gửi Slack `#llmops-alerts`, có duration/severity/owner.

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
