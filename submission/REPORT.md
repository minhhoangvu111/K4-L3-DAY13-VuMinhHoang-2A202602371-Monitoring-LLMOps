# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Vũ Minh Hoàng
- **MSSV:** 2A202602371
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/minhhoangvu111/K4-L3-DAY13-VuMinhHoang-2A202602371-Monitoring-LLMOps
- **Commit SHA cuối:** `e906f35d33966caab1b5aaff4cf59384c65eb40d` (HEAD trước các cập nhật hiện tại; cần cập nhật sau khi commit/push)
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602371`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/16-test-results.txt` |
| Log validator | `evidence/02-log-validator.txt` |
| Dashboard validator | `evidence/03-dashboard-validator.txt` |
| Structured log | `evidence/04-structured-log.txt` |
| PII redaction | `evidence/05-pii-redaction.txt` |
| Trace list | `evidence/15-langfuse-trace-audit.txt` (live API audit) |
| Trace waterfall | `evidence/15-langfuse-trace-audit.txt` (root AGENT với RETRIEVER và GENERATION) |
| Trace metadata | `evidence/15-langfuse-trace-audit.txt` |
| Prompt versions | Trace test dùng `local-v1` do remote prompt fetch timeout; chưa có bằng chứng managed versions |
| Prompt rollback | Chưa thực hiện; chưa có ảnh evidence |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.txt` |
| Incident log | `evidence/13-incident-log.txt` |
| Incident trace | `evidence/14-incident-trace.txt` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | Chưa lưu kết quả baseline riêng trước CP1 | 100/100; 93 log records, 46 correlation IDs, 0 thiếu field, 0 PII leak | Kết quả sau workload challenge; evidence ở `evidence/02-log-validator.txt` |
| `validate_dashboard.py` | Chưa chạy | HỢP LỆ: 6/6 panel | Contract sáu panel đạt; dashboard runtime tại `/dashboard` |
| `pytest` | Chưa lưu kết quả baseline riêng trước CP1 | 26 passed | Chạy toàn bộ suite sau cập nhật instrumentation; output ở `evidence/16-test-results.txt` |
| Số traces hợp lệ | Chưa đo | 1 trace được xác nhận qua Langfuse API, gồm 3 observations | Trace ID `8aae047ae870e628b47a5f04de161fe6`; evidence ở `evidence/15-langfuse-trace-audit.txt` |
| Số PII leak | Chưa đo | 0 trong validator log và trace audit mẫu | Synthetic email/điện thoại được che trước khi xuất trace |
| Latency P95 / TTFT P95 | Baseline P95 168.3 ms | Challenge latency P95 2712.2 ms; TTFT của request được chọn 63 ms | P95 challenge vượt threshold 2000 ms, chưa vượt SLO 3000 ms; không suy diễn TTFT P95 từ một request |
| Retrieval success rate | Chưa đo | 100% (5/5 request challenge) | Mỗi response challenge có `tool_success=true` |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware nhận `x-request-id` đúng định dạng `req-<8-hex>`, nếu thiếu/sai định dạng thì sinh ID mới; bind vào structlog contextvars, trả trong response header và body.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env`; log request/response cũng có timestamp, event, correlation ID và latency/TTFT, token, cost, quality.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor đệ quy scrub mọi chuỗi trong log event trước JSONL writer/renderer; pattern che email, số điện thoại Việt Nam, CCCD 12 số và thẻ thanh toán.
- **Cách kiểm chứng kết quả:** Validator gần nhất báo 93 records, 46 correlation IDs, 0 trường bắt buộc thiếu, 0 metadata thiếu và 0 PII leak (100/100). Evidence: `evidence/02-log-validator.txt`, `evidence/04-structured-log.txt`, `evidence/05-pii-redaction.txt`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Keys trong `.env` đã được xác thực với Langfuse (`auth_check=True`); một request audit riêng tạo trace `8aae047ae870e628b47a5f04de161fe6`. Evidence đã loại credentials tại `evidence/15-langfuse-trace-audit.txt`.
- **Cấu trúc root/retrieval/generation observations:** Root `AGENT lab-agent-run` có child `RETRIEVER retrieve-context` và `GENERATION generate-response`. Trace ghi model, token usage, cost, environment, tags, prompt metadata; query, context và answer được scrub PII và giới hạn độ dài.
- **Cách nối trace với log:** `correlation_id` trong log và trace metadata khớp (`req-4d00b84f` cho audit trace; `req-5e15d214` cho challenge lịch sử).
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** Chưa xác nhận managed version; audit trace dùng `local-v1`, label cấu hình `production`, nguồn `local-fallback` do lần gọi prompt Cloud timeout.
- **Version/label candidate:** Chưa tạo/xác nhận trong Langfuse.
- **Trace ID của mỗi version:** Managed prompt trace chưa có; trace audit hiện có là `8aae047ae870e628b47a5f04de161fe6` với local fallback.
- **Cách promote và rollback `production`:** Chưa thực hiện; chưa có evidence. Quy trình dự kiến theo `docs/PROMPT_VERSIONING.md` sau khi truy cập được managed prompt trong project.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Contract `config/dashboard.yaml` đạt 6/6; dashboard HTML chạy tại `/dashboard`, đọc `data/logs.jsonl`, time range 60 phút, refresh 30 giây. Ảnh overview được kết xuất từ log runtime thực tế: `evidence/11-dashboard-overview.png`.
- **SLO và lý do chọn:** 99.5% request thành công trong ≤3 giây trên cửa sổ 28 ngày; guardrails lấy từ ngưỡng dashboard và baseline.
- **Cách tính error budget:** 100% - 99.5% = 0.5%; với 10,000 request, budget tương ứng tối đa 50 request không đạt.
- **Ba alert và runbook tương ứng:** `ElevatedRequestErrorRate` → `docs/alerts.md#alert-1`; `HighRequestLatency` → `#alert-2`; `LowRetrievalSuccess` → `#alert-3`. Cả ba gửi Slack `#llmops-alerts`, có duration/severity/owner.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1` (cohort K4; file challenge gốc được giữ nguyên và không đưa vào Git).
- **Khoảng thời gian điều tra:** 2026-09-29 09:30:34–09:30:45 UTC (response timestamps; latest run from the attached file).
- **Triệu chứng từ metrics:** 5 request của feature `monitoring` có latency P95 2712.2 ms, vượt challenge threshold 2000 ms; baseline 10 request có P95 168.3 ms. `load_test.py` ghi round-trip 12.77–15.48 giây khi chạy concurrency 5; metric `response_sent.latency_ms` chưa vượt SLO 3000 ms.
- **Log line và correlation ID liên quan:** `request_received` và `response_sent` cùng `req-5e15d214`; response latency 2715 ms, `tool_name=retrieval`, `tool_success=true`.
- **Trace ID và span gây ảnh hưởng:** Request challenge lịch sử `req-5e15d214` chạy trước khi cấu hình keys nên không có trace ID; không thể gắn trace audit mới vào incident cũ. Trace audit sau đó xác nhận cấu trúc retrieval/generation tại `evidence/15-langfuse-trace-audit.txt`.
- **Root cause:** Challenge bật incident `rag_slow`; retrieval giả lập chờ thêm 2.5 giây trong `app/mock_rag.py`, làm tăng latency của cả năm request challenge.
- **Fix action:** Tắt incident sau workload; health check xác nhận `rag_slow: false`.
- **Preventive measure:** Cảnh báo P95 trên ngưỡng và kiểm tra retrieval health; Langfuse tracing hiện bật để các request mới có retrieval child span tra cứu theo correlation ID.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Chỉ đưa query/context/answer đã scrub và rút gọn vào trace; user ID và session ID được băm để giữ khả năng nhóm trace mà giảm lộ dữ liệu cá nhân.
- **Một lỗi/blocker đã gặp:** Máy Windows dùng kho CA không được Python HTTP client tin cậy mặc định trong môi trường chạy này; lần prompt fetch 2 giây bị timeout và dùng fallback.
- **Cách tìm nguyên nhân và xử lý:** Xác thực keys bằng `auth_check`, bổ sung kho CA gốc Windows cho lần audit HTTPS, sau đó truy vấn observations bằng Langfuse CLI. Không tắt TLS verification; trace API trả về đầy đủ ba observations.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics cho biết P95 retrieval tăng; correlation ID định vị cặp request/response trong logs; trace của các request mới cho biết thời gian và dữ liệu retrieval/generation từng bước.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt version cho biết cấu hình nào tạo câu trả lời; usage/cost giúp phân tích mức dùng; SLO đặt ngưỡng trải nghiệm; rollback khôi phục version đã biết khi candidate gây regression.
- **Điều quan trọng nhất đã học:** Một trace có ích cần đúng cây observation, input/output đủ để giải thích quyết định, metadata tương quan với log, usage/cost và masking PII.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Challenge lịch sử không có trace vì chạy trước khi keys được thêm; Cloud prompt fetch hiện timeout nên remote baseline/candidate và rollback chưa được xác minh. Repository URL và commit SHA cuối cần điền sau khi push commit nộp bài.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
