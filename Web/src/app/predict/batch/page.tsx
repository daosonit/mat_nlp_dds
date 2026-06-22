"use client";

import { useState, useContext, useEffect } from "react";
import AuthGuard, { WebSocketContext } from "@/components/AuthGuard";
import api from "@/lib/api";
import { Send, Hash, Activity } from "lucide-react";
import toast from "react-hot-toast";

function BatchPredictContent() {
  const [numInputs, setNumInputs] = useState<number>(3);
  const [texts, setTexts] = useState<string[]>(["", "", ""]);
  const [loading, setLoading] = useState(false);
  const [batchStatus, setBatchStatus] = useState<{
    message: string;
    invalids: string[];
  } | null>(null);
  const wsContext = useContext(WebSocketContext);
  const clientId = wsContext?.clientId;
  const wsConnected = wsContext?.wsConnected || false;

  const handleNumChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = parseInt(e.target.value);
    if (isNaN(val) || val < 1) val = 1;
    if (val > 10) val = 10;

    setNumInputs(val);

    setTexts((prev) => {
      const newTexts = [...prev];
      if (val > newTexts.length) {
        // Add empty strings
        for (let i = newTexts.length; i < val; i++) {
          newTexts.push("");
        }
      } else if (val < newTexts.length) {
        // Truncate array
        newTexts.length = val;
      }
      return newTexts;
    });
  };

  const handleTextChange = (index: number, value: string) => {
    setTexts((prev) => {
      const newTexts = [...prev];
      newTexts[index] = value;
      return newTexts;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validTexts = texts.map((t) => t.trim()).filter((t) => t.length > 0);

    if (validTexts.length === 0) {
      toast.error("Vui lòng nhập ít nhất một văn bản!");
      return;
    }

    setLoading(true);
    setBatchStatus(null);

    try {
      const res = await api.post("/predict/batch", {
        texts: validTexts,
        client_id: clientId,
      });

      const data = res.data;

      const invalids =
        data.invalid_texts && data.invalid_texts.length > 0
          ? data.invalid_texts.map(
              (inv: any) => `Dòng ${inv.index + 1}: ${inv.reason}`,
            )
          : [];

      setBatchStatus({
        message:
          data.message || `Đã đẩy ${validTexts.length} task vào hàng đợi!`,
        invalids,
      });

      // Clear inputs after successful submission
      setTexts(Array(numInputs).fill(""));
    } catch (error: any) {
      const errMessage =
        error.response?.data?.detail || "Gửi batch thất bại, vui lòng thử lại!";
      toast.error(errMessage);
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-[980px] mx-auto py-8 px-4 sm:px-6 lg:px-8 font-mono">
      <div className="text-center mb-10 border-b border-[#00ff33]/30 pb-6">
        <h1 className="text-base font-bold text-[#00ff33] tracking-widest cyber-text-glow">
          BATCH PREDICTION ENGINE
        </h1>

        {batchStatus && (
          <div className="mt-6 p-4 bg-black border border-[#00ff33]/30 inline-block text-left min-w-[300px]">
            <p className="text-[#00ff33] font-bold text-sm tracking-widest flex items-center">
              <Activity className="w-4 h-4 mr-2" />
              {batchStatus.message}
            </p>
            {batchStatus.invalids.length > 0 && (
              <div className="mt-3 pt-3 border-t border-[#00ff33]/20 space-y-1">
                {batchStatus.invalids.map((inv, idx) => (
                  <p
                    key={idx}
                    className="text-[#ff003c] text-xs font-bold cyber-text-glow-red"
                  >
                    [FAIL] {inv}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="bg-black cyber-border overflow-hidden mb-8 relative">
        <div>
          <form onSubmit={handleSubmit} className="p-6 sm:p-8 relative z-10">
            <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#00ff33]/30 pb-6 gap-4">
              <div className="flex items-center gap-4">
                <label
                  htmlFor="numInputs"
                  className="block text-sm font-bold text-[#00ff33] uppercase tracking-widest"
                >
                  NUMBER OF INPUTS (1-10):
                </label>
                <input
                  type="number"
                  id="numInputs"
                  min="1"
                  max="10"
                  value={numInputs}
                  onChange={handleNumChange}
                  className="bg-black border border-[#00ff33]/50 text-[#00ff33] text-center w-20 p-2 focus:ring-0 focus:border-[#00ff33] cyber-glow transition-all"
                />
              </div>

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

            <div className="space-y-4 mb-8">
              {texts.map((text, idx) => (
                <div key={idx} className="relative">
                  <textarea
                    rows={2}
                    className="block w-full bg-black border border-[#00ff33]/30 text-[#00ff33] focus:ring-0 focus:border-[#00ff33] cyber-glow text-base p-2 resize-none transition-all rounded-none placeholder-[#00ff33]/30"
                    placeholder={`Input text #${idx + 1}...`}
                    value={text}
                    onChange={(e) => handleTextChange(idx, e.target.value)}
                    disabled={loading}
                  />
                </div>
              ))}
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={
                  loading ||
                  !wsConnected ||
                  !texts.some((t) => t.trim().length > 0)
                }
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
                    EXECUTE BATCH
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function PredictBatchPage() {
  return (
    <AuthGuard>
      <BatchPredictContent />
    </AuthGuard>
  );
}
