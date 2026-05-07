# Stock Agent AI - Hướng Dẫn Kỹ Thuật Cho AI

Tài liệu này là hướng dẫn làm việc cho quá trình phát triển có hỗ trợ AI trong repository này. Nó giữ vai trò tương tự như `CLAUDE.md` hoặc một tài liệu hướng dẫn agent cục bộ của repo: xác định các ràng buộc kiến trúc, quy tắc triển khai và tiêu chuẩn review để Codex có thể chỉnh sửa mà không làm lệch hệ thống.

Hãy coi tài liệu này là hợp đồng vận hành mặc định, trừ khi người dùng đưa ra chỉ dẫn rõ ràng mới hơn.

## Mục Tiêu

Xây dựng và phát triển một hệ thống phân tích cổ phiếu đa agent theo hướng production, có khả năng:

- phân tích dữ liệu thị trường chứng khoán bằng chỉ báo xác định và mô hình ML cục bộ
- đưa ra `BUY`, `SELL`, hoặc `HOLD`
- trả về độ tin cậy, cảnh báo và lập luận
- sẵn sàng cho backtesting và tích hợp RAG trong tương lai

Stack chính:

- Python
- FastAPI
- LangGraph
- LangChain
- Ollama
- Redis
- PostgreSQL
- Docker

## Nguyên Tắc Cốt Lõi

- Giữ logic nghiệp vụ mang tính xác định ở mức tối đa có thể.
- Chỉ dùng LLM cho suy luận, tóm tắt và giải thích.
- Mỗi agent phải có đúng một trách nhiệm chính.
- Điều phối phải rõ ràng trong LangGraph.
- Ưu tiên các service có thể tái sử dụng thay vì agent quá lớn.
- Thiết kế theo hướng dễ quan sát, có retry, chịu được lỗi từng phần.
- Ưu tiên khả năng bảo trì trước sự mới lạ.

## Nguyên Tắc Kiến Trúc

- Hệ thống là hybrid:
  - orchestration agentic để điều phối workflow
  - phân tích xác định cho technical và scoring dựa trên rule
  - mô hình ML cục bộ để hỗ trợ tín hiệu hướng đi
  - interface sẵn sàng cho RAG để tăng cường tri thức trong tương lai
- Graph là nguồn chân lý cho thứ tự thực thi.
- Agent chỉ nên trả về cập nhật state từng phần.
- I/O với hệ thống bên ngoài phải nằm ở layer service, không nằm trong logic ra quyết định.
- Tất cả kết quả quyết định phải có thể tái hiện từ input state cộng với phản hồi LLM đã được kiểm tra.
- Các concern hạ tầng dùng chung như config, cache, persistence và logging phải nằm trong `services/` hoặc `db/`, không đặt trong file agent.

## Tiêu Chuẩn Mã Nguồn

- Dùng style Python 3.12+ và type hints nhất quán.
- Ưu tiên module nhỏ, mỗi module một trách nhiệm rõ ràng.
- Dùng `TypedDict`, dataclass hoặc Pydantic khi cấu trúc dữ liệu là quan trọng.
- Tránh global state ẩn.
- Tránh side effect khi import.
- Giữ function ngắn và tường minh.
- Raise exception cụ thể cho lỗi validate và lỗi runtime.
- Validate mọi input bên ngoài ở boundary.
- Chỉ thêm `TODO` cho công việc follow-up thật sự, không ghi chú trống nghĩa.
- Không tạo abstraction rộng nếu nó không giải quyết được trùng lặp hoặc phức tạp cụ thể.

## Quy Tắc LangGraph

- Dùng `TypedDict` làm contract cho state của graph.
- Giữ state key ổn định. Không đổi tên key tùy tiện.
- Mỗi node phải đọc từ state và trả về partial state dict.
- Không mutate các field state không liên quan bên trong một agent.
- Topology của graph phải luôn dễ đọc.
- Ưu tiên fan-out từ `data_agent` sang các analysis agent, sau đó hội tụ vào `decision_agent`.
- Giữ branching mang tính xác định trừ khi có lý do rõ ràng về hiệu năng hoặc sản phẩm.
- Không ẩn quy tắc orchestration bên trong service code.
- Nếu thêm agent mới, phải cập nhật:
  - topology của graph
  - định nghĩa state
  - test
  - tài liệu này nếu role đó làm thay đổi hành vi hệ thống

## Quy Tắc Quản Lý State

LangGraph state phải bao gồm:

- `symbol`
- `price_data`
- `indicators`
- `fundamentals`
- `sentiment`
- `prediction`
- `decision`
- `alerts`
- `metadata`

