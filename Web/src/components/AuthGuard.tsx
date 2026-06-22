"use client";

import { useEffect, useState, useRef, createContext } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Database, Bot, LogOut } from "lucide-react";
import toast from "react-hot-toast";

export const WebSocketContext = createContext<{
  ws: WebSocket | null;
  clientId: string;
  wsConnected: boolean;
  loadingPredict: boolean;
  setLoadingPredict: React.Dispatch<React.SetStateAction<boolean>>;
  predictResult: any | null;
  setPredictResult: React.Dispatch<React.SetStateAction<any | null>>;
} | null>(null);

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [clientId] = useState(
    () =>
      Math.random().toString(36).substring(2, 15) +
      Math.random().toString(36).substring(2, 15),
  );

  // Global Predict States
  const [loadingPredict, setLoadingPredict] = useState(false);
  const [predictResult, setPredictResult] = useState<any | null>(null);
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
    } else {
      setIsAuthenticated(true);
    }
  }, [router]);

  useEffect(() => {
    if (!isAuthenticated) return;

    const baseWsURL = process.env.NEXT_PUBLIC_WSS_URL || "ws://localhost:8000";
    let wsURL = baseWsURL + "/ws";
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token")
        : null;
    wsURL += `?client_id=${clientId}`;
    if (token) {
      wsURL += `&token=${token}`;
    }

    const websocket = new WebSocket(wsURL);
    setWs(websocket);

    websocket.onopen = () => {
      console.log("Global WebSocket connected");
      setWsConnected(true);
    };

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("📥 [WebSocket Global] Nhận được data từ Server:", data);

        // Match response from RabbitMQ/WebSocket with current task
        if (data.cmd === "predict_result") {
          if (data.status === "success" && data.ai_result) {
            setPredictResult(data.ai_result);

            const { label, segmented_text, score, model_used } = data.ai_result;
            const formattedScore = (score * 100).toFixed(1) + "%";

            const toastMessage = (
              <div className="flex flex-col space-y-1 font-mono">
                <span className="font-bold tracking-widest uppercase">
                  [{label}]
                </span>
                <span className="text-xs opacity-90 line-clamp-2">
                  {segmented_text}
                </span>
                <span className="text-[10px] opacity-70 border-t border-current/30 pt-1 mt-1 uppercase">
                  SCORE: {formattedScore} | MODEL: {model_used}
                </span>
              </div>
            );

            if (label === "positive") {
              toast.success(toastMessage);
            } else if (label === "negative") {
              toast.error(toastMessage);
            } else {
              toast(toastMessage);
            }
          } else {
            toast.error(data.error || "Phân tích thất bại từ AI Worker!");
          }
          setLoadingPredict(false);
        }
      } catch (error) {
        console.error("Error parsing websocket message", error);
      }
    };

    websocket.onerror = (error) => {
      console.error("Global WebSocket error:", error);
      setWsConnected(false);
    };

    websocket.onclose = () => {
      console.log("Global WebSocket disconnected");
      setWsConnected(false);
      setWs(null);
    };

    return () => {
      websocket.close();
    };
  }, [isAuthenticated]);

  const handleLogout = () => {
    if (ws) ws.close();
    localStorage.removeItem("access_token");
    router.push("/login");
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#00ff33] border-t-transparent rounded-full animate-spin mx-auto mb-4 cyber-glow"></div>
          <div className="text-[#00ff33] font-mono tracking-widest animate-pulse">
            INITIALIZING SECURE CONNECTION...
          </div>
        </div>
      </div>
    );
  }

  const menuItems = [
    { name: "DASHBOARD", href: "/", icon: Database },
    { name: "AI PREDICT", href: "/predict", icon: Bot },
    { name: "BATCH PREDICT", href: "/predict/batch", icon: Bot },
    { name: "AI ASSISTANT", href: "/agent", icon: Bot },
  ];

  return (
    <div className="flex h-screen bg-black overflow-hidden font-mono text-[#00ff33]">
      {/* Sidebar */}
      <aside className="w-64 bg-[#050505] border-r border-[#00ff33]/30 flex flex-col cyber-border z-10 relative">
        <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(0,255,51,0.02)_1px,transparent_1px)] bg-[size:100%_4px] opacity-20 z-0"></div>
        <div className="p-6 border-b border-[#00ff33]/30 relative z-10">
          <span className="text-base font-bold text-[#00ff33] cyber-text-glow tracking-widest">
            MAT ADMIN
          </span>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-3 overflow-y-auto relative z-10">
          {menuItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center px-4 py-3 text-sm font-bold uppercase transition-all duration-200 rounded-none cursor-pointer ${
                  isActive
                    ? "bg-[#00ff33]/10 text-[#00ff33] cyber-border cyber-glow"
                    : "text-gray-500 hover:text-[#00ff33] border border-transparent hover:border-[#00ff33]/50"
                }`}
              >
                <item.icon
                  className={`mr-3 flex-shrink-0 h-5 w-5 ${isActive ? "text-[#00ff33]" : "text-gray-500"}`}
                />
                {item.name}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t border-[#00ff33]/30 bg-black relative z-10">
          <button
            onClick={handleLogout}
            className="flex w-full items-center px-4 py-3 text-sm font-bold uppercase text-[#ff003c] hover:bg-[#ff003c]/10 border border-transparent hover:border-[#ff003c] cyber-text-glow-red transition-all duration-200 rounded-none cursor-pointer"
          >
            <LogOut className="mr-3 flex-shrink-0 h-5 w-5 text-[#ff003c]" />
            LOGOUT
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-[#050505] relative">
        {/* Terminal Scanline overlay */}
        <div className="fixed inset-0 pointer-events-none bg-[linear-gradient(rgba(0,255,51,0.03)_1px,transparent_1px)] bg-[size:100%_4px] opacity-20 z-0"></div>
        <div className="relative z-10 h-full w-full flex flex-col">
          <WebSocketContext.Provider
            value={{
              ws,
              clientId,
              wsConnected,
              loadingPredict,
              setLoadingPredict,
              predictResult,
              setPredictResult,
            }}
          >
            {children}
          </WebSocketContext.Provider>
        </div>
      </main>
    </div>
  );
}
