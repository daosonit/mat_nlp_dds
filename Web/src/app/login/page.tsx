"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { Lock, User } from "lucide-react";
import toast from "react-hot-toast";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const response = await api.post("/auth/login", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      if (response.data && response.data.access_token) {
        localStorage.setItem("access_token", response.data.access_token);
        toast.success("Đăng nhập thành công!");
        router.push("/");
      }
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || "Sai tài khoản hoặc mật khẩu."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-black font-mono text-[#00ff33] relative">
      {/* Scanline overlay */}
      <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(0,255,51,0.03)_1px,transparent_1px)] bg-[size:100%_4px] opacity-30 z-0"></div>
      
      <div className="bg-black p-8 z-10 w-full max-w-md cyber-border rounded-none relative">
        <div className="text-center mb-8">
          <h1 className="text-base font-bold text-[#00ff33] mb-2 cyber-text-glow tracking-widest">MATGROUP AI LOGIN</h1>
          <p className="text-sm text-[#00ff33]/70">AUTHENTICATION REQUIRED</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-bold text-[#00ff33] mb-1">
              USERNAME
            </label>
            <div className="relative mt-2">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className="h-4 w-4 text-[#00ff33]" />
              </div>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="block w-full pl-10 pr-3 py-3 bg-black border border-[#00ff33]/30 text-[#00ff33] focus:ring-0 focus:border-[#00ff33] sm:text-sm placeholder-[#00ff33]/30 rounded-none transition-colors"
                placeholder="enter username"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-[#00ff33] mb-1">
              PASSWORD
            </label>
            <div className="relative mt-2">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-4 w-4 text-[#00ff33]" />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="block w-full pl-10 pr-3 py-3 bg-black border border-[#00ff33]/30 text-[#00ff33] focus:ring-0 focus:border-[#00ff33] sm:text-sm placeholder-[#00ff33]/30 rounded-none transition-colors"
                placeholder="********"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-8 flex justify-center py-3 px-4 border border-[#00ff33] text-[#00ff33] bg-black hover:bg-[#00ff33] hover:text-black hover:cyber-glow focus:outline-none transition-all duration-300 disabled:opacity-50 text-base font-bold tracking-widest rounded-none uppercase"
          >
            {loading ? "PROCESSING..." : "INITIALIZE"}
          </button>
        </form>
      </div>
    </div>
  );
}
