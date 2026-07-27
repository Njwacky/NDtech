"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

interface Product {
  id: number
  name: string
  price: number
  stock: number
}

interface CartItem {
  id: number
  name: string
  price: number
  quantity: number
}

interface InteractiveCheckoutProps {
  products: Product[]
  onCheckout?: (items: CartItem[], total: number) => void
}

export function InteractiveCheckout({ products, onCheckout }: InteractiveCheckoutProps) {
  const [cart, setCart] = useState<CartItem[]>([])
  const [step, setStep] = useState<"shopping" | "checkout" | "confirmation">("shopping")

  const addToCart = (product: Product) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.id === product.id)
      if (existing) {
        return prev.map((item) =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        )
      }
      return [...prev, { id: product.id, name: product.name, price: product.price, quantity: 1 }]
    })
  }

  const removeFromCart = (id: number) => {
    setCart((prev) => prev.filter((item) => item.id !== id))
  }

  const updateQuantity = (id: number, quantity: number) => {
    if (quantity === 0) {
      removeFromCart(id)
      return
    }
    setCart((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, quantity } : item
      )
    )
  }

  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)

  const handleCheckout = () => {
    setStep("checkout")
  }

  const handleConfirm = () => {
    onCheckout?.(cart, total)
    setCart([])
    setStep("confirmation")
  }

  const handleReset = () => {
    setStep("shopping")
  }

  if (step === "confirmation") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Order Confirmed! 🎉</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4">Your order has been successfully processed.</p>
          <Button onClick={handleReset}>Continue Shopping</Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {step === "shopping" && (
        <>
          <h2 className="text-2xl font-bold">Products</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {products.map((product) => (
              <Card key={product.id}>
                <CardHeader>
                  <CardTitle>{product.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold mb-2">${product.price.toFixed(2)}</p>
                  <p className="text-sm text-muted-foreground mb-4">
                    Stock: {product.stock}
                  </p>
                  <Button onClick={() => addToCart(product)} className="w-full">
                    Add to Cart
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>

          {cart.length > 0 && (
            <div className="fixed bottom-4 right-4 p-4 bg-background border rounded-lg shadow-lg">
              <p className="font-bold">Cart: {cart.length} items</p>
              <p>Total: ${total.toFixed(2)}</p>
              <Button onClick={handleCheckout} className="mt-2 w-full">
                Checkout
              </Button>
            </div>
          )}
        </>
      )}

      {step === "checkout" && (
        <Card>
          <CardHeader>
            <CardTitle>Checkout</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {cart.map((item) => (
                <div key={item.id} className="flex justify-between items-center">
                  <div>
                    <p className="font-semibold">{item.name}</p>
                    <p className="text-sm text-muted-foreground">
                      ${item.price.toFixed(2)} x {item.quantity}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => updateQuantity(item.id, item.quantity - 1)}
                    >
                      -
                    </Button>
                    <span>{item.quantity}</span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => updateQuantity(item.id, item.quantity + 1)}
                    >
                      +
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => removeFromCart(item.id)}
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              ))}
              <div className="border-t pt-4">
                <p className="text-2xl font-bold">Total: ${total.toFixed(2)}</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep("shopping")}>
                  Continue Shopping
                </Button>
                <Button onClick={handleConfirm}>Confirm Order</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
