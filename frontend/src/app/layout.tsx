import { Menu, Bell } from "lucide-react";
import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "NDtech POS System",
  description: "Point of Sale System with Inventory Management",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">{children}</body>
    </html>
  )
}
