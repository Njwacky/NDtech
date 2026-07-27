"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

// Mock product data
const mockProducts = [
  { id: 1, name: "Product A", price: 29.99, stock: 50 },
  { id: 2, name: "Product B", price: 49.99, stock: 30 },
  { id: 3, name: "Product C", price: 19.99, stock: 100 },
]

interface CartItem {
  id: number
  name: string
  price: number
  quantity: number
}

export default function CartPage() {
  const [cart, setCart] = useState<CartItem[]>([])

  const addToCart = (product: (typeof mockProducts)[0]) => {
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

  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">Shopping Cart Demo</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Products */}
        <div>
          <h2 className="text-2xl font-semibold mb-4">Products</h2>
          <div className="space-y-4">
            {mockProducts.map((product) => (
              <Card key={product.id}>
                <CardHeader>
                  <CardTitle>{product.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold mb-2">${product.price}</p>
                  <p className="text-sm text-muted-foreground mb-4">
                    Stock: {product.stock}
                  </p>
                  <Button onClick={() => addToCart(product)}>Add to Cart</Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Cart */}
        <div>
          <h2 className="text-2xl font-semibold mb-4">Cart</h2>
          {cart.length === 0 ? (
            <p className="text-muted-foreground">Your cart is empty</p>
          ) : (
            <div className="space-y-4">
              {cart.map((item) => (
                <Card key={item.id}>
                  <CardContent className="flex justify-between items-center pt-6">
                    <div>
                      <p className="font-semibold">{item.name}</p>
                      <p className="text-sm text-muted-foreground">
                        ${item.price} x {item.quantity}
                      </p>
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => removeFromCart(item.id)}
                    >
                      Remove
                    </Button>
                  </CardContent>
                </Card>
              ))}
              <div className="text-2xl font-bold mt-4">
                Total: ${total.toFixed(2)}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
