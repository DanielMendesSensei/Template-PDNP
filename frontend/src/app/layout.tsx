import type { Metadata } from "next";
import "./globals.css";
import { ToastContainer } from "react-toastify";
import { ThemeProvider } from "@/context/theme-provider";

export const metadata: Metadata = {
  title: process.env.PROJECT_NAME as string,
  description: "The Newest version",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
          storageKey={process.env.PROJECT_NAME as string}
        >
          {children}
          <ToastContainer position="top-right" autoClose={3000} />
        </ThemeProvider>
      </body>
    </html>
  );
}
