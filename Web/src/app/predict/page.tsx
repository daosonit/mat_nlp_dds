"use client";

import { useState, useEffect, useRef } from "react";
import AuthGuard, { WebSocketContext } from "@/components/AuthGuard";
import { useContext } from "react";
import api from "@/lib/api";
import {
  Send,
  Bot,
  AlertCircle,
  CheckCircle,
  Activity,
  Hash,
} from "lucide-react";
import toast from "react-hot-toast";

interface PredictResponse {
  text: string;
  segmented_text: string;
  label: string;
  score: number;
  model_used: string;
  is_teencode: boolean;
}

function PredictContent() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [predictStatus, setPredictStatus] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);
  const wsContext = useContext(WebSocketContext);
  const clientId = wsContext?.clientId;
  const wsConnected = wsContext?.wsConnected || false;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) {
      setPredictStatus({
        type: "error",
        message: "Vui lòng nhập văn bản cần phân tích!",
      });
      return;
    }

    setLoading(true);
    setResult(null);
    setPredictStatus(null);

    try {
      const res = await api.post("/predict", {
        text: text.trim(),
        client_id: clientId,
      });
      setText("");
      setPredictStatus({
        type: "success",
        message: res.data.message || "Đã gửi vào hàng đợi xử lý!",
      });
      setLoading(false);
    } catch (error: any) {
      const errorText = error.response?.data?.text || "";
      const reason =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        "Nội dung không có ý nghĩa";
      setPredictStatus({
        type: "error",
        message: errorText
          ? `[FAIL] ${errorText} - ${reason}`
          : `[FAIL] ${reason}`,
      });
      setLoading(false);
    }
  };

  const getLabelColor = (label: string) => {
    switch (label) {
      case "positive":
        return "text-[#00ff33] bg-[#00ff33]/10 border-[#00ff33] cyber-glow";
      case "negative":
        return "text-[#ff003c] bg-[#ff003c]/10 border-[#ff003c] cyber-glow-red";
      case "neutral":
        return "text-gray-400 bg-gray-900 border-gray-600";
      default:
        return "text-[#00ff33] bg-[#00ff33]/10 border-[#00ff33]";
    }
  };

  const getLabelText = (label: string) => {
    switch (label) {
      case "positive":
        return "POSITIVE";
      case "negative":
        return "NEGATIVE";
      case "neutral":
        return "NEUTRAL";
      default:
        return label;
    }
  };

  return (
    <div className="w-full max-w-[980px] mx-auto py-8 px-4 sm:px-6 lg:px-8 font-mono">
      <div className="text-center mb-10 border-b border-[#00ff33]/30 pb-6">
        <h1 className="text-base font-bold text-[#00ff33] tracking-widest cyber-text-glow">
          AI PREDICTION ENGINE
        </h1>
        <p className="mt-2 text-sm text-[#00ff33]/60">
          AUTO-DETECT: TEENCODE | MODELS: PHO-BERT / VISO-BERT
        </p>

        {predictStatus && (
          <div
            className={`mt-6 p-4 border inline-block text-left min-w-[300px] bg-black ${
              predictStatus.type === "success"
                ? "border-[#00ff33]/30"
                : "border-[#ff003c]/30"
            }`}
          >
            <p
              className={`font-bold text-sm tracking-widest flex items-center ${
                predictStatus.type === "success"
                  ? "text-[#00ff33]"
                  : "text-[#ff003c] cyber-text-glow-red"
              }`}
            >
              <Activity className="w-4 h-4 mr-2" />
              {predictStatus.message}
            </p>
          </div>
        )}
      </div>

      <div className="bg-black cyber-border overflow-hidden mb-8 relative">
        <form onSubmit={handleSubmit} className="p-6 sm:p-8 relative z-10">
          {/* Header Form: Label + Realtime Status */}
          <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#00ff33]/30 pb-6 gap-4">
            <label
              htmlFor="text"
              className="block text-sm font-bold text-[#00ff33] uppercase tracking-widest"
            >
              INPUT TEXT TO ANALYZE
            </label>

            {/* Realtime Status Indicator */}
            <div className="flex items-center bg-[#00ff33]/5 border border-[#00ff33]/30 px-4 py-2">
              <div
                className={`w-2 h-2 rounded-full mr-3 ${wsConnected ? "bg-[#00ff33] animate-pulse cyber-glow" : "bg-red-500"}`}
              ></div>
              <span
                className={`text-xs font-bold tracking-widest ${wsConnected ? "text-[#00ff33]" : "text-red-500"}`}
              >
                {wsConnected ? "REALTIME: ON" : "REALTIME: OFF"}
              </span>
            </div>
          </div>
          <div className="mb-6">
            <textarea
              id="text"
              rows={4}
              className="block w-full bg-black border border-[#00ff33]/30 text-[#00ff33] focus:ring-0 focus:border-[#00ff33] cyber-glow text-base p-4 resize-none transition-all rounded-none placeholder-[#00ff33]/30"
              placeholder="Enter text here..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading || !text.trim() || !wsConnected}
              className="inline-flex items-center px-8 py-3 border border-[#00ff33] text-[#00ff33] bg-black hover:bg-[#00ff33] hover:text-black font-bold uppercase transition-all cursor-pointer disabled:cursor-not-allowed disabled:opacity-30 rounded-none cyber-glow tracking-widest"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-[#00ff33] border-t-transparent rounded-full animate-spin mr-3"></div>
                  PROCESSING...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5 mr-2" />
                  EXECUTE
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {result && (
        <div className="bg-black cyber-border overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className={`px-6 py-4 border-b ${getLabelColor(result.label)}`}>
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold flex items-center tracking-widest">
                <Activity className="w-5 h-5 mr-2" />
                RESULT: {getLabelText(result.label)}
              </h3>
              <span className="inline-flex items-center px-3 py-1 text-sm font-bold border border-current">
                CONFIDENCE: {(result.score * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="p-6 sm:p-8 space-y-6">
            <div className="grid grid-cols-1 gap-6">
              <div className="bg-[#050505] p-4 border border-[#00ff33]/20">
                <div className="flex items-center text-xs font-bold text-[#00ff33]/60 mb-2 uppercase">
                  <Bot className="w-4 h-4 mr-1.5" /> MODEL USED
                </div>
                <div className="text-[#00ff33] font-bold text-base uppercase cyber-text-glow">
                  {result.model_used}
                </div>
              </div>
            </div>

            <div>
              <div className="flex items-center text-xs font-bold text-[#00ff33]/60 mb-2 mt-4 uppercase">
                <Hash className="w-4 h-4 mr-1.5" /> WORD SEGMENTATION OUTPUT
              </div>
              <div className="bg-[#050505] p-4 border border-[#00ff33]/20 text-[#00ff33] font-mono text-sm leading-relaxed whitespace-pre-wrap break-words">
                {result.segmented_text}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function PredictPage() {
  return (
    <AuthGuard>
      <PredictContent />
    </AuthGuard>
  );
}
