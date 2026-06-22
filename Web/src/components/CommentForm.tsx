"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { ArrowLeft, Save } from "lucide-react";
import Link from "next/link";

interface CommentFormProps {
  id?: string;
}

export default function CommentForm({ id }: CommentFormProps) {
  const router = useRouter();
  const isEdit = !!id;

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEdit);

  const [formData, setFormData] = useState({
    raw_text: "",
    label: "",
  });

  useEffect(() => {
    if (isEdit) {
      const fetchComment = async () => {
        try {
          const res = await api.get(`/car-comments/${id}`);
          const data = res.data;
          setFormData({
            raw_text: data.raw_text || "",
            label: data.label || "",
          });
        } catch (error) {
          toast.error("Không thể tải dữ liệu");
          router.push("/");
        } finally {
          setFetching(false);
        }
      };
      fetchComment();
    }
  }, [id, router, isEdit]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.raw_text.trim()) {
      toast.error("Vui lòng nhập Raw Text");
      return;
    }
    if (!formData.label) {
      toast.error("Vui lòng chọn Label");
      return;
    }

    setLoading(true);

    try {
      const payload = {
        raw_text: formData.raw_text,
        label: formData.label,
      };

      if (isEdit) {
        await api.patch(`/car-comments/${id}`, payload);
        toast.success("Cập nhật thành công!");
      } else {
        await api.post("/car-comments/", payload);
        toast.success("Tạo mới thành công!");
      }
      router.push("/");
    } catch (error) {
      toast.error(isEdit ? "Cập nhật thất bại" : "Tạo thất bại");
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return <div className="text-center py-10">Đang tải dữ liệu...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      <div className="mb-6 flex items-center border-b border-[#00ff33]/30 pb-4">
        <Link href="/" className="text-[#00ff33] hover:text-[#00ff33] hover:cyber-text-glow mr-4 transition-all">
          <ArrowLeft className="w-6 h-6" />
        </Link>
        <h1 className="text-base font-bold text-[#00ff33] cyber-text-glow uppercase tracking-widest">
          {isEdit ? "EDIT RECORD" : "NEW RECORD"}
        </h1>
      </div>

      <div className="bg-black cyber-border overflow-hidden relative">
        <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(0,255,51,0.02)_1px,transparent_1px)] bg-[size:100%_4px] opacity-20 z-0"></div>
        <form onSubmit={handleSubmit} className="p-8 space-y-8 relative z-10">
          <div>
            <label className="block text-sm font-bold text-[#00ff33] mb-2 uppercase">RAW TEXT <span className="text-[#ff003c]">*</span></label>
            <textarea
              name="raw_text"
              required
              rows={6}
              value={formData.raw_text}
              onChange={handleChange}
              className="w-full p-4 bg-black border border-[#00ff33]/30 text-[#00ff33] focus:ring-0 focus:border-[#00ff33] cyber-glow transition-all rounded-none placeholder-[#00ff33]/30 font-mono"
              placeholder="Enter raw text here..."
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-[#00ff33] mb-2 uppercase">LABEL <span className="text-[#ff003c]">*</span></label>
            <select
              name="label"
              required
              value={formData.label}
              onChange={handleChange}
              className="w-full p-4 bg-black border border-[#00ff33]/30 text-[#00ff33] focus:ring-0 focus:border-[#00ff33] cyber-glow transition-all rounded-none font-mono"
            >
              <option value="">-- CHOOSE LABEL --</option>
              <option value="positive">POSITIVE</option>
              <option value="negative">NEGATIVE</option>
              <option value="neutral">NEUTRAL</option>
            </select>
          </div>

          <div className="pt-6 flex justify-end border-t border-[#00ff33]/30 mt-8">
            <Link
              href="/"
              className="px-6 py-3 border border-[#ff003c] text-[#ff003c] bg-black hover:bg-[#ff003c] hover:text-black font-bold uppercase transition-all mr-4 rounded-none cyber-glow-red"
            >
              CANCEL
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center px-8 py-3 border border-[#00ff33] text-[#00ff33] bg-black hover:bg-[#00ff33] hover:text-black font-bold uppercase transition-all disabled:opacity-30 rounded-none cyber-glow tracking-widest"
            >
              <Save className="w-5 h-5 mr-3" />
              {loading ? "SAVING..." : "SAVE RECORD"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
