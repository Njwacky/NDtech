import { Button } from "@/components/ui/button"
import Link from "next/link"

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold mb-8">NDtech POS System</h1>
      </div>

      <div className="mb-8 text-center">
        <p className="text-xl mb-4">Point of Sale & Inventory Management</p>
        <p className="text-muted-foreground">
          Modern POS system with real-time inventory tracking
        </p>
      </div>

      <div className="flex gap-4">
        <Button asChild>
          <Link href="/cart">View Cart Demo</Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/dashboard">Dashboard</Link>
        </Button>
      </div>
    </main>
  )
}
