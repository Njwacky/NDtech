"use client";

import InteractiveCheckout, { type Product } from "@/components/ui/interactive-checkout";


const defaultProducts: Product[] = [
  {
    id: "1",
    name: "Air Max 90",
    price: 129.99,
    category: "Running",
    image:
      "https://images.unsplash.com/photo-1528701800489-20be3c1e9d8b?auto=format&fit=crop&w=400&h=400&q=80",
    color: "Black/White",
  },
  {
    id: "2",
    name: "Ultra Boost",
    price: 179.99,
    category: "Performance",
    image:
      "https://images.unsplash.com/photo-1528702748617-c94d5d6b17d8?auto=format&fit=crop&w=400&h=400&q=80",
    color: "Grey/Blue",
  },
  {
    id: "3",
    name: "Classic Trainer",
    price: 89.99,
    category: "Casual",
    image:
      "https://images.unsplash.com/photo-1528700771517-7aa4c9e0d4d3?auto=format&fit=crop&w=400&h=400&q=80",
    color: "White/Red",
  },
];

export default function HomePage() {
  return <InteractiveCheckout products={defaultProducts} />;
}