Quy tắc:

- Xem state là contract giữa các agent.
- Giữ cho mỗi field top-level có ý nghĩa hẹp và rõ.
- `metadata` dùng cho context thực thi, flag, timing, provenance và ghi chú run.
- Không nhồi kết quả nghiệp vụ vào `metadata` nếu nó xứng đáng là field hạng nhất.
- `price_data` chỉ nên chứa dữ liệu đã chuẩn hóa và có thể serialize.
- Giá trị trong state mặc định phải JSON-serializable, trừ khi có lý do rất rõ cho object nội bộ chỉ dùng trong graph.
- Tránh lưu object nặng như DataFrame hay DB session trong state dài hạn.

## Trách Nhiệm Của Agent

### `data_agent`

- Lấy và chuẩn hóa dữ liệu thị trường.
- Không dùng LLM.
- Không làm suy luận đầu tư.
- Phải trả về lịch sử giá sạch và metadata nguồn gốc.

### `technical_agent`

- Tính chỉ báo bằng thư viện xác định như `pandas-ta`.
- Không dùng LLM.
- Không gọi API trừ khi agent được mở rộng rõ ràng cho việc enrich dữ liệu nội bộ.
- Không bao giờ tính indicator bằng prompt cho model.

### `fundamental_agent`

- Xây snapshot fundamentals ở cấp doanh nghiệp hoặc tín hiệu fundamentals suy ra.
- Ưu tiên rule xác định hơn narrative output.
- Nếu dữ liệu upstream không có, phải trả về trạng thái fallback rõ ràng.

### `sentiment_agent`

- Dùng LLM với prompt ngắn, bị ràng buộc chặt.
- Phải trả về output có cấu trúc và đã validate.
- Không được trực tiếp quyết định giao dịch.

### `prediction_agent`

- Load và chạy file `.pt` PyTorch cục bộ.
- Phát ra directional prediction cùng confidence và metadata thô.
- Prediction chỉ là một tín hiệu đầu vào.
- Không tải model artifact từ xa khi runtime.

### `decision_agent`

- Kết hợp mọi tín hiệu trước đó thành action cuối cùng và reasoning.
- Không được truy cập API bên ngoài.
- Không tính indicator.
- Không fetch market data.
- Phải sinh ra output có cấu trúc chặt chẽ.
- Phải xem output ML như một tín hiệu trong nhiều tín hiệu, không phải nguồn quyết định tuyệt đối.

### `alert_agent`

- Chuyển final decision và tín hiệu đáng chú ý thành cảnh báo hành động.
- Giữ việc tạo alert ở dạng xác định.
- Tách độ nghiêm trọng của alert khỏi trade decision.

## Quy Tắc Prompt Engineering

- Giữ prompt ngắn.
- Luôn nêu rõ output schema.
- Ưu tiên strict JSON.
- Chỉ cung cấp cho model lượng context tối thiểu cần thiết.
- Yêu cầu model giải thích, không phát minh.
- Không yêu cầu LLM tính technical indicator hoặc tín hiệu số đã có sẵn trong code.
- Validate mọi phản hồi từ LLM trước khi dùng.
- Luôn có fallback khi parse thất bại.
- Tránh prompt nhiều đoạn trừ khi nhiệm vụ thật sự cần thêm context.

Hướng dẫn template prompt:

- system prompt:
  - định nghĩa vai trò thật hẹp
  - định nghĩa chính xác output shape
  - cấm markdown nếu không cần
- user prompt:
  - chỉ truyền tín hiệu liên quan
  - truyền giá trị đã chuẩn hóa
  - tránh dump context dài dòng

## Quy Tắc Tích Hợp ML

- Prediction dùng artifact `.pt` PyTorch cục bộ.
- Inference model phải được cô lập trong `services/prediction_model.py` hoặc tương đương.
- Không giấu việc load model trong agent không liên quan.
- Quá trình tạo feature phải mang tính xác định và có thể version hóa.
- Thiếu model artifact phải fail rõ ràng hoặc đi theo fallback path minh bạch.
- Log model version hoặc model path cho mỗi run.
- Không để inference ML trực tiếp override deterministic risk control.
- Giữ input feature shape, sequence length và giả định label được ghi rõ trong code.
- Code retraining model trong tương lai phải tách khỏi runtime inference.

## Anti-Patterns

Không làm những việc sau:

