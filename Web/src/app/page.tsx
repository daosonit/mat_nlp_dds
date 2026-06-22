"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import api from "@/lib/api";
import { Plus, Edit2, Trash2, Search, X, FileX } from "lucide-react";
import toast from "react-hot-toast";
import AuthGuard from "@/components/AuthGuard";

interface WordsTraining {
  id: string;
  comment: string;
  label: string | null;
  score: number | null;
  segmented_text: string | null;
  model_used: string | null;
  created_at: string;
}

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  const urlPage = Number(searchParams.get("page")) || 1;
  const urlLabel = searchParams.get("label") || "";
  const urlSearch = searchParams.get("search") || "";

  const [records, setRecords] = useState<WordsTraining[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);

  const [filterLabel, setFilterLabel] = useState(urlLabel);
  const [filterSearch, setFilterSearch] = useState(urlSearch);

  const PAGE_SIZE = 50;

  useEffect(() => {
    setFilterLabel(urlLabel);
    setFilterSearch(urlSearch);
  }, [urlLabel, urlSearch]);

  const fetchRecords = async () => {
    setLoading(true);
    try {
      let url = `/words-training?page=${urlPage}&size=${PAGE_SIZE}`;
      if (urlLabel) url += `&label=${urlLabel}`;
      if (urlSearch) url += `&search=${encodeURIComponent(urlSearch)}`;

      const res = await api.get(url);
      setRecords(res.data.data);
      setTotalPages(res.data.meta.total_pages);
      setTotalRecords(res.data.meta.total_records);
    } catch (error) {
      toast.error("Không thể tải danh sách dữ liệu");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [urlPage, urlLabel, urlSearch]);

  const pushToRouter = (params: {
    page?: string;
    label?: string;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params.page) query.set("page", params.page);
    if (params.label) query.set("label", params.label);
    if (params.search) query.set("search", params.search);

    router.push(`${pathname}?${query.toString()}`);
  };

  const handleSearch = () => {
    pushToRouter({
      page: "1",
      label: filterLabel,
      search: filterSearch,
    });
  };

  const getLabelColor = (label: string | null) => {
    switch (label) {
      case "positive":
        return "bg-[#00ff33]/10 text-[#00ff33] border border-[#00ff33] cyber-glow";
      case "negative":
        return "bg-[#ff003c]/10 text-[#ff003c] border border-[#ff003c] cyber-glow-red";
      case "neutral":
        return "bg-gray-800 text-gray-400 border border-gray-600";
      default:
        return "bg-gray-800 text-yellow-500 border border-yellow-500";
    }
  };

  return (
    <div className="w-full p-8">
      <div className="flex justify-between items-center mb-6 border-b border-[#00ff33]/30 pb-4">
        <div>
          <h1 className="text-base font-bold text-[#00ff33] cyber-text-glow uppercase">
            DATA CORE Training Dataset
          </h1>
          <p className="text-sm text-[#00ff33]/60 mt-1">
            Status: Online | Records: {totalRecords}
          </p>
        </div>
      </div>

      <div className="flex space-x-4 items-center mb-6">
        <div className="relative">
          <input
            type="text"
            placeholder="SEARCH TEXT"
            value={filterSearch}
            onChange={(e) => setFilterSearch(e.target.value)}
            className="bg-black border border-[#00ff33]/30 text-[#00ff33] text-sm font-bold placeholder-[#00ff33]/30 focus:ring-0 focus:border-[#00ff33] rounded-none px-3 py-2 outline-none w-64 transition-colors pr-8"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSearch();
              }
            }}
          />
          {filterSearch ? (
            <X
              className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-[#ff003c] cursor-pointer hover:text-white transition-colors cyber-glow-red"
              onClick={() => {
                setFilterSearch("");
                pushToRouter({
                  page: "1",
                  label: filterLabel,
                  search: "",
                });
              }}
            />
          ) : (
            <Search className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-[#00ff33]/50 pointer-events-none" />
          )}
        </div>

        <select
          value={filterLabel}
          onChange={(e) => setFilterLabel(e.target.value)}
          className="bg-black border border-[#00ff33]/30 text-[#00ff33] text-sm font-bold uppercase focus:ring-0 focus:border-[#00ff33] rounded-none px-3 py-2 cursor-pointer outline-none hover:border-[#00ff33] transition-colors"
        >
          <option value="">ALL LABELS</option>
          <option value="positive">POSITIVE</option>
          <option value="negative">NEGATIVE</option>
          <option value="neutral">NEUTRAL</option>
        </select>

        <button
          onClick={handleSearch}
          className="inline-flex items-center px-6 py-2 border border-[#00ff33] text-black bg-[#00ff33] hover:bg-black hover:text-[#00ff33] font-bold text-sm uppercase transition-all duration-200 rounded-none shadow-[0_0_10px_rgba(0,255,51,0.2)]"
        >
          SEARCH
        </button>
      </div>

      <div className="bg-black cyber-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-[#00ff33]/30">
            <thead className="bg-[#00ff33]/10">
              <tr>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-bold text-[#00ff33] uppercase tracking-wider w-full"
                >
                  RAW TEXT
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-bold text-[#00ff33] uppercase tracking-wider"
                >
                  LABEL
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-center text-xs font-bold text-[#00ff33] uppercase tracking-wider"
                >
                  SCORE & MODEL
                </th>
              </tr>
            </thead>
            <tbody className="bg-black divide-y divide-[#00ff33]/10">
              {loading ? (
                Array.from({ length: 10 }).map((_, idx) => (
                  <tr key={`skeleton-${idx}`} className="animate-pulse">
                    <td className="px-6 py-4">
                      <div className="h-4 bg-[#00ff33]/20 rounded-none w-3/4 cyber-glow"></div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="h-6 bg-[#00ff33]/20 rounded-none w-20 cyber-glow"></div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="h-6 bg-[#00ff33]/20 rounded-none w-24 cyber-glow mx-auto"></div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="h-6 bg-[#00ff33]/20 rounded-none w-10 cyber-glow ml-auto"></div>
                    </td>
                  </tr>
                ))
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-16 text-center">
                    <div className="flex flex-col items-center justify-center space-y-4">
                      <FileX className="w-16 h-16 text-[#00ff33]/30" />
                      <p className="text-[#00ff33]/50 font-bold tracking-widest uppercase">
                        NO DATA FRAGMENTS LOCATED
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                records.map((record) => (
                  <tr
                    key={record.id}
                    className="hover:bg-[#00ff33]/5 transition-colors"
                  >
                    <td className="px-6 py-4 w-full max-w-0">
                      <div
                        className="text-sm text-gray-300 truncate"
                        title={record.comment}
                      >
                        {record.comment}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-bold uppercase ${getLabelColor(record.label)}`}
                      >
                        {record.label || "UNASSIGNED"}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <div className="text-xs font-mono uppercase">
                        <span className="text-[#00ff33]">
                          {record.score
                            ? (record.score * 100).toFixed(1) + "%"
                            : "N/A"}
                        </span>
                        <br />
                        <span className="text-gray-500 opacity-70">
                          {record.model_used || "N/A"}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!loading && records.length > 0 && (
          <div className="px-6 py-4 border-t border-[#00ff33]/30 flex items-center justify-between bg-black">
            <div className="text-sm text-[#00ff33]/70">
              TOTAL RECORDS:{" "}
              <strong className="text-[#00ff33] cyber-text-glow">
                {totalRecords}
              </strong>
            </div>
            <div className="flex space-x-2 items-center">
              <button
                onClick={() =>
                  pushToRouter({ page: Math.max(1, urlPage - 1).toString() })
                }
                disabled={urlPage === 1}
                className="px-3 py-1.5 border border-[#00ff33] rounded-none text-sm font-bold text-[#00ff33] bg-black hover:bg-[#00ff33] hover:text-black disabled:opacity-30 disabled:hover:bg-black disabled:hover:text-[#00ff33] transition-colors uppercase"
              >
                &lt;
              </button>
              <span className="px-4 py-1.5 text-sm text-[#00ff33] font-bold border-y border-[#00ff33]">
                PAGE {urlPage} OF {totalPages}
              </span>
              <button
                onClick={() =>
                  pushToRouter({
                    page: Math.min(totalPages, urlPage + 1).toString(),
                  })
                }
                disabled={urlPage >= totalPages}
                className="px-3 py-1.5 border border-[#00ff33] rounded-none text-sm font-bold text-[#00ff33] bg-black hover:bg-[#00ff33] hover:text-black disabled:opacity-30 disabled:hover:bg-black disabled:hover:text-[#00ff33] transition-colors uppercase"
              >
                &gt;
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <Suspense
        fallback={
          <div className="p-8 text-[#00ff33] cyber-text-glow font-bold uppercase text-center w-full">
            LOADING DATA CORE...
          </div>
        }
      >
        <DashboardContent />
      </Suspense>
    </AuthGuard>
  );
}
