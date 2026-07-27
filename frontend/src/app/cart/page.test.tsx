import { render, screen, fireEvent } from '@testing-library/react'
import CartPage from '@/app/cart/page'

// Mock the Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}))

describe('Cart Page', () => {
  it('renders the cart page title', () => {
    render(<CartPage />)
    const title = screen.getByText(/shopping cart demo/i)
    expect(title).toBeInTheDocument()
  })

  it('displays products', () => {
    render(<CartPage />)
    // Check if mock products are displayed
    expect(screen.getByText('Product A')).toBeInTheDocument()
    expect(screen.getByText('Product B')).toBeInTheDocument()
    expect(screen.getByText('Product C')).toBeInTheDocument()
  })

  it('adds item to cart when "Add to Cart" is clicked', () => {
    render(<CartPage />)
    
    // Find and click "Add to Cart" button for Product A
    const addButtons = screen.getAllByText(/add to cart/i)
    fireEvent.click(addButtons[0])
    
    // Check if cart section updates
    const cartTitle = screen.getByText(/cart/i)
    expect(cartTitle).toBeInTheDocument()
  })

  it('removes item from cart when "Remove" is clicked', () => {
    render(<CartPage />)
    
    // Add an item first
    const addButtons = screen.getAllByText(/add to cart/i)
    fireEvent.click(addButtons[0])
    
    // Now remove it
    const removeButton = screen.getByText(/remove/i)
    fireEvent.click(removeButton)
    
    // Check if cart is empty
    expect(screen.getByText(/your cart is empty/i)).toBeInTheDocument()
  })

  it('calculates total correctly', () => {
    render(<CartPage />)
    
    // Add two items
    const addButtons = screen.getAllByText(/add to cart/i)
    fireEvent.click(addButtons[0]) // Product A - $29.99
    fireEvent.click(addButtons[1]) // Product B - $49.99
    
    // Check total
    const total = screen.getByText(/\$79\.98/i) // 29.99 + 49.99
    expect(total).toBeInTheDocument()
  })
})