- tính RSI, MACD hoặc indicator tương tự bằng LLM
- fetch API bên ngoài bên trong `decision_agent`
- trộn data fetching, reasoning và persistence trong cùng một agent
- trả về text tự do từ model mà không validate
- truyền DataFrame thô xuyên suốt mọi layer khi dạng serialize là đủ
- giấu business rule quan trọng chỉ trong wording của prompt
- coi ML model là quyết định giao dịch cuối cùng
- viết agent quá lớn, sở hữu nhiều concern
- xây dựng hành vi của graph theo cách ngầm thông qua side effect
- đưa cross-cutting logic trực tiếp vào API route handler

## Quy Tắc Tổ Chức File

Project layout:

- `apps/api/`: FastAPI app, routes, schemas, dependency wiring
- `apps/worker/`: worker async và queue consumer
- `agents/`: chỉ chứa implementation của graph node
- `graph/`: định nghĩa state và builder LangGraph
- `services/`: domain service và infrastructure service tái sử dụng
- `models/`: model artifact cục bộ và ghi chú về model
- `db/`: ORM models, SQL bootstrap, repository, session
- `rag/`: interface và implementation retrieval trong tương lai
- `configs/`: nơi đặt các module config tách riêng khi cần

Quy tắc:

- Giữ route handler mỏng.
- Giữ agent mỏng.
- Đặt logic nghiệp vụ tái sử dụng trong `services/`.
- Đặt persistence logic trong `db/` hoặc storage service.
- Không tạo circular dependency giữa `agents/`, `services/` và `graph/`.
- Nếu file vượt quá kích thước hợp lý cho một trách nhiệm, hãy tách theo concern.

## Chiến Lược Logging

- Dùng log có cấu trúc, nhất quán.
- Log tối thiểu:
  - bắt đầu run
  - kết thúc run
  - symbol
  - lỗi agent
  - tình huống fallback
  - trạng thái load model
  - lỗi persistence
- Không bao giờ log secret.
- Tránh log toàn bộ payload thô trừ khi thật sự cần debug và an toàn.
- Khi có thể, luôn đưa symbol và execution context vào log.
- Lỗi parse LLM phải được log đủ để debug, nhưng không dump quá nhiều gây nhiễu.

Cách làm khuyến nghị:

- logger ở cấp module cho mỗi file
- cấu hình logging tập trung
- message key nhất quán
- sẵn sàng cho JSON logs trong container sau này

## Chiến Lược Testing

Kỳ vọng tối thiểu:

- test từng agent độc lập
- test graph chạy end to end
- mock LLM call
- mock provider market data từ xa
- test validation output có cấu trúc và fallback logic
- test fallback prediction khi thiếu model file
- test persistence và queue integration riêng

Các tầng test khuyến nghị:

### Unit tests

- tính toán indicator
- decision scoring
- parse prompt
- chuẩn bị feature cho model
- repository method

### Integration tests

- API request đi đến graph execution
- luồng queue dựa trên Redis
- persistence với PostgreSQL
- sanity startup local bằng Docker Compose

### Regression tests

- độ ổn định của state key
- độ ổn định của decision schema
- giả định về topology graph

## Quy Trình Docker

- Dùng Docker để đảm bảo môi trường local gần với triển khai.
- Giữ API, worker, Redis, PostgreSQL và Ollama là các service riêng.
- Build image tái lặp được với dependency pin chặt khi hợp lý.
- Ưu tiên environment variable hơn hardcode giá trị triển khai.
- Mount model artifact và config rõ ràng.
- Không giả định Ollama model đã được pull sẵn; phải bootstrap có chủ đích.

Quy trình kỳ vọng:

1. cập nhật `.env`
2. đảm bảo `models/stock_trending_model.pt` tồn tại
3. chạy `docker compose up --build`
4. kiểm tra health của API và dependency
5. test một request phân tích end to end

## Checklist Review Cho Codex

Trước khi hoàn tất thay đổi, cần xác minh:

- boundary kiến trúc vẫn được giữ
- state key vẫn nhất quán
- agent vẫn đúng một trách nhiệm
- không dùng LLM cho tính toán số xác định
- `decision_agent` không fetch dữ liệu bên ngoài
- output ML chỉ là tín hiệu phụ trợ
- file mới được đặt đúng package
- lỗi và fallback là tường minh
- test bao phủ hành vi thay đổi ở mức tương xứng

## Ghi Chú Về Khả Năng Mở Rộng Tương Lai

Chuẩn bị cho các mở rộng sau mà không cản trở việc giao hàng hiện tại:

