import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "AI NLP Manager - TERMINAL",
  description: "Quản lý dữ liệu huấn luyện NLP",
  icons: {
    icon: "/favicon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body className="font-mono bg-black text-[#00ff33] antialiased" suppressHydrationWarning>
        {children}
        <Toaster position="top-right" 
          toastOptions={{
            style: {
              borderRadius: '0',
              background: '#000',
              color: '#00ff33',
              border: '1px solid #00ff33',
              boxShadow: '0 0 10px rgba(0,255,51,0.3)',
            },
          }}
        />
      </body>
    </html>
  );
}
