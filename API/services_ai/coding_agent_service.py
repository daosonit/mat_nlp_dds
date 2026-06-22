import os
import logging
from typing import Dict, Any, List
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from tools.file_tools import read_file, write_file, list_directory

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory để khởi tạo LLM Model theo cấu hình"""

    @staticmethod
    def create_llm(provider: str = "ollama", **kwargs):
        if provider.lower() == "ollama":
            model = kwargs.get("model", "qwen2.5-coder:14b")
            temperature = kwargs.get("temperature", 0.2)
            base_url = kwargs.get("base_url") or os.getenv(
                "OLLAMA_BASE_URL", "http://192.168.1.99:11434"
            )
            logger.info(f"Khởi tạo Ollama LLM (Model: {model}, URL: {base_url})")
            return ChatOllama(model=model, temperature=temperature, base_url=base_url)

        elif provider.lower() == "gemini":
            model = kwargs.get("model", "gemini-2.5-flash")
            temperature = kwargs.get("temperature", 0.2)
            api_key = (
                kwargs.get("api_key")
                or os.getenv("GEMINI_AI_KEY")
                or os.getenv("GEMINI_API_KEY")
            )
            if not api_key:
                logger.warning("Không tìm thấy API Key cho Gemini!")
            logger.info(f"Khởi tạo Gemini LLM (Model: {model})")
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                google_api_key=api_key,
                max_retries=2,
            )
        else:
            raise ValueError(
                f"Provider '{provider}' không được hỗ trợ. Dùng 'ollama' hoặc 'gemini'."
            )


class CodingAgentService:
    def __init__(self):
        # Lấy provider từ biến môi trường, mặc định là ollama
        provider = os.getenv("LLM_PROVIDER", "ollama")

        # Khởi tạo LLM thông qua Factory
        self.llm = LLMFactory.create_llm(provider=provider)

        self.tools = [read_file, write_file, list_directory]

        # Xây dựng Graph
        self.graph = self._build_graph()

    def _build_graph(self):
        son_prompt = (
            "Bạn là Kỹ sư Sơn - Chuyên gia Python, DevOps & Setup Môi trường AI.\n"
            "Chuyên môn: Là một chuyên gia Python lão luyện, hiểu biết cực kỳ sâu rộng về PhoBERT, VisoBERT, LangChain, và LangGraph. Bậc thầy về Docker, Docker Compose, CI/CD, Containerization và triển khai Microservices.\n"
            "Góc nhìn: Thiết lập môi trường phải chuẩn xác, cô lập, và dễ dàng nhân bản. Tối ưu networking giữa các container.\n"
            "Lập trường: Mọi dự án (đặc biệt là hệ thống API, AI Model và Frontend) phải chạy được chỉ với một lệnh (vd: docker-compose up). Code ngon mà không setup môi trường chuẩn thì cũng vô dụng.\n"
            "Giọng điệu: Kỹ thuật, hệ thống, thích sử dụng các khái niệm về Python, AI (PhoBERT, VisoBERT, LangChain, LangGraph), container, port mapping, volume, network.\n"
            "NHIỆM VỤ CỦA BẠN: Cung cấp giải pháp lập trình Python và thiết lập môi trường bằng Docker, Docker Compose cho 3 dự án (API, AI Model, Frontend). Tư vấn cách đóng gói, kết nối chúng thành một hệ thống Microservices thống nhất tích hợp AI. BẠN CÓ QUYỀN SỬ DỤNG TOOLS (read_file, write_file, list_directory) để tương tác với mã nguồn, tự động viết code Python, viết file Dockerfile và docker-compose.yml."
        )

        # Sử dụng ReAct agent cho Sơn để có thể gọi Tools
        son_agent = create_react_agent(self.llm, self.tools, prompt=son_prompt)

        def node_son(state: MessagesState):
            # Gọi sub-agent (ReAct)
            result = son_agent.invoke({"messages": state["messages"]})
            # Lấy các tin nhắn mới sinh ra (từ AI, Tool) ngoại trừ tin nhắn cũ
            new_messages = result["messages"][len(state["messages"]) :]
            for msg in new_messages:
                if isinstance(msg, AIMessage) and not msg.name:
                    msg.name = "Son"
            return {"messages": new_messages}

        # Dựng đồ thị
        workflow = StateGraph(MessagesState)
        workflow.add_node("Son", node_son)

        workflow.add_edge(START, "Son")
        workflow.add_edge("Son", END)

        return workflow.compile()

    def stream_chat(self, message: str):
        """Chạy Multi-Agent Workflow và stream kết quả về qua SSE."""
        inputs = {"messages": [HumanMessage(content=message)]}
        import json

        try:
            # stream_mode="updates" để hứng output từng Node
            for update in self.graph.stream(inputs, stream_mode="updates"):
                for node_name, state_update in update.items():
                    messages = state_update.get("messages", [])
                    for msg in messages:
                        if isinstance(msg, AIMessage):
                            if msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    step = {
                                        "type": "tool_call",
                                        "tool": tool_call["name"],
                                        "args": tool_call["args"],
                                        "author": msg.name or node_name,
                                    }
                                    yield f"data: {json.dumps(step)}\n\n"
                            elif msg.content:
                                content_str = msg.content
                                if isinstance(content_str, list):
                                    # Gemini sometimes returns content as a list of dicts: [{"type": "text", "text": "..."}]
                                    content_str = " ".join(
                                        [
                                            (
                                                c.get("text", "")
                                                if isinstance(c, dict)
                                                else str(c)
                                            )
                                            for c in content_str
                                        ]
                                    )
                                elif not isinstance(content_str, str):
                                    content_str = str(content_str)

                                step = {
                                    "type": "message",
                                    "content": content_str,
                                    "author": msg.name or node_name,
                                }
                                yield f"data: {json.dumps(step)}\n\n"
                        elif isinstance(msg, ToolMessage):
                            content = msg.content
                            if len(content) > 1000:
                                content = content[:1000] + "\n... (truncated)"
                            step = {
                                "type": "tool_result",
                                "tool": msg.name,
                                "result": content,
                                "author": "System",
                            }
                            yield f"data: {json.dumps(step)}\n\n"
        except Exception as e:
            logger.error(f"Agent error: {e}")
            step = {
                "type": "message",
                "content": f"Đã xảy ra lỗi: {str(e)}",
                "author": "System",
            }
            yield f"data: {json.dumps(step)}\n\n"
        finally:
            yield "data: [DONE]\n\n"