- backtesting engine tách khỏi live inference path
- batch analysis cho workflow nhiều symbol
- routing alert và notification channel phong phú hơn
- research summary có hỗ trợ RAG
- so sánh tín hiệu có awareness về memory hoặc lịch sử
- model registry và versioning cho artifact
- thực thi song song async cho các node tốn chi phí nhưng không phụ thuộc nhau
- observability stack với metrics và traces
- API auth theo vai trò và audit logging

Giữ mọi mở rộng trong tương lai theo hướng cộng thêm. Không trộn runtime graph hiện tại với feature suy đoán nếu chưa có boundary rõ.

## Codex Nên Làm Gì Trong Repo Này

- Đọc các file liên quan trước khi chỉnh sửa.
- Ưu tiên pattern cục bộ đã được thiết lập trong repo.
- Thực hiện thay đổi với phạm vi hẹp.
- Giữ nguyên graph và state contract.
- Khi thêm capability mới, cập nhật code, docs và test cùng lúc.
- Nêu blocker rõ ràng khi thiếu asset bên ngoài, đặc biệt:
  - file model PyTorch
  - model Ollama
  - kết nối database
  - lỗi provider market data

Nếu yêu cầu của người dùng xung đột với tài liệu này, hãy làm theo yêu cầu rõ ràng của người dùng và cố gắng giữ tối đa kỷ luật kiến trúc.

## Tóm Tắt Phiên Làm Việc

Phần này tóm tắt những gì đã được triển khai trong repository ở phiên hiện tại để các lần làm việc sau có thể bắt đầu từ trạng thái thực của dự án, thay vì giả định theo trạng thái scaffold ban đầu.

### Đã Hoàn Thành Trong Phiên Này

Các khu vực sau đã được triển khai hoặc refactor đáng kể:

- scaffold dự án cho:
  - `apps/api`
  - `apps/worker`
  - `agents`
  - `graph`
  - `services`
  - `db`
  - `rag`
  - `models`
  - `configs`
- orchestration LangGraph:
  - typed graph state
  - builder module tường minh
  - parallel fan-out từ `data_agent`
  - hội tụ vào `decision_agent`
  - `alert_agent` là node cuối
- các agent đã triển khai:
  - `data_agent`
  - `technical_agent`
  - `fundamental_agent`
  - `sentiment_agent`
  - `prediction_agent`
  - `decision_agent`
  - `alert_agent`
- FastAPI API:
  - `GET /v1/analyze/{symbol}`
  - `GET /healthz`
  - response có cấu trúc
  - logging và exception handling
- worker scaffold cho queued analysis execution
- hạ tầng Docker:
  - `Dockerfile` nhiều stage
  - `docker-compose.yml`
  - `.env.example`
- cấu hình tập trung trong `configs/settings.py`
- tích hợp prediction với local PyTorch model loading và fallback behavior
- skeleton RAG:
  - ingestion service
  - retrieval abstraction
  - tích hợp Ollama embeddings
- skeleton test:
  - cấu hình pytest
  - unit tests
  - agent tests
  - graph tests
- refactor theo hướng production:
  - shared Pydantic schemas
  - runtime wiring tập trung
  - exception class tường minh
  - retry helper cơ bản
  - cải thiện logging
  - DB session handling chắc chắn hơn
  - loại bỏ `decision_parser.py` lỗi thời
- đã thêm scaffold cho tương lai:
  - Kubernetes deployment
  - async ingestion
  - websocket streaming
  - backtesting engine

### Trạng Thái Thực Tế Hiện Tại Của Codebase

Các sự thật quan trọng về repo ở thời điểm này:

- `decision_agent` đang sở hữu logic deterministic scoring thực tế.
- `services/decision_parser.py` đã bị xóa và không nên được đưa trở lại trừ khi có lý do kiến trúc rất rõ.
- output của technical indicator là dạng lồng nhau, có cấu trúc, không còn là dạng phẳng.
- prediction output đánh dấu rõ ràng rằng nó là:
  - tín hiệu phụ trợ
  - không phải quyết định cuối cùng
- RAG mới chỉ là skeleton. Nó chưa được nối vào decision flow.
- Kubernetes manifest mới chỉ ở mức baseline khởi đầu.
- worker flow đã tồn tại, nhưng queue semantics và retry/dead-letter behavior vẫn chưa hoàn chỉnh ở mức production.

## Các Khoảng Trống Đã Biết Và Vùng Chưa Rõ

Những phần sau vẫn chưa hoàn thiện, còn mang tính xấp xỉ, hoặc cần làm rõ trước khi coi là production-ready:

### Fundamentals

- `fundamental_agent` hiện vẫn dựa trên một deterministic estimator dạng placeholder.
- Chưa có nguồn dữ liệu tài chính kiểm toán thực tế được tích hợp.
- Trước khi dùng thực tế, cần thay logic placeholder bằng provider thật và chiến lược validate phù hợp.

### Hợp Đồng Với Prediction Model

- loader `.pt` hiện hỗ trợ:
  - `nn.Module` được serialize
  - `state_dict` tương thích
- contract chính thức của kiến trúc model huấn luyện vẫn chưa được tài liệu hóa đầy đủ
- nếu kiến trúc model thật khác đi, loader sẽ cần adapter chuyên biệt cho model đó

### Decision Logic

- trọng số deterministic hiện tại mới là trọng số heuristic khởi đầu
- chưa có quy trình calibration chính thức cho:
  - score threshold
  - confidence mapping
  - risk level mapping
- nếu business logic thay đổi, phải cập nhật test và tài liệu này cùng lúc

### Độ Tin Cậy Của Market Data Và Sentiment

- market data hiện đang dùng `yfinance`
- sentiment hiện đang dùng ước lượng LLM cục bộ
- chưa nên xem hai đường này là chất lượng dữ liệu ở cấp tổ chức/tổ chức tài chính

### Tích Hợp RAG

- RAG chưa được nối vào:
  - `decision_agent`
  - API response
  - report generation
- adapter Qdrant/Chroma hiện là placeholder đứng sau interface sạch

### Async Và Streaming

- async ingestion coordinator mới là scaffold, chưa phải job system hoạt động
- websocket streaming broker mới là in-memory, chưa được lộ ra qua API route
- chưa có tích hợp pub/sub bền vững

### Kubernetes

- đã có starter manifests, nhưng vẫn còn thiếu:
  - Secret management
  - Ingress
  - worker deployment
  - HPA
  - per-environment overlays

## Những Khu Vực Có Khả Năng Cần Chỉnh Sửa Tiếp

Các contributor hoặc AI agent trong tương lai nên chờ đợi các thay đổi tiếp theo ở những module sau:

- `services/fundamental_service.py`
  - thay logic placeholder
- `services/prediction_model.py`
  - đồng bộ với contract thật của model artifact
- `agents/decision_agent.py`
  - hiệu chỉnh trọng số score và cải thiện reasoning contract
- `rag/retriever.py`
  - thay fallback in-memory bằng backend adapter thật
- `services/market_data.py`
  - cải thiện provider abstraction và khả năng chịu lỗi
- `apps/worker/main.py`
  - cải thiện queue handling, retry policy và poison-message handling
- `k8s/`
  - mở rộng manifest vượt quá mức starter deployment

## Các Cải Tiến Tiếp Theo Được Khuyến Nghị

Các việc follow-up ưu tiên:

1. Thay fundamentals placeholder bằng tích hợp dữ liệu tài chính thật.
2. Định nghĩa contract thật của PyTorch model và tương thích training/inference.
3. Bổ sung coverage chạy pytest thực tế cho:
   - API routes
   - storage layer
   - runtime wiring
4. Thêm worker deployment thực tế và mô hình độ tin cậy cho queue.
5. Nối RAG vào luồng giải thích/reporting trước, không nối thẳng vào quyết định ngay.
6. Thêm websocket endpoint để stream tiến trình phân tích và event.
7. Đưa vào backtesting replay bằng historical snapshot trước khi tinh chỉnh decision weight.

## Các Cơ Hội Mở Rộng

Kiến trúc hiện tại đã sẵn sàng để hỗ trợ các mở rộng sau:

- phân tích batch nhiều symbol
- scoring có nhận thức về portfolio
- so sánh lịch sử và decision support có awareness về memory
- các kênh alert phong phú hơn:
  - websocket
  - email
  - Slack
  - webhook
- research summary dựa trên tài liệu qua RAG
- model registry và version tracking
- backtesting và strategy analytics
- human review workflow cho output có confidence thấp hoặc risk cao
- ingestion và streaming pipeline phân tán

## Hướng Dẫn Cho Các Lần AI Chỉnh Sửa Sau

Khi tiếp tục làm việc từ trạng thái repo này:

- không giả định dự án vẫn còn ở giai đoạn scaffold
- đọc code hiện tại trước khi thêm abstraction trùng lặp
- ưu tiên mở rộng các runtime/service boundary đã được thêm trong phiên này
- tránh đưa lại các legacy path đã bị xóa trừ khi có yêu cầu rõ ràng
- cập nhật lại tài liệu này nếu một phiên sau làm thay đổi đáng kể:
  - topology của graph
  - nơi sở hữu decision logic
  - prediction contract
  - mô hình triển khai
